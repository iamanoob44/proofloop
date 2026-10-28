import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .checkout import quote
from .common import ROOT, digest, source_state, spec
from .runner import save_run
from .schema import validate_batch
from .storage import Store


class App(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port=8765, db='data/proofloop.sqlite'):
        Path(db).parent.mkdir(parents=True, exist_ok=True)
        self.store = Store(db)
        self.source = source_state()
        self.spec_text = spec()
        self.spec_hash = digest(self.spec_text)
        self.action_lock = threading.RLock()
        super().__init__(('127.0.0.1', port), Handler)

    def server_close(self):
        super().server_close()
        self.store.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, value, mime='application/json'):
        data = json.dumps(value, allow_nan=False).encode() if mime == 'application/json' else value
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-ProofLoop-Source', self.server.source['source_hash'])
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 65536:
            raise ValueError('Expected a JSON body up to 64 KiB')
        self.connection.settimeout(5)
        def invalid(value):
            raise ValueError('Non-finite JSON number')
        return json.loads(self.rfile.read(size), parse_constant=invalid)

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_PUT(self):
        self.handle_request('PUT')

    def do_DELETE(self):
        self.handle_request('DELETE')

    def do_PATCH(self):
        self.handle_request('PATCH')

    def handle_request(self, method):
        app = self.server
        host = f'127.0.0.1:{app.server_port}'
        if self.headers.get('Host') != host:
            return self.send(403, {'error': 'Use the exact 127.0.0.1 URL shown at startup'})
        if self.path == '/unsupported':
            return self.send(404, {'error': 'NOT_FOUND'})
        if self.path == '/checkout':
            try:
                body = self.read_json() if method == 'POST' else None
            except (ValueError, UnicodeError, OSError, RecursionError):
                return self.send(400, {'error': 'INVALID_REQUEST'})
            code, response = quote(body, method, self.path)
            return self.send(code, response)
        if method == 'GET':
            assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if self.path in assets:
                name, mime = assets[self.path]
                return self.send(200, (ROOT / 'proofloop' / 'web' / name).read_bytes(), mime)
            if self.path == '/api/state':
                return self.send(200, {'spec': app.spec_text, 'spec_hash': app.spec_hash, 'source': app.source,
                    'revisions': [{**r, 'status': app.store.status(r['id'])} for r in app.store.all('revision')],
                    'runs': app.store.all('run'), 'reviews': app.store.all('review'),
                    'generations': app.store.all('generation'), 'diagnoses': app.store.all('diagnosis')})
            return self.send(404, {'error': 'NOT_FOUND'})
        if method != 'POST':
            return self.send(405, {'error': 'METHOD_NOT_ALLOWED'})
        if (self.headers.get('Origin') not in (None, f'http://{host}')
                or self.headers.get('X-ProofLoop') != '1'
                or self.headers.get_content_type() != 'application/json'):
            return self.send(403, {'error': 'Same-origin JSON request required'})
        try:
            data = self.read_json()
            if type(data) is not dict:
                raise ValueError('Expected an object')
            with app.action_lock:
                if source_state()['source_hash'] != app.source['source_hash']:
                    raise ValueError('Source files changed. Restart the application before continuing.')
                result = self.action(data)
            self.send(200, result)
        except (ValueError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
            self.send(400, {'error': str(exc)})
        except Exception as exc:
            # Keep exception details and any provider payload/credentials off the HTTP surface.
            self.send(500, {'error': f'Internal error ({type(exc).__name__}); no successful result recorded'})

    def action(self, data):
        app = self.server
        store = app.store
        if self.path == '/api/generate':
            from .generator import generate
            return generate(store, data, app.spec_text, app.spec_hash)
        if self.path == '/api/edit':
            return store.edit(data['revision_id'], data['test'], data['editor'])
        if self.path == '/api/review':
            return store.review(data['revision_id'], data['status'], data['reviewer'], data['note'])
        if self.path == '/api/run':
            return save_run(store, data['revision_id'], app.server_port, app.source,
                            app.spec_hash, data.get('parent_run_id'))
        if self.path == '/api/diagnose':
            store.get('run', data['run_id'])
            if data['classification'] not in {'product_defect', 'incorrect_test', 'environment', 'inconclusive'}:
                raise ValueError('Unsupported diagnosis')
            if not data.get('reviewer', '').strip() or not data.get('note', '').strip():
                raise ValueError('Reviewer and localization/reason are required')
            return store.append('diagnosis', {'run_id': data['run_id'], 'classification': data['classification'],
                                             'reviewer': data['reviewer'][:120], 'note': data['note'][:2000]})
        raise ValueError('Unknown API operation')
