import argparse
import json
import threading
from pathlib import Path
from .common import ROOT, digest
from .runner import save_run
from .schema import validate_batch
from .server import App


def main():
    p = argparse.ArgumentParser(description='ProofLoop local development and verification')
    p.add_argument('command', choices=['serve', 'reference', 'retest', 'export'])
    p.add_argument('--db', default='data/proofloop.sqlite')
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--output', default='evidence/run.json')
    p.add_argument('--parent', help='Exact earlier run ID for retest')
    args = p.parse_args()
    app = App(args.port if args.command == 'serve' else 0, args.db)
    if args.command == 'serve':
        print(f'ProofLoop: http://127.0.0.1:{app.server_port} | source {app.source["source_hash"][:12]}', flush=True)
        try:
            app.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            app.server_close()
        return
    thread = threading.Thread(target=app.serve_forever, daemon=True)
    thread.start()
    try:
        if args.command == 'reference':
            tests = validate_batch(json.loads((ROOT / 'fixtures/reference.json').read_text()))
            revs = app.store.import_tests(tests, {'mode': 'independent_reference', 'model': None,
                'author': 'assistant-authored from specification; no provider generation'}, app.spec_hash)
            runs = []
            for r in revs:
                app.store.review(r['id'], 'approved', 'assistant validation',
                                 'Arithmetic inspected against SPEC v1 for automated demonstration; not owner acceptance.')
                runs.append(save_run(app.store, r['id'], app.server_port, app.source, app.spec_hash))
            result = {'source': app.source, 'runs': runs, 'summary': {s: sum(r['outcome'] == s for r in runs)
                for s in ['passed', 'failed_assertion', 'invalid_test', 'execution_error', 'not_run']}}
        elif args.command == 'retest':
            if not args.parent:
                p.error('--parent required')
            old = app.store.get('run', args.parent)
            result = save_run(app.store, old['revision_id'], app.server_port, app.source, app.spec_hash, args.parent)
        else:
            result = {k: app.store.all(k) for k in ('revision', 'review', 'generation', 'run', 'diagnosis')}
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'output': str(target), 'summary': result.get('summary'),
                          'outcome': result.get('outcome'), 'run_id': result.get('id')}))
    finally:
        app.shutdown()
        thread.join()
        app.server_close()


if __name__ == '__main__':
    main()
