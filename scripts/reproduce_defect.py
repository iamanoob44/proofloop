"""Replay a disclosed source defect in an isolated local clone; preserve every attempt."""
import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',default=None)
    p.add_argument('--pause',action='store_true',help='Pause for live explanation before repair')
    args=p.parse_args()
    out=Path(args.output_dir or ('data/reproduction-'+str(uuid.uuid4())[:8])).resolve()
    out.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='proofloop-replay-') as temp:
        clone=Path(temp)/'app'
        subprocess.run(['git','clone','--quiet','--no-hardlinks',str(ROOT),str(clone)],check=True)
        source=clone/'proofloop/checkout.py';fixed=source.read_text()
        correct='shipping = 0 if net >= 5000 else 500'
        seeded='shipping = 0 if net > 5000 else 500'
        assert fixed.count(correct)==1,'Unexpected source; do not patch blindly'
        source.write_text(fixed.replace(correct,seeded))
        patch=subprocess.check_output(['git','diff','--','proofloop/checkout.py'],cwd=clone,text=True)
        (out/'seeded.patch').write_text(patch)
        print('DISCLOSED SEEDED DEFECT: strict > instead of inclusive >=. Temporary clone only.',flush=True)
        print(patch,flush=True)
        def run(*a):
            subprocess.run([sys.executable,'-m','proofloop',*a],cwd=clone,check=True)
        db=str(out/'demo.sqlite')
        run('reference','--db',db,'--output',str(out/'before.json'))
        before=json.loads((out/'before.json').read_text())
        failures=[r for r in before['runs'] if r['outcome']=='failed_assertion']
        assert len(failures)==1 and failures[0]['revision']['test']['id']=='shipping-exact'
        failed=failures[0]
        print(json.dumps({'requirement':'R5','expected':failed['revision']['test']['expected'],
                          'observed':failed['actual'],'revision':failed['revision_id']},indent=2),flush=True)
        if args.pause:input('Explain the mismatch and the source operator. Press Enter to apply the repair: ')
        source.write_text(fixed)
        print('SOURCE REPAIR APPLIED: > becomes >=. Test remains unchanged.',flush=True)
        run('retest','--db',db,'--parent',failed['id'],'--output',str(out/'after.json'))
        after=json.loads((out/'after.json').read_text())
        assert after['revision_id']==failed['revision_id']
        assert after['revision']['test_hash']==failed['revision']['test_hash']
        assert after['outcome']=='passed'
        run('reference','--db',db,'--output',str(out/'regression.json'))
        assert json.loads((out/'regression.json').read_text())['summary']['passed']==15
        run('export','--db',db,'--output',str(out/'history.json'))
        (out/'result.json').write_text(json.dumps({'status':'verified','before_run':failed['id'],
            'after_run':after['id'],'same_revision':after['revision_id'],'source_revision':after['source']['git_revision'],
            'label':'Real local HTTP execution against a disclosed source mutation in an isolated clone'},indent=2)+'\n')
        print('Verified same-revision repair and 15/15 regression scenarios. Evidence: '+str(out))

if __name__=='__main__':main()
