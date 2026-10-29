import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def spec():
    return (ROOT / 'SPEC.md').read_text(encoding='utf-8')


def source_state():
    files = sorted([ROOT / 'SPEC.md', *ROOT.glob('proofloop/**/*.py'),
                    *ROOT.glob('proofloop/web/*'), *ROOT.glob('fixtures/*.json')])
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in files if p.is_file()}
    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(ROOT), *args],
                                           stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return 'unavailable'
    return {'git_revision': git('rev-parse', 'HEAD'),
            'working_tree': git('status', '--porcelain'),
            'source_hash': digest(hashes), 'files': hashes}
