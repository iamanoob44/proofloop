"""Replay selection checks use explicitly synthetic provider records."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from proofloop.common import ROOT, digest, spec
from proofloop.storage import Store
from scripts.replay_generated import read_history, select_revisions


class ReplaySelectionTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:')
        self.test = json.loads((ROOT / 'fixtures/offline.json').read_text())['tests'][0]
        self.generation = self.store.append('generation', {
            'mode': 'live', 'status': 'validated', 'provider_response_id': 'synthetic-test-only',
            'spec_hash': digest(spec()), 'input': {'specification': spec()},
            'output_text': json.dumps({'tests': [self.test]})})
        self.rev = self.store.import_tests([self.test], {
            'mode': 'live', 'generation_id': self.generation['id']}, digest(spec()))[0]

    def tearDown(self):
        self.store.close()

    def approve(self, rev):
        self.store.review(rev['id'], 'approved', 'automated test', 'Synthetic test setup only')

    def test_pending_rejected_and_superseded_cannot_replay(self):
        with self.assertRaisesRegex(ValueError, 'approved'):
            select_revisions(self.store, [self.rev['id']], spec())
        self.store.review(self.rev['id'], 'rejected', 'automated test', 'Synthetic rejection')
        with self.assertRaisesRegex(ValueError, 'approved'):
            select_revisions(self.store, [self.rev['id']], spec())
        self.approve(self.rev)
        edited = self.store.edit(self.rev['id'], self.test, 'automated test')
        with self.assertRaisesRegex(ValueError, 'approved'):
            select_revisions(self.store, [self.rev['id']], spec())
        self.approve(edited)
        self.assertEqual(select_revisions(self.store, [edited['id']], spec()), [edited])

    def test_spec_mismatch_and_duplicate_selection_fail(self):
        self.approve(self.rev)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            select_revisions(self.store, [self.rev['id']], spec() + '\n')
        with self.assertRaisesRegex(ValueError, 'distinct'):
            select_revisions(self.store, [self.rev['id']] * 2, spec())

    def test_offline_origin_and_substituted_proposal_fail(self):
        offline = self.store.import_tests([self.test], {
            'mode': 'offline', 'generation_id': self.generation['id']}, digest(spec()))[0]
        self.approve(offline)
        with self.assertRaisesRegex(ValueError, 'live generation'):
            select_revisions(self.store, [offline['id']], spec())
        altered = copy.deepcopy(self.test)
        altered['title'] = 'Not the original provider output'
        forged = self.store.import_tests([altered], self.rev['provenance'], digest(spec()))[0]
        self.approve(forged)
        with self.assertRaisesRegex(ValueError, 'provider output'):
            select_revisions(self.store, [forged['id']], spec())

    def test_snapshot_retains_identity_and_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'source.sqlite'
            source = Store(str(path))
            original = source.append('generation', self.generation)
            source.close()
            before = path.read_bytes()
            history = read_history(db=path)
            self.assertEqual(history['generation'], [original])
            self.assertEqual(path.read_bytes(), before)
            export = Path(temp) / 'history.json'
            export.write_text(json.dumps(history), encoding='utf-8')
            self.assertEqual(read_history(history=export), history)
            with self.assertRaises(sqlite3.OperationalError):
                read_history(db=Path(temp) / 'missing.sqlite')
            self.assertFalse((Path(temp) / 'missing.sqlite').exists())
