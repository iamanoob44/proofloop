"""Fictional quote service. Seeded R5 defect disclosed in docs/DEMO.md."""
CATALOG = {'TEE': {'price': 2500, 'stock': 4},
           'PIN': {'price': 501, 'stock': 10},
           'MUG': {'price': 1500, 'stock': 3}}
FIXTURE = 'catalog-v1'


def quote(body, method='POST', path='/checkout'):
    def error(status, code):
        return status, {'error': code}
    if path != '/checkout':
        return error(404, 'NOT_FOUND')
    if method != 'POST':
        return error(405, 'METHOD_NOT_ALLOWED')
    if (type(body) is not dict or not {'items'} <= body.keys()
            or not body.keys() <= {'items', 'coupon'}
            or type(body['items']) is not list or not 1 <= len(body['items']) <= 10
            or ('coupon' in body and type(body['coupon']) is not str)):
        return error(400, 'INVALID_REQUEST')
    seen = set()
    for item in body['items']:
        if (type(item) is not dict or set(item) != {'sku', 'quantity'}
                or type(item['sku']) is not str or not item['sku']
                or type(item['quantity']) is not int or not 1 <= item['quantity'] <= 10
                or item['sku'] in seen):
            return error(400, 'INVALID_REQUEST')
        seen.add(item['sku'])
    for item in body['items']:
        if item['sku'] not in CATALOG:
            return error(404, 'UNKNOWN_SKU')
        if item['quantity'] > CATALOG[item['sku']]['stock']:
            return error(409, 'OUT_OF_STOCK')
    subtotal = sum(CATALOG[i['sku']]['price'] * i['quantity'] for i in body['items'])
    coupon = body.get('coupon', '')
    if coupon not in ('', 'SAVE10'):
        return error(422, 'INVALID_COUPON')
    if coupon and subtotal < 3000:
        return error(422, 'COUPON_INELIGIBLE')
    discount = subtotal * 10 // 100 if coupon else 0
    net = subtotal - discount
    shipping = 0 if net >= 5000 else 500  # R5: inclusive, after discount.
    return 200, {'subtotal_cents': subtotal, 'discount_cents': discount,
                 'shipping_cents': shipping, 'total_cents': net + shipping}
