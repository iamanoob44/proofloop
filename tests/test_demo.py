import json
import tempfile
import unittest
from pathlib import Path

from proofloop.common import ROOT
from scripts.prepare_demo import prepare
from scripts.replay_generated import read_history


class DemoRestoreTests(unittest.TestCase):
    def test_restore_preserves_every_record_and_refuses_overwrite(self):
        history = ROOT / 'evidence/generated-suite-2026-10-31/demo-history.json'
        records = read_history(history=history)
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'demo.sqlite'
            counts = prepare(history, destination)
            self.assertEqual(counts['revision'], 3)
            self.assertEqual(read_history(db=destination), records)
            original = destination.read_bytes()
            with self.assertRaises(FileExistsError):
                prepare(history, destination)
            self.assertEqual(destination.read_bytes(), original)

    def test_missing_approval_fails_before_creating_database(self):
        records = read_history(history=ROOT / 'evidence/generated-suite-2026-10-31/demo-history.json')
        records['review'] = []
        with tempfile.TemporaryDirectory() as temp:
            history = Path(temp) / 'history.json'
            history.write_text(json.dumps(records), encoding='utf-8')
            destination = Path(temp) / 'demo.sqlite'
            with self.assertRaisesRegex(ValueError, 'approved'):
                prepare(history, destination)
            self.assertFalse(destination.exists())
