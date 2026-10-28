"""Append-only revisions, review events, runs, and diagnoses in SQLite."""
import json
import sqlite3
import threading
import uuid
from .common import digest, encode, now
from .schema import validate


class Store:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS records (seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)')
        self.db.commit()

    def append(self, kind, record):
        record = dict(record)
        record.setdefault('id', str(uuid.uuid4()))
        record.setdefault('created_at', now())
        with self.lock, self.db:
            self.db.execute('INSERT INTO records(kind,id,payload) VALUES (?,?,?)', (kind, record['id'], encode(record)))
        return record

    def all(self, kind):
        with self.lock:
            return [json.loads(row[0]) for row in self.db.execute('SELECT payload FROM records WHERE kind=? ORDER BY seq', (kind,))]

    def get(self, kind, id):
        with self.lock:
            row = self.db.execute('SELECT payload FROM records WHERE kind=? AND id=?', (kind, id)).fetchone()
        if not row:
            raise ValueError(f'Unknown {kind}')
        return json.loads(row[0])

    def import_tests(self, tests, provenance, spec_hash):
        result = []
        for test in tests:
            validate(test)
        for test in tests:
            result.append(self.append('revision', {'test_id': str(uuid.uuid4()), 'number': 1,
                'test': test, 'test_hash': digest(test), 'spec_hash': spec_hash,
                'provenance': provenance, 'parent_revision': None}))
        return result

    def status(self, revision_id):
        events = [r for r in self.all('review') if r['revision_id'] == revision_id]
        return events[-1]['status'] if events else 'pending'

    def edit(self, revision_id, test, editor):
        validate(test)
        with self.lock:
            old = self.get('revision', revision_id)
            if test['id'] != old['test']['id']:
                raise ValueError('Stable test ID cannot change')
            latest = [r for r in self.all('revision') if r['test_id'] == old['test_id']][-1]
            if latest['id'] != revision_id:
                raise ValueError('Stale revision: refresh before editing')
            return self.append('revision', {'test_id': old['test_id'], 'number': old['number'] + 1,
                'test': test, 'test_hash': digest(test), 'spec_hash': old['spec_hash'],
                'provenance': old['provenance'], 'parent_revision': revision_id, 'editor': editor})

    def review(self, revision_id, status, reviewer, note):
        with self.lock:
            rev = self.get('revision', revision_id)
            latest = [r for r in self.all('revision') if r['test_id'] == rev['test_id']][-1]
            if rev['id'] != latest['id']:
                raise ValueError('Cannot approve a superseded revision')
            if status not in {'approved', 'rejected'} or not reviewer.strip() or not note.strip():
                raise ValueError('Review needs approved/rejected status, reviewer and business reason')
            return self.append('review', {'revision_id': revision_id, 'status': status,
                                         'reviewer': reviewer[:120], 'note': note[:2000]})

    def close(self):
        self.db.close()
