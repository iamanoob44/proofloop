# Checkout specification v1 — proposed, awaiting owner acceptance

This is a fictional checkout quote service. No purchases, payments, inventory reservations, external commerce APIs, or real customer data exist. All money is USD integer cents.

Fixture `catalog-v1`: TEE costs 2500, stock 4; PIN costs 501, stock 10; MUG costs 1500, stock 3. A quote never changes stock. Every request uses this same immutable catalog, which is the fixture preparation step.

Rules are checked in the following order; the first error ends processing. An error response contains exactly `{ "error": "CODE" }`.

- **R1 — Operation and shape.** Only POST /checkout is supported. Unknown paths return 404 NOT_FOUND; other methods at /checkout return 405 METHOD_NOT_ALLOWED. Body must be a JSON object with `items` and optionally `coupon`, no extra keys. `items` must be a list with 1–10 entries. Invalid JSON or shape returns 400 INVALID_REQUEST. Each entry has exactly `sku` (nonempty string) and `quantity` (integer 1–10; booleans are not integers). Duplicate SKUs are rejected. Shape and duplicates are checked for all entries before catalog checks. If present, coupon must be a string.
- **R2 — Catalog and stock.** Check entries in input order. Unknown SKU returns 404 UNKNOWN_SKU; quantity exceeding fixed stock returns 409 OUT_OF_STOCK. No stock mutation occurs.
- **R3 — Subtotal.** Sum price × quantity using integer cents. Do not use floating point arithmetic.
- **R4 — Coupon.** Omitted coupon or empty string means no coupon. Only SAVE10 is supported. Any other nonempty string returns 422 INVALID_COUPON. SAVE10 requires subtotal >= 3000; otherwise return 422 COUPON_INELIGIBLE. Discount is floor(subtotal × 10 / 100), rounded down once on the full subtotal.
- **R5 — Shipping.** Compute net = subtotal − discount. Shipping is zero when net >= 5000 (inclusive); otherwise 500 cents. Apply the threshold after the discount.
- **R6 — Success.** Return HTTP 200 and exactly `subtotal_cents`, `discount_cents`, `shipping_cents`, `total_cents`; total = subtotal − discount + shipping.

## Independent arithmetic examples

Two TEEs: subtotal 5000, no discount, shipping 0, total 5000.
Two TEEs with SAVE10: subtotal 5000, discount 500, net 4500, shipping 500, total 5000.
Six PINs with SAVE10: subtotal 3006, discount 300, shipping 500, total 3206.
Two MUGs with SAVE10: subtotal 3000, discount 300, shipping 500, total 3200.

Specification changes require a new version and renewed review of affected tests. The v1 app rejects edits to its specification file while running; restart after an intentional change and reimport proposals.
