# ProofLoop

**AI proposes tests. People review their business meaning. Deterministic execution records the evidence.**

ProofLoop helps engineers maintaining a fictional creator-commerce checkout quote service explore the gap between writing requirements and trusting generated regression tests. Scope: one local target, one immutable catalog, structured JSON proposals, revision-based review, one model provider adapter, SQLite history, and inspectable reports. No payments, authentication, tenancy, production commerce integrations or browser agents.

**Status (31 October 2026, Singapore):** 21 implementation tests pass on Windows. Saved live generation contains three proposals; Jake approved and executed the shipping-boundary case. That same generated revision detects the seeded defect and passes unchanged after repair; reference regression passes 15/15. Browser workflow checks have been performed with explicitly labelled assistant reviews. The owner accepted R1–R6 on 31 October. Review of the other two live proposals, full presentation rehearsal, recording and final publication remain outstanding.

## Start locally

Prerequisites: Python 3.12 (Windows 3.12.10 and Linux 3.12.14 verified), Git for source identity and the isolated repair demo, and a modern browser. No pip or npm runtime packages; `requirements.lock` records that explicitly. macOS has not been rehearsed.

```bash
cd proofloop
python -m proofloop serve
```

Open **http://127.0.0.1:8765**. Use the exact numeric loopback address; `localhost` is intentionally rejected by the Host guard. The server stays local. Press Ctrl+C to stop.

On the owner's Windows laptop, open PowerShell in `proofloop-restored` and use the verified interpreter explicitly:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m proofloop serve
```

Use that same interpreter in place of `python` in the commands below. Another machine can use its own Python 3.12 installation.

1. Read the proposed specification, then select **Offline · prepared examples** and load proposals.
2. Inspect a proposal's inputs, exact expectation, requirement references and rationale.
3. Enter your reviewer name and business reason. Edit if needed, save a new revision, then approve or reject.
4. Execute an approved revision. Inspect expected versus actual and the full saved record.
5. Retest the exact revision or record a separate diagnosis. Download the evidence JSON.

Offline fixtures are prepared assistant-authored examples, **not** captured successful API responses. The constructed incorrect-test mode is visibly labeled as deliberate, not an observed model error. CLI verification reviews are labeled assistant validation and are not human sign-off.

## Live generation

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in your shell or local secret manager **before starting the server**. Use a model enabled in your account that supports Responses API JSON output. `.env.example` lists the names; the app does not automatically read `.env`. Do not paste secrets into the UI or commit them. Your ChatGPT sign-in does not configure this application's provider credential.

Choose **Live · OpenAI provider**, enter a scenario focus, and generate. Generation instructions, the fictional specification and focus are sent to `https://api.openai.com/v1/responses`; implementation source and defect disclosure are excluded. Provider output must pass local validation and human review. An error is saved as a generation attempt; there is no silent fallback or automatic retry. A manual retry preserves and links the first attempt. Live calls may incur account charges. The saved 30 October generation reports `gpt-6-luna`, three validated proposals and 1596 total tokens; availability on another account still needs checking. See the original record in [input-history.json](evidence/live-replay-2026-10-31/input-history.json). No new provider call was made during the 31 October audit.

## Verify and reproduce

```bash
python -m unittest discover -s tests -v
python -m proofloop reference --db data/reference.sqlite --output data/reference.json
python scripts/verify_workflow.py --db data/workflow-new.sqlite --output data/workflow-new.json
python scripts/reproduce_defect.py
```

The last command creates an isolated temporary clone, injects the disclosed `>` shipping defect, runs the reference suite, repairs the source to `>=`, retests the **same approved revision**, and reruns the regression suite. It prints a unique evidence directory. The current checkout and older reports are not overwritten. Add `--pause` for an explanation pause before the source repair. All code changes must be committed first because the replay clones the committed version.

To inspect replay records in the UI, restart the server with the printed database path:

```bash
python -m proofloop serve --db data/reproduction-REPLACE_WITH_PRINTED_ID/demo.sqlite
```

Use the actual directory printed by the script. Its original failure and same-revision retest appear in the evidence table. Current checkout code is fixed. Old source versions stay visible in each run's source metadata.

### Replay the actual generated test

The reference command above uses prepared reference cases. This separate command replays the saved, approved live-generated revision and retains its generation, review, revision and test identities:

```bash
python scripts/replay_generated.py --history evidence/live-replay-2026-10-31/input-history.json --revision 1ebc9242-5540-48c3-88f1-7778be9ead69
```

