"""Regression checks for Windows text decoding and early HTTP rejection."""
import http.client
import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from proofloop.common import digest, spec
from proofloop.server import App


class SpecificationEncodingTests(unittest.TestCase):
    def test_utf8_specification_preserves_symbols_and_hash(self):
        text = 'Rules \u2014 net = subtotal \u2212 discount; 2 \u00d7 2500; quantities 1\u201310.\n'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'SPEC.md').write_bytes(text.encode('utf-8'))
            with patch('proofloop.common.ROOT', root):
                self.assertEqual(spec(), text)
                self.assertEqual(digest(spec()), digest(text))


class EarlyRejectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = App(0, str(Path(self.temp.name) / 'db'))
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.app.shutdown()
        self.thread.join()
        self.app.server_close()
        self.temp.cleanup()

    def test_rejections_with_bodies_keep_their_status_and_precedence(self):
        cases = [
            ('POST', '/unsupported', {}, 404, 'NOT_FOUND'),
            ('POST', '/unknown', {}, 404, 'NOT_FOUND'),
            ('PUT', '/checkout', {}, 405, 'METHOD_NOT_ALLOWED'),
            ('POST', '/api/generate', {'Origin': 'https://evil.example'}, 403,
             'Same-origin JSON request required'),
            ('POST', '/checkout', {'Host': 'evil.example'}, 403,
             'Use the exact 127.0.0.1 URL shown at startup'),
        ]
        # Repeated connections exercise the previously intermittent Windows reset.
        # Invalid JSON must not replace operation/origin errors with a parse error.
        for attempt in range(10):
            for method, path, extra, status, error in cases:
                with self.subTest(attempt=attempt, method=method, path=path, extra=extra):
                    conn = http.client.HTTPConnection('127.0.0.1', self.app.server_port, timeout=3)
                    try:
                        headers = {'Content-Type': 'application/json', 'X-ProofLoop': '1', **extra}
                        conn.request(method, path, body='{' * 4096, headers=headers)
                        response = conn.getresponse()
                        self.assertEqual(response.status, status)
                        self.assertEqual(json.loads(response.read()), {'error': error})
                    finally:
                        conn.close()
        self.assertEqual(self.app.store.all('generation'), [])

    def test_rejection_does_not_wait_indefinitely_for_missing_body(self):
        with socket.create_connection(('127.0.0.1', self.app.server_port), timeout=3) as conn:
            request = (f'POST /unsupported HTTP/1.0\r\nHost: 127.0.0.1:{self.app.server_port}\r\n'
                       'Content-Length: 10\r\n\r\n')
            conn.sendall(request.encode('ascii'))
            response = http.client.HTTPResponse(conn)
            try:
                response.begin()
                self.assertEqual(response.status, 404)
                self.assertEqual(json.loads(response.read()), {'error': 'NOT_FOUND'})
            finally:
                response.close()


if __name__ == '__main__':
    unittest.main()
