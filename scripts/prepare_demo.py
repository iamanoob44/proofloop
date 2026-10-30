"""Restore saved evidence into a new demo database; never approve or regenerate tests."""
import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from proofloop.common import spec
from proofloop.storage import Store
from scripts.replay_generated import KINDS, read_history, select_revisions


def prepare(history, destination):
    records = read_history(history=history)
    # Validate all selected current revisions before creating any output file.
    staging = Store(':memory:')
    try:
        for kind in KINDS:
            for record in records[kind]:
                staging.append(kind, record)
        latest = {r['test_id']: r for r in records['revision']}
        select_revisions(staging, [r['id'] for r in latest.values()], spec())
        for run in records['run']:
            revision = staging.get('revision', run['revision_id'])
            if run['revision'] != revision:
                raise ValueError('Run snapshot differs from preserved revision')
            if run.get('parent_run_id'):
                parent = staging.get('run', run['parent_run_id'])
                if parent['revision_id'] != run['revision_id']:
                    raise ValueError('Retest parent differs from preserved revision')
        for diagnosis in records['diagnosis']:
            staging.get('run', diagnosis['run_id'])
    finally:
        staging.close()
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also prevents accidentally modifying an existing demo DB.
    with destination.open('xb'):
        pass
    store = Store(str(destination))
    try:
        for kind in KINDS:
            for record in records[kind]:
                store.append(kind, record)
    finally:
        store.close()
    return {kind: len(records[kind]) for kind in KINDS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', default=str(ROOT / 'evidence/generated-suite-2026-10-31/demo-history.json'))
    parser.add_argument('--db', default='data/demo-' + uuid.uuid4().hex[:8] + '.sqlite')
    args = parser.parse_args()
    counts = prepare(args.history, args.db)
    print(json.dumps({'db': str(Path(args.db).resolve()), 'records': counts,
                      'label': 'Restored recorded live generation and real executions; no new provider call'}))
    print('Open this database with: python -m proofloop serve --db "' + str(Path(args.db).resolve()) + '" --port 8768')


if __name__ == '__main__':
    main()
