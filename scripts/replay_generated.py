"""Replay selected, already-approved live revisions without altering their history.

No provider calls or new approvals are made. The target is a temporary Git clone.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from proofloop.common import digest
from proofloop.schema import validate_batch, validate
from proofloop.storage import Store

KINDS = ('generation', 'revision', 'review', 'run', 'diagnosis')
CORRECT = b'shipping = 0 if net >= 5000 else 500'
SEEDED = b'shipping = 0 if net > 5000 else 500'

# Runs in a fresh interpreter in the isolated target, so repaired source is reloaded.
# -B prevents a same-size, same-second source repair from reusing stale bytecode.
WORKER = '''
import json, sys, threading
from pathlib import Path
from proofloop.server import App
from proofloop.runner import save_run
db, destination, selections = sys.argv[1:]
app = App(0, db)
thread = threading.Thread(target=app.serve_forever, daemon=True)
thread.start()
try:
    runs = [save_run(app.store, item['revision_id'], app.server_port,
                    app.source, app.spec_hash, item.get('parent_run_id'))
            for item in json.loads(selections)]
    Path(destination).write_text(json.dumps({'runs': runs}, indent=2)+'\\n', encoding='utf-8')
finally:
    app.shutdown()
    thread.join()
    app.server_close()
'''


def read_history(db=None, history=None):
    if history:
        value = json.loads(Path(history).read_text(encoding='utf-8'))
        if not isinstance(value, dict) or any(not isinstance(value.get(k), list) for k in KINDS):
            raise ValueError('Use a ProofLoop CLI history export containing all five record lists')
        return {k: value[k] for k in KINDS}
    # A read-only transaction includes WAL records and never creates a missing DB.
    conn = sqlite3.connect(Path(db).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        rows = conn.execute('SELECT kind,payload FROM records ORDER BY seq').fetchall()
        return {k: [json.loads(raw) for kind, raw in rows if kind == k] for k in KINDS}
    finally:
        conn.close()


def select_revisions(store, ids, spec_text):
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Select one or more distinct existing revision IDs')
    selected = []
    for revision_id in ids:
        rev = store.get('revision', revision_id)
        latest = [r for r in store.all('revision') if r['test_id'] == rev['test_id']][-1]
        if latest['id'] != revision_id or store.status(revision_id) != 'approved':
            raise ValueError('Replay requires the current approved revision; no automatic approvals')
        validate(rev['test'])
        if rev['test_hash'] != digest(rev['test']) or rev['spec_hash'] != digest(spec_text):
            raise ValueError('Revision test/specification hash mismatch')
        provenance = rev['provenance']
        generation = store.get('generation', provenance.get('generation_id'))
        if (provenance.get('mode') != 'live' or generation.get('mode') != 'live'
                or generation.get('status') != 'validated' or not generation.get('provider_response_id')):
            raise ValueError('Selected revision must link to a saved successful live generation')
        if (generation['spec_hash'] != rev['spec_hash']
                or generation['input']['specification'] != spec_text):
            raise ValueError('Generation specification differs from the replay target')
        original = rev
        seen = set()
        while original.get('parent_revision'):
            if original['id'] in seen:
                raise ValueError('Cyclic revision ancestry')
            seen.add(original['id'])
            original = store.get('revision', original['parent_revision'])
            if (original['test_id'] != rev['test_id'] or original['provenance'] != provenance
                    or original['test_hash'] != digest(original['test'])):
                raise ValueError('Broken revision provenance')
        proposals = validate_batch(json.loads(generation['output_text']))
        if original['test'] not in proposals:
            raise ValueError('Original revision does not match the saved provider output')
        selected.append(rev)
    return selected


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def replay(records, ids, out, pause=False):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'input-history.json', records)
    db = out / 'demo.sqlite'
    store = Store(str(db))
    try:
        for kind in KINDS:
            for record in records[kind]:
                store.append(kind, record)
        with tempfile.TemporaryDirectory(prefix='proofloop-live-replay-') as temp:
            clone = Path(temp) / 'app'
            subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], check=True)
            selected = select_revisions(store, ids, (clone / 'SPEC.md').read_text(encoding='utf-8'))
            store.close()
            store = None
            source = clone / 'proofloop/checkout.py'
            fixed = source.read_bytes()
            if fixed.count(CORRECT) != 1:
                raise ValueError('Unexpected source; refusing to inject a defect')
            source.write_bytes(fixed.replace(CORRECT, SEEDED))
            patch = subprocess.check_output(['git', 'diff', '--', 'proofloop/checkout.py'], cwd=clone)
            (out / 'seeded.patch').write_bytes(patch)

            def run_batch(filename, selections):
                subprocess.run([sys.executable, '-B', '-c', WORKER, str(db), str(out / filename),
                                json.dumps(selections)], cwd=clone, check=True)
                return json.loads((out / filename).read_text(encoding='utf-8'))['runs']

            before = run_batch('before.json', [{'revision_id': r['id']} for r in selected])
            print('Seeded outcomes: ' + ', '.join(r['outcome'] for r in before), flush=True)
            if pause:
                input('Inspect the saved assertions and source patch. Press Enter to repair the source: ')
            source.write_bytes(fixed)
            after = run_batch('after.json', [{'revision_id': r['revision_id'], 'parent_run_id': r['id']}
                                              for r in before])
            for old, new in zip(before, after):
                if (old['revision'] != new['revision'] or new['parent_run_id'] != old['id']
                        or old['source']['source_hash'] == new['source']['source_hash']):
                    raise ValueError('Retest identity/source invariant failed')
            for command, filename in [('reference', 'regression.json'), ('export', 'history.json')]:
                subprocess.run([sys.executable, '-B', '-m', 'proofloop', command, '--db', str(db),
                                '--output', str(out / filename)], cwd=clone, check=True)
            regression = json.loads((out / 'regression.json').read_text(encoding='utf-8'))
            pairs = [{'revision_id': old['revision_id'], 'test_hash': old['revision']['test_hash'],
                      'generation_id': old['revision']['provenance']['generation_id'],
                      'before_run': old['id'], 'before_outcome': old['outcome'],
                      'after_run': new['id'], 'after_outcome': new['outcome'],
                      'detected_seeded_defect': old['outcome'] == 'failed_assertion' and new['outcome'] == 'passed'}
                     for old, new in zip(before, after)]
            result = {'label': 'Saved live-generated revisions; actual isolated HTTP execution; no new provider call or approval',
                      'input_history_hash': digest(records), 'selected_revisions': ids,
                      'pairs': pairs, 'detected_count': sum(p['detected_seeded_defect'] for p in pairs),
                      'fixed_all_passed': all(r['outcome'] == 'passed' for r in after),
                      'reference_summary': regression['summary']}
            write_json(out / 'result.json', result)
            print(json.dumps(result, indent=2), flush=True)
            print('Evidence directory: ' + str(out), flush=True)
            if not result['fixed_all_passed'] or regression['summary']['passed'] != 15:
                raise ValueError('Replay preserved, but fixed-target verification failed; inspect reports')
            return result
    finally:
        if store is not None:
            store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--db', help='Existing database, read only')
    source.add_argument('--history', help='Exported CLI history; permits fresh-clone replay')
    parser.add_argument('--revision', action='append', required=True, help='Approved revision ID; repeat to select several')
    parser.add_argument('--output-dir', default=None, help='New directory only; existing evidence is never overwritten')
    parser.add_argument('--pause', action='store_true')
    args = parser.parse_args()
    replay(read_history(args.db, args.history), args.revision,
           args.output_dir or ('data/live-replay-' + str(uuid.uuid4())[:8]), args.pause)


if __name__ == '__main__':
    main()
