import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from proofloop.checkout import quote
from proofloop.common import ROOT, digest
from proofloop.runner import execute, save_run
from proofloop.schema import InvalidTest, validate, validate_batch
from proofloop.server import App
from proofloop.storage import Store


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tests = json.loads((ROOT / 'fixtures/reference.json').read_text())['tests']

    def test_reference_contract_all_scenarios(self):
        for t in self.tests:
            with self.subTest(t=t['id']):
                status, body = quote(t['request']['body'], t['request']['method'], t['request']['path'])
                self.assertEqual({'status': status, 'body': body}, t['expected'])

    def test_shape_precedence_and_stock_is_not_mutated(self):
        self.assertEqual(quote({'items':[{'sku':'NOPE','quantity':1},{'sku':'TEE','quantity':True}]}),
                         (400, {'error':'INVALID_REQUEST'}))
        body = {'items':[{'sku':'TEE','quantity':4}]}
        self.assertEqual(quote(body), quote(body))
        for body in [None, {}, {'items':[]}, {'items':[{'sku':'TEE','quantity':1}], 'extra':0}]:
            self.assertEqual(quote(body)[0], 400)

    def test_schema_rejects_urls_commands_empty_assertions_and_bool_money(self):
        for mutate in [lambda t:t['request'].update(path='https://example.com'),
                       lambda t:t.update(command='rm'), lambda t:t['expected'].update(body={}),
                       lambda t:t['expected']['body'].update(total_cents=True)]:
            t=copy.deepcopy(self.tests[0]);mutate(t)
            with self.assertRaises(InvalidTest):validate(t)
        with self.assertRaises(InvalidTest):validate_batch({'tests':[self.tests[0]]*2})

    def test_edit_invalidates_approval_and_preserves_old_revision(self):
        s=Store(':memory:')
        r=s.import_tests([self.tests[0]],{'mode':'reference'},'spec')[0]
        s.review(r['id'],'approved','test reviewer','checked arithmetic')
        t=copy.deepcopy(r['test']);t['title']='Edited title'
        new=s.edit(r['id'],t,'test editor')
        self.assertEqual(s.status(new['id']),'pending')
        self.assertEqual(s.get('revision',r['id'])['test'],r['test'])
        with self.assertRaises(ValueError):s.review(r['id'],'approved','x','stale')
        with self.assertRaises(ValueError):s.edit(r['id'],t,'x')
        s.close()

    def test_real_http_and_unavailable_target_preserve_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=App(0, str(Path(tmp)/'db'))
            thread=threading.Thread(target=app.serve_forever,daemon=True);thread.start()
            try:
                r=app.store.import_tests([self.tests[1]],{'mode':'reference'},app.spec_hash)[0]
                skipped=save_run(app.store,r['id'],app.server_port,app.source,app.spec_hash)
                self.assertEqual(skipped['outcome'],'not_run')
                app.store.review(r['id'],'approved','test reviewer','R3, R5 arithmetic checked')
                good=save_run(app.store,r['id'],app.server_port,app.source,app.spec_hash)
                self.assertEqual(good['outcome'],'passed')
                # Bind without listening: reliably unavailable local target, no guessed service port.
                import socket
                with socket.socket() as sock:
                    sock.bind(('127.0.0.1',0))
                    fail=save_run(app.store,r['id'],sock.getsockname()[1],app.source,app.spec_hash)
                self.assertEqual(fail['outcome'],'execution_error')
                recovery=save_run(app.store,r['id'],app.server_port,app.source,app.spec_hash,fail['id'])
                self.assertEqual(recovery['outcome'],'passed')
                self.assertEqual(app.store.get('run',fail['id'])['outcome'],'execution_error')
                changed=copy.deepcopy(r);changed['test']['expected']['body']['total_cents']=0
                self.assertEqual(execute(changed,'approved',app.server_port,app.source,app.spec_hash)['outcome'],'invalid_test')
            finally:
                app.shutdown();thread.join();app.server_close()


if __name__=='__main__':unittest.main()
