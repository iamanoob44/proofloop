"""Strict allowlisted, non-executable proposal contract, version 1."""
import json
import re

FIELDS = {'schema_version', 'id', 'requirement_refs', 'title', 'category',
          'request', 'fixture', 'expected', 'rationale'}
CATEGORIES = {'normal', 'boundary', 'invalid', 'exception'}
ERRORS = {'INVALID_REQUEST', 'UNKNOWN_SKU', 'OUT_OF_STOCK', 'INVALID_COUPON',
          'COUPON_INELIGIBLE', 'NOT_FOUND', 'METHOD_NOT_ALLOWED'}
MONEY = {'subtotal_cents', 'discount_cents', 'shipping_cents', 'total_cents'}


class InvalidTest(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidTest(message)


def validate(test):
    require(type(test) is dict and set(test) == FIELDS, 'Unexpected or missing test fields')
    require(type(test['schema_version']) is int and test['schema_version'] == 1, 'Unsupported schema')
    require(type(test['id']) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', test['id']), 'Invalid test ID')
    for key in ('title', 'rationale'):
        require(type(test[key]) is str and 1 <= len(test[key]) <= 2000, f'Invalid {key}')
    refs = test['requirement_refs']
    require(type(refs) is list and 1 <= len(refs) <= 6 and all(type(r) is str and r in
            {'R1', 'R2', 'R3', 'R4', 'R5', 'R6'} for r in refs), 'Invalid requirement references')
    require(type(test['category']) is str and test['category'] in CATEGORIES, 'Invalid category')
    require(test['fixture'] == 'catalog-v1', 'Unknown fixture')
    req = test['request']
    require(type(req) is dict and set(req) == {'method', 'path', 'body'}, 'Invalid request envelope')
    require(type(req['method']) is str and req['method'] in {'POST', 'GET'}, 'Unsupported method')
    require(type(req['path']) is str and req['path'] in {'/checkout', '/unsupported'}, 'Unsupported path')
    try:
        require(len(json.dumps(req['body'], allow_nan=False)) <= 12000, 'Request body too large')
    except (ValueError, TypeError, RecursionError) as exc:
        raise InvalidTest('Body must be finite JSON') from exc
    exp = test['expected']
    require(type(exp) is dict and set(exp) == {'status', 'body'}, 'Invalid expectation envelope')
    require(type(exp['status']) is int and exp['status'] in {200, 400, 404, 405, 409, 422}, 'Unsupported expected status')
    body = exp['body']
    require(type(body) is dict, 'Expected body must be an object')
    if exp['status'] == 200:
        require(set(body) == MONEY and all(type(v) is int and 0 <= v <= 1000000 for v in body.values()),
                'Success requires all four integer money fields')
    else:
        require(set(body) == {'error'} and type(body['error']) is str and body['error'] in ERRORS,
                'Invalid expected error')
    return test


def validate_batch(value):
    require(type(value) is dict and set(value) == {'tests'}, 'Expected a tests wrapper')
    require(type(value['tests']) is list and 1 <= len(value['tests']) <= 20, 'Expected 1–20 tests')
    for test in value['tests']:
        validate(test)
    require(len({t['id'] for t in value['tests']}) == len(value['tests']), 'Duplicate IDs')
    return value['tests']
