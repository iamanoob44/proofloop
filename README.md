# ProofLoop

**AI proposes tests. People review their business meaning. Deterministic execution records the evidence.**

ProofLoop helps engineers maintaining a fictional creator-commerce checkout quote service explore the gap between writing requirements and trusting generated regression tests. Scope: one local target, one immutable catalog, structured JSON proposals, revision-based review, one model provider adapter, SQLite history, and inspectable reports. No payments, authentication, tenancy, production commerce integrations or browser agents.

**Status:** core checkout, runner, repair and HTTP workflow verified. UI implemented but browser verification outstanding. Live provider success unverified: no credential was available. Business rules in [SPEC.md](SPEC.md) await owner acceptance. This is a working prototype, not a completed submission.

## Start locally

Prerequisites: Python 3.12 (verified 3.12.14), Git for source identity and the isolated repair demo, and a modern browser. No pip or npm runtime packages; `requirements.lock` records that explicitly. Linux verified; Windows/macOS not yet rehearsed.

```bash
cd proofloop
python -m proofloop serve
```

Open **http://127.0.0.1:8765**. Use the exact numeric loopback address; `localhost` is intentionally rejected by the Host guard. The server stays local. Press Ctrl+C to stop.

1. Read the proposed specification, then select **Offline · prepared examples** and load proposals.
2. Inspect a proposal's inputs, exact expectation, requirement references and rationale.
3. Enter your reviewer name and business reason. Edit if needed, save a new revision, then approve or reject.
4. Execute an approved revision. Inspect expected versus actual and the full saved record.
5. Retest the exact revision or record a separate diagnosis. Download the evidence JSON.

Offline fixtures are prepared assistant-authored examples, **not** captured successful API responses. The constructed incorrect-test mode is visibly labeled as deliberate, not an observed model error. CLI verification reviews are labeled assistant validation and are not human sign-off.

## Live generation

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in your shell or local secret manager **before starting the server**. Use a model enabled in your account that supports Responses API JSON output. `.env.example` lists the names; the app does not automatically read `.env`. Do not paste secrets into the UI or commit them. Your ChatGPT sign-in does not configure this application's provider credential.

Choose **Live · OpenAI provider**, enter a scenario focus, and generate. Only the fictional specification and focus are sent to `https://api.openai.com/v1/responses`. Provider output must pass local validation and human review. An error is saved as a generation attempt; there is no silent fallback or automatic retry. A manual retry preserves and links the first attempt. Live calls may incur account charges. Successful live generation, available model selection and actual token usage still need verification on your machine.

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
| `docs/ENGINEERING.md` | Modules, two decisions, design iteration, failure semantics and limitations |
| `docs/ASSISTANCE.md` | Actual assistance, corrections, reuse and contribution boundaries |
| `docs/DEMO.md` | Proposed demo and technical questions |

These small samples do not establish productivity gains, general model accuracy or complete requirements coverage. The reference expectations were specified from the independent business specification, not calculated by the checkout code. The same assistant authored both; no independent human adjudication is claimed.

## Source history and distribution

Meaningful local commits preserve the specification, seeded implementation, observed failure, repair, review workflow and hardening. No commits were backdated. No remote repository has been created or pushed. Repository author identity is a neutral local development identity, not a claim about the owner's personal authorship. Confidential assessment materials are outside this repository and its history.

A distributed archive includes `proofloop-history.bundle` and `RELEASE.json`. To restore the real local history, run `git clone proofloop-history.bundle proofloop-restored`; then follow the commands above. The manifest identifies the packaged source SHA. A final submitted SHA must be recorded after the owner accepts the result and publishes the dedicated repository.
