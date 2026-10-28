import http.client
import json
import time
from .common import digest, now
from .checkout import CATALOG, FIXTURE
from .schema import InvalidTest, validate


def execute(revision, status, port, source, spec_hash, parent=None):
    started = time.monotonic()
    test = revision['test']
    result = {'created_at': now(), 'revision_id': revision['id'], 'revision': revision,
              'source': source, 'spec_hash': spec_hash, 'fixture': {'id': FIXTURE, 'hash': digest(CATALOG), 'data': CATALOG},
              'parent_run_id': parent, 'request': test.get('request'), 'actual': None,
              'assertions': [], 'outcome': 'not_run', 'error': None, 'diagnosis': 'unreviewed',
              'target': f'http://127.0.0.1:{port}', 'review_status_at_start': status}
    try:
        validate(test)
        if digest(test) != revision['test_hash']:
            raise InvalidTest('Test hash mismatch')
        if revision['spec_hash'] != spec_hash:
            raise InvalidTest('Specification changed; import and review against the new specification')
        if status != 'approved':
            result['error'] = 'Only the current approved revision executes'
            return result
        request = test['request']
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
        try:
            conn.request(request['method'], request['path'], body=json.dumps(request['body']),
                         headers={'Content-Type': 'application/json'})
            response = conn.getresponse()
            raw = response.read(65537)
            result['response_source_hash'] = response.getheader('X-ProofLoop-Source')
            result['actual'] = {'status': response.status, 'raw_body': raw.decode('utf-8', errors='replace')}
            if len(raw) > 65536:
                raise OSError('Response too large')
            body = json.loads(raw)
            result['actual']['body'] = body
            if result['response_source_hash'] != source['source_hash']:
                raise OSError('Target source identity mismatch')
        finally:
            conn.close()
        expected = test['expected']
        # Canonical JSON comparison distinguishes false from 0, including nested values.
        assertions = [{'field': 'status', 'expected': expected['status'], 'actual': response.status,
                       'passed': type(response.status) is int and expected['status'] == response.status},
                      {'field': 'body (exact)', 'expected': expected['body'], 'actual': body,
                       'passed': digest(expected['body']) == digest(body)}]
        result['assertions'] = assertions
        result['outcome'] = 'passed' if all(a['passed'] for a in assertions) else 'failed_assertion'
    except (InvalidTest, KeyError, TypeError) as exc:
        result['outcome'] = 'invalid_test'
        result['error'] = str(exc)
    except (OSError, http.client.HTTPException, ValueError) as exc:
        result['outcome'] = 'execution_error'
        result['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        result['duration_ms'] = round((time.monotonic() - started) * 1000, 3)
    return result


def save_run(store, revision_id, port, source, spec_hash, parent=None):
    revision = store.get('revision', revision_id)
    latest = [r for r in store.all('revision') if r['test_id'] == revision['test_id']][-1]
    status = store.status(revision_id) if latest['id'] == revision_id else 'superseded'
    previous = store.get('run', parent) if parent else None
    if previous and previous['revision_id'] != revision_id:
        raise ValueError('Retest must use the exact original revision')
    run = execute(revision, status, port, source, spec_hash, parent)
    same = [r for r in store.all('run') if r['revision_id'] == revision_id
            and r['source']['source_hash'] == source['source_hash']
            and r['spec_hash'] == spec_hash and r['fixture']['hash'] == run['fixture']['hash']]
    comparable = {'passed', 'failed_assertion'}
    run['inconsistent_result'] = run['outcome'] in comparable and any(
        r['outcome'] in comparable and r['outcome'] != run['outcome'] for r in same)
    run['investigation_note'] = 'Different assertion outcomes with matching inputs/source; investigate.' if run['inconsistent_result'] else None
    return store.append('run', run)
