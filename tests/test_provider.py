import json
import os
import unittest
from unittest.mock import patch
from proofloop.common import ROOT, digest, spec
from proofloop.generator import ProviderError, generate
from proofloop.storage import Store


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.s=Store(':memory:')
        self.env=patch.dict(os.environ, {'OPENAI_API_KEY':'unit-test-secret','OPENAI_MODEL':'mock-model'})
        self.env.start()
    def tearDown(self):
        self.env.stop();self.s.close()
    def run_generation(self,transport):
        return generate(self.s,{'mode':'live'},spec(),digest(spec()),transport)
    def test_valid_response_stays_pending_and_records_usage(self):
        def fake(payload,key):
            self.assertEqual(payload['text']['format']['type'],'json_object')
            self.assertFalse(payload['store']);self.assertNotIn(key,json.dumps(payload))
            return {'id':'mock-response','status':'completed','model':'mock-model','usage':{'input_tokens':100},
                    'output':[{'type':'message','content':[{'type':'output_text','text':(ROOT/'fixtures/offline.json').read_text()}]}]}
        result=self.run_generation(fake)
        self.assertEqual(len(result['revisions']),4)
        self.assertEqual(self.s.status(result['revisions'][0]['id']),'pending')
        self.assertEqual(result['generation']['usage'],{'input_tokens':100})
    def test_malformed_refusal_and_incomplete_are_not_imported(self):
        for text,status in [('not json','completed'),('{}','completed'),('','completed'),('{}','incomplete')]:
            result=self.run_generation(lambda *_:{'status':status,'output':[{'type':'message','content':[{'type':'output_text','text':text}]}]})
            self.assertEqual(result['generation']['status'],'error');self.assertFalse(result['revisions'])
    def test_provider_failure_and_manual_retry_preserve_both(self):
        def fail(*_):raise ProviderError('Provider HTTP 429')
        first=self.run_generation(fail)
        second=generate(self.s,{'mode':'live','parent_generation_id':first['generation']['id']},spec(),digest(spec()),fail)
        self.assertEqual(len(self.s.all('generation')),2)
        self.assertEqual(second['generation']['parent_generation_id'],first['generation']['id'])
        self.assertNotIn('unit-test-secret',json.dumps(self.s.all('generation')))
    def test_missing_credentials_no_offline_fallback(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':''}):
            result=self.run_generation(lambda *_:self.fail('Must not call provider'))
        self.assertEqual(result['generation']['status'],'error');self.assertEqual(result['revisions'],[])
    def test_constructed_error_is_labeled(self):
        r=generate(self.s,{'mode':'constructed_incorrect'},spec(),digest(spec()))
        self.assertIn('Deliberately incorrect',r['generation']['label'])
        self.assertEqual(r['revisions'][0]['test']['expected']['body']['shipping_cents'],0)


if __name__=='__main__':unittest.main()
