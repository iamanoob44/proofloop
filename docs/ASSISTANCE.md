# Development assistance record

The project owner supplied the ProofLoop direction, scope, sequencing, and evidence requirements. The assistant proposed the Python standard-library stack and the concrete fictional checkout rules; owner acceptance remains pending. The assistant is writing and executing the initial implementation in this session. Do not present this as unaided personal authorship.

Stage 1: specification written before checkout implementation and reference tests. Chosen independent boundary: exactly 5000 cents after discount qualifies for free shipping. Rejected approach: calculating expected results by calling the checkout implementation; that would share its bugs.

No user interview, productivity measurement, live provider generation, or owner review has occurred yet.

Stage 2: the assistant implemented a disclosed strict shipping threshold and ran 15 independently specified reference scenarios over HTTP. Fourteen passed and one failed. It corrected `>` to `>=`, preserved the test revision/expectation hash and original failure, then observed 15 passing scenarios. The failing run was captured before the repair commit; history was not manufactured afterwards.

Stage 3: accepted structured proposals and append-only SQLite records. Corrected a first request-handler implementation that parsed JSON before rejecting an unsupported route, contrary to the specification's operation-first precedence. Added a regression check. Corrected the first UI revision so an error does not discard an unsaved draft. Rejected automatic fallback from live generation to canned content because that would misrepresent provenance.

The deliberately wrong coupon/shipping proposal is a constructed teaching example. No live model mistake has been observed. Provider response tests use labeled mocks. The environment example uses an actual refused loopback connection. Instability detection is unit-tested with a simulated outcome.

Owner contribution currently evidenced: selecting the product direction and defining a tight scope, explicit independent expectations, honest provenance, and acceptance gates in the supplied brief. The owner has not yet approved the proposed monetary rules, personally reviewed the code/tests, or demonstrated understanding in this session. Any later submission statement must add only judgments the owner actually makes; do not claim assistant decisions as personal corrections.
