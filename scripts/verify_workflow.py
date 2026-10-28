"""Real HTTP API workflow. Explicit assistant validation; no claim of human review."""
import argparse
import copy
import http.client
import json
import socket
import sys
import threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from proofloop.common import ROOT, now
from proofloop.runner import save_run
from proofloop.server import App


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/workflow.sqlite');p.add_argument('--output',default='evidence/04-workflow.json');args=p.parse_args()
    app=App(0,args.db);thread=threading.Thread(target=app.serve_forever,daemon=True);thread.start()
    events=[]
    def api(route,data):
        c=http.client.HTTPConnection('127.0.0.1',app.server_port,timeout=5)
        c.request('POST','/api/'+route,json.dumps(data),{'Content-Type':'application/json','X-ProofLoop':'1'})
        res=c.getresponse();body=json.loads(res.read());c.close()
        assert res.status==200,(res.status,body)
        events.append({'route':route,'request':data,'response':body})
        return body
    def review(rev,reason,status='approved'):
        return api('review',{'revision_id':rev['id'],'status':status,'reviewer':'assistant HTTP workflow verification','note':reason})
    try:
        proposals=api('generate',{'mode':'offline'})
        assert len(proposals['revisions'])==4
        first=proposals['revisions'][0]
        skipped=api('run',{'revision_id':first['id']});assert skipped['outcome']=='not_run'
        for rev in proposals['revisions']:
            review(rev,'Assistant checked exact arithmetic against SPEC v1; owner acceptance pending.')
            run=api('run',{'revision_id':rev['id']});assert run['outcome']=='passed'
        # Constructed incorrect assumption is honestly labeled, corrected by review, then executed.
        bad=api('generate',{'mode':'constructed_incorrect'})['revisions'][0]
        review(bad,'R5 applies after R4: net 4500 must pay 500 shipping. Reject pre-discount threshold.','rejected')
        blocked=api('run',{'revision_id':bad['id']});assert blocked['outcome']=='not_run'
        fixed=copy.deepcopy(bad['test'])
        fixed['expected']['body'].update(shipping_cents=500,total_cents=5000)
        fixed['title']='Corrected constructed example: shipping after discount'
        fixed['rationale']='R4: 5000 - 500 = 4500. R5: 4500 < 5000 so shipping = 500; total = 5000.'
        new=api('edit',{'revision_id':bad['id'],'test':fixed,'editor':'assistant HTTP workflow verification'})
        pending=api('run',{'revision_id':new['id']});assert pending['outcome']=='not_run'
        review(new,'Corrected expected shipping using R4 then R5.')
        assert api('run',{'revision_id':new['id']})['outcome']=='passed'
        # Environment demonstration: actual connection refusal, created by reserving a non-listening local port.
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            unavailable=save_run(app.store,first['id'],sock.getsockname()[1],app.source,app.spec_hash)
        assert unavailable['outcome']=='execution_error'
        recovered=api('run',{'revision_id':first['id'],'parent_run_id':unavailable['id']})
        assert recovered['outcome']=='passed'
        api('diagnose',{'run_id':unavailable['id'],'classification':'environment',
            'reviewer':'assistant HTTP workflow verification','note':'Controlled non-listening loopback port produced actual connection refusal; recovery used the running target. Not a product defect.'})
        result={'verified_at':now(),'scope':'HTTP API + runner, not browser interaction or live provider generation',
                'source':app.source,'events':events,'records':{k:app.store.all(k) for k in ('generation','revision','review','run','diagnosis')},
                'measured':{'offline_proposals':4,'offline_schema_valid':4,'approved_unchanged':4,
                    'constructed_incorrect':1,'constructed_rejected':1,'constructed_corrected_revisions':1,
                    'environment_errors':1,'successful_recoveries':1,'live_provider_calls':0}}
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result['measured']))
    finally:
        app.shutdown();thread.join();app.server_close()

if __name__=='__main__':main()