It needs no API key or pre-existing local database. The helper copies exported history into a new database, clones committed target code, injects the disclosed defect, executes the selected revision, repairs the source, retests unchanged expectations, and runs the reference regression suite. It refuses pending/rejected/superseded revisions and specification mismatches. It reports missed detections as such. Repeat `--revision` for multiple approved tests; use `--db PATH` instead of `--history PATH` to take a read-only snapshot of an existing database. `--pause` pauses before repair. It never approves proposals or replaces them with reference cases. `input-history.json` preserves the original records; `history.json` adds the replay and regression runs. Local SQLite files remain ignored.

## Reset and recover without deleting history

Use a new database filename, e.g. `python -m proofloop serve --db data/fresh-session.sqlite`. Retain the old database and exports. To return, stop and restart with the previous `--db` path. If port 8765 is busy, use `--port 8766` and open the corresponding numeric loopback address. Restart after a source/spec change; the app refuses API mutations against changed on-disk source. After a spec change, generate and review new proposals.

Export all persisted records:

```bash
python -m proofloop export --db data/proofloop.sqlite --output data/export.json
```

## Evidence and documentation

| Evidence | What it establishes |
|---|---|
| `evidence/01-seeded-reference.json` | 14 passing scenarios and 1 observed boundary mismatch before repair |
| `evidence/02-fixed-same-revision.json` | Same revision and expectation hash passes after source fix |
| `evidence/03-fixed-reference.json` | 15/15 fixed reference scenarios pass |
| `evidence/04-workflow.json` | Actual HTTP review/edit/run workflow; constructed wrong-test correction; connection failure/recovery |
| `evidence/validation.txt` | Implementation test results and JS syntax check |
| `evidence/clean-rehearsal.json` | Isolated clean-checkout reproduction results |
| [Windows reproduction](evidence/windows-reproduction-2026-10-29/result.json) | Owner's earlier reference-case reproduction and unchanged-revision retest |
| [Live-generated replay](evidence/live-replay-2026-10-31/result.json) | Actual generated boundary revision fails against the seed and passes unchanged after repair; 15/15 reference regression |
| [Browser verification](evidence/browser-verification-2026-10-31/verification.json) | Assistant-operated browser checks and explicitly listed remaining checks |
| [Fresh-clone development check](evidence/final-development-check-2026-10-31.json) | Committed version `0486366` passes 21 tests, generated replay, 15/15 regression and the HTTP failure/recovery workflow without a pre-existing database |
| `docs/ENGINEERING.md` | Modules, two decisions, design iteration, failure semantics and limitations |
| `docs/ASSISTANCE.md` | Actual assistance, corrections, reuse and contribution boundaries |
| `docs/DEMO.md` | Proposed demo and technical questions |

These small samples do not establish productivity gains, general model accuracy or complete requirements coverage. The reference expectations were specified from the independent business specification, not calculated by the checkout code. The same assistant authored both; no independent human adjudication is claimed.

## Source history and distribution

Meaningful commits preserve the specification, seeded implementation, observed failure, repair, review workflow and hardening. No commits were backdated. The repository is published at [iamanoob44/proofloop](https://github.com/iamanoob44/proofloop). Early commits retain the neutral development identity and assistance disclosures; later owner commits use the configured owner identity. Confidential assessment materials are outside this repository and its history.

A distributed archive includes `proofloop-history.bundle` and `RELEASE.json`. To restore the real local history, run `git clone proofloop-history.bundle proofloop-restored`; then follow the commands above. The manifest identifies the packaged source SHA. A final submitted SHA must be recorded after the owner accepts the result and publishes the dedicated repository.

The original bundle and sibling `proofloop` folder are historical baseline artifacts. Continue from the current Git repository, not that older copy.

## Remaining completion steps

1. In the original live database, personally review the normal six-PIN case (3006 subtotal, 300 discount, 500 shipping, 3206 total) and duplicate-SKU case (400 INVALID_REQUEST). Approve or correct them with meaningful reasons, then execute. Strengthen the boundary review reason beyond the original “Testing” note by appending a new review; preserve the old event.
2. Rehearse the browser flow and failure recovery on the presentation laptop. The saved provider-success and missing-credential failures are separate sessions; successful live recovery from a failed attempt has not been demonstrated.
3. Record and play back an actual walkthrough: generation provenance, review, assertions, seeded source repair, unchanged-revision retest, and an incorrect-test/environment example. Check Lark sign-in and screen sharing separately.
4. A fresh local clone of `0486366` passed the development checks above; repeat after any further code changes. Inspect and push the reviewed local commits, record the final submitted SHA (and optional tag), and confirm reviewer access. Final-code deadline from the handover: **2 November 2026, 23:59 Singapore time**; on-site demonstration: **3 November**, time/venue still to be confirmed.
