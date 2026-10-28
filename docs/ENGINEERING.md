# Implementation and evidence

## Modules and flow

| Module | Responsibility |
|---|---|
| SPEC.md | Independent fictional business contract; pending owner acceptance |
| checkout.py | Fixed catalog and pure checkout calculations; no expected-test generation |
| generator.py | One OpenAI Responses endpoint or explicitly selected prepared examples |
| schema.py | Version 1 proposal contract; rejects executable/extra fields and arbitrary targets |
| storage.py | SQLite append-only revisions, reviews, generations, runs and diagnoses |
| runner.py | Fixed-loopback HTTP requests, exact status/body assertions and linked attempts |
| server.py | Local UI/API and checkout endpoint; source-change and origin guards |
| web/ | Requirements, proposal editor, approval controls and comparison reports |

Data moves from specification + scenario focus to proposal generation, validation and pending revisions. A reviewer can reject or approve; editing appends a pending revision. Only the latest approved revision can execute. The runner prepares the immutable catalog by using the stateless quote endpoint; inventory never changes. Each HTTP response is compared to the stored expectation. The saved run contains a full test snapshot, fixture data/hash, source revision/file hashes, specification hash, request, raw and parsed response, assertion observations and duration. Diagnoses are separate append-only records. A linked retest must use the same revision.

The UI selects the fixed v1 requirement set and accepts additional live-generation focus. It does not pretend to support arbitrary specification authoring. Change SPEC.md deliberately, restart, regenerate and re-review; prior-spec revisions are blocked.

## Decision 1 — Structured data, never generated executable code

Implemented in schema.py and runner.py. Only two paths and GET/POST are allowed; the model cannot choose hosts, commands, scripts or assertion operators. Exact response equality keeps interpretation visible and deterministic. Alternative: generate Python tests and execute them in a sandbox. That offers more expressive tests but introduces sandbox operation, dependency and code-review costs. The prototype sacrifices arbitrary workflows and richer assertion predicates for a small inspectable boundary.

Generation requests use JSON mode followed by strict local validation, allowing intentionally malformed checkout request bodies as negative cases. JSON mode does not guarantee schema compliance or business correctness. Strict provider-side JSON Schema could improve shape reliability; a future design should maintain one generated shared schema rather than two drifting contracts. Current malformed batches fail closed, and every accepted proposal still starts pending.

## Decision 2 — One local process, SQLite revision/event history

Implemented in server.py, storage.py and runner.py. A threaded development server serves UI, API and the local checkout target, while real execution uses loopback HTTP. SQLite retains explicit revisions/events rather than updating test definitions or run verdicts in place. Alternative: separate backend, database and target services. Separation better approximates deployment and isolation, but adds setup and network failure modes beyond this scope. Consequence: the environment demonstration must intentionally direct the internal runner to a reserved non-listening local port. The browser cannot choose a target URL.

No authentication, production HTTP hosting, process isolation or tamper-proof audit is claimed. Someone with database access can alter SQLite. The app preserves history through its API; it is not a compliance ledger. Multiple independent server processes writing one database are unsupported. Review/run actions are serialized in one app process.

## Real design iteration

Initial implementation at commit 53704f1 rendered the entire state as raw JSON. Inspecting its code and report format showed the reviewer had to locate expectations and actuals inside nested records; there was no actionable review path. Commit 863ab80 replaced it with the numbered requirements/review/evidence workflow, explicit source labels, revision controls, and side-by-side expected/actual assertions. The later edit-preservation change keeps a draft if a validation error occurs. These are assistant-led design judgments, not user research. Browser rendering and keyboard interaction remain unverified because no usable local browser binary was available and the cloud browser could not reach loopback. No screenshot is fabricated.

## AI assistance and reused components

See ASSISTANCE.md for consequential accepted/corrected/rejected suggestions and ownership. No existing repository, template, UI kit or business implementation was copied. Runtime components reused as-is: CPython standard library (HTTP, JSON, SQLite bindings, hashing, TLS, unittest) and browser-native HTML/CSS/JS. Git is a development/reproduction tool. No third-party source was modified. The application code and prepared examples were newly assistant-authored from the owner's brief; the reference expectations were manually specified by the assistant from SPEC.md, not produced by quote(). Independence here means independence from the implementation, not a second independent human author.

Sources: https://docs.python.org/3.12/library/ and https://git-scm.com/docs and the official OpenAI JSON output guide at https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses (checked during implementation). Provider wire behavior, account/model access and actual usage remain unverified live. No credentials are included in evidence; prompts contain only the fictional specification and user-entered focus. Do not enter confidential assessment text or secrets into scenario focus.

## Failure interpretation

- `passed`: every exact deterministic assertion matched for this attempt.
- `failed_assertion`: a mismatch requiring investigation; not automatically a product defect.
- `invalid_test`: invalid contract, test hash or specification mismatch.
- `execution_error`: network, invalid response or target source-identity problem; not a product verdict.
- `not_run`: no current approval (including superseded revision).

A successful retry creates another record. It never removes the earlier observation. Different pass/fail observations for matching revision, specification, fixture and source hashes trigger an investigation flag. The flag was tested with an explicitly simulated outcome in a unit test, not an observed unstable service. Matching hashes are a useful proxy, not proof that the environment is identical.

## Evaluation limits and future impact study

The small sample includes 15 reference scenarios and four prepared demonstration proposals. These share a specification and some input cases, so they are not an unbiased estimate of AI capability. The one deliberately seeded defect is detected. This does not establish detection of unknown defects, complete coverage, generalization, or time saved. No live generation quality or latency claim is made. No held-out generator evaluation has occurred.

A follow-up should freeze prompts, reserve new boundary variations, and have engineers independently adjudicate expectations before execution. Compare manual and AI-assisted drafting in counterbalanced tasks; measure total time including review/repair, incorrect approvals, scenario completeness, and defects found, with sample size and uncertainty reported. Do not optimize merely for more generated cases.

## Known limits

Provider calls have a 20-second socket timeout, bounded response size and zero automatic retries; this is an inactivity timeout, not a hard end-to-end wall-clock budget. One manual retry creates a linked generation attempt. There is no rate limiter, background job queue, cancellation, streaming, or automatic schema repair. A model refusal is retained as a failed generation without imported proposals. The 64 KiB API body limit and 256 KiB provider response limit bound payloads, not all computational resource usage. The app is a trusted local prototype, not a hostile-input service.

JSON proposal editing is intentionally technical. A schema-derived form, external service isolation, broader assertion types and richer test-suite grouping would be sensible next changes only after live generation and user review establish value.
