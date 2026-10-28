import copy
import http.client
import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from proofloop.common import ROOT, digest
from proofloop.generator import ProviderError, provider_call
from proofloop.runner import execute, save_run
from proofloop.server import App


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(0,str(Path(self.tmp.name)/'db'))
        self.thread=threading.Thread(target=self.app.serve_forever,daemon=True);self.thread.start()
        self.test=json.loads((ROOT/'fixtures/reference.json').read_text())['tests'][0]
    def tearDown(self):
        self.app.shutdown();self.thread.join();self.app.server_close();self.tmp.cleanup()
    def request(self,method,path,body,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.app.server_port,timeout=3)
        c.request(method,path,body=body,headers=headers or {})
        r=c.getresponse();value=json.loads(r.read());c.close();return r.status,value
    def test_wire_errors_and_mutation_origin_guard(self):
        self.assertEqual(self.request('POST','/checkout','{')[0],400)
        self.assertEqual(self.request('POST','/unsupported','{'),(404,{'error':'NOT_FOUND'}))
        self.assertEqual(self.request('PUT','/checkout','{}')[0],405)
        self.assertEqual(self.request('POST','/api/generate','{"mode":"offline"}',
            {'Content-Type':'application/json','X-ProofLoop':'1','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('GET','/api/state',None,{'Host':'evil.example'})[0],403)
    def test_changed_spec_and_superseded_revision_cannot_execute(self):
        s=self.app.store;r=s.import_tests([self.test],{'mode':'reference'},self.app.spec_hash)[0]
        s.review(r['id'],'approved','test','check')
        invalid=execute(r,'approved',self.app.server_port,self.app.source,'new-spec')
        self.assertEqual(invalid['outcome'],'invalid_test')
        old=save_run(s,r['id'],self.app.server_port,self.app.source,self.app.spec_hash)
        newer=copy.deepcopy(self.test);newer['title']='New title'
        s.edit(r['id'],newer,'test')
        self.assertEqual(save_run(s,r['id'],self.app.server_port,self.app.source,self.app.spec_hash)['outcome'],'not_run')
        self.assertEqual(s.get('run',old['id']),old)
    def test_inconsistent_results_flagged_using_explicit_simulated_execution(self):
        s=self.app.store;r=s.import_tests([self.test],{'mode':'reference'},self.app.spec_hash)[0]
        s.review(r['id'],'approved','test','check')
        first=save_run(s,r['id'],self.app.server_port,self.app.source,self.app.spec_hash)
        simulated=copy.deepcopy(first);simulated.pop('id');simulated['outcome']='failed_assertion'
        with patch('proofloop.runner.execute',return_value=simulated):
            second=save_run(s,r['id'],self.app.server_port,self.app.source,self.app.spec_hash,first['id'])
        self.assertTrue(second['inconsistent_result'])
        self.assertEqual(s.get('run',first['id'])['outcome'],'passed')
    def test_provider_http_failure_timeout_and_malformed_json(self):
        for status,raw,error in [(503,b'ignored',None),(200,b'bad-json',None),(200,b'',TimeoutError())]:
            with self.subTest(status=status,error=error),patch('proofloop.generator.http.client.HTTPSConnection') as cls:
                response=cls.return_value.getresponse.return_value
                response.status=status;response.read.return_value=raw
                if error:cls.return_value.getresponse.side_effect=error
                with self.assertRaises(ProviderError):provider_call({'model':'mock'},'mock-secret')
                cls.return_value.close.assert_called_once()


if __name__=='__main__':unittest.main()
