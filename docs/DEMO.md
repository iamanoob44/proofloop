# Demonstration and defense

This is a proposed 7–10 minute demonstration, not a prescribed duration. It is not yet rehearsed with the owner. No recording exists yet.

## Current preparation status — 31 October 2026

Live generation is now evidenced in [the saved original history](../evidence/live-replay-2026-10-31/input-history.json): three proposals, one owner-approved boundary revision and one passing original execution. The generated boundary revision subsequently detected the disclosed defect and passed unchanged after source repair. All three cases subsequently received requirement-grounded delegated-assistant reviews and passed. See the [complete suite](../evidence/generated-suite-2026-10-31/result.json). These reviews do not claim independent human sign-off. The owner accepted R1–R6 on 31 October; the historical SPEC.md heading is retained to avoid altering the saved model-input snapshot.

For step 4 below, demonstrate the actual generated case with:

```bash
python scripts/replay_generated.py --history evidence/live-replay-2026-10-31/input-history.json --revision 1ebc9242-5540-48c3-88f1-7778be9ead69 --pause
```

This performs new local HTTP executions of a saved live-generated proposal. It makes no new provider call. Its `input-history.json` contains the original generation and review, while `before.json`, `after.json`, `regression.json` and `history.json` preserve replay evidence. Use the printed `data/live-replay-.../demo.sqlite` with `python -m proofloop serve --db PATH` to inspect the result. The original `reproduce_defect.py` sequence remains useful, but is reference-case evidence and must be labelled that way.

Assistant browser checks now cover prepared-source labelling, pending/rejected execution gates, missing review fields, malformed JSON and draft retention, approval/execution, edit-to-pending, linked retest comparison, separate diagnosis, JSON download, missing-credential failure and a linked manual retry, persistence, and 800/1366-pixel layout checks. See [verification details](../evidence/browser-verification-2026-10-31/verification.json) for the scope and remaining checks. This does not substitute for the owner's recorded rehearsal or a successful live recovery after failure.

## Ready-to-use saved demonstration

The prepared local database is `data/presentation-demo-20261031.sqlite`, served on port 8768. A fresh clone can reproduce it with `python scripts/prepare_demo.py --db data/presentation.sqlite`, then `python -m proofloop serve --db data/presentation.sqlite --port 8768`.

Show the saved generation, its three proposals and review identities. Explain the six-PIN arithmetic and duplicate rejection. In the execution table select **9ab5aa9e** to show the generated boundary case's failed original attempt and passing retest. Expand the original **a0ab2332** to inspect its separate product-defect diagnosis. These are saved real executions, not a new API generation. Use the complete-suite replay command in README.md with `--pause` when demonstrating a new source repair live.

Suggested explanation: “The model proposes structured test data from the business specification. Review and execution are separate. This boundary case expects free shipping at exactly 5000 cents. The disclosed seeded implementation used a strict greater-than comparison, so it charged 500 cents. We changed only that source operator and reran the identical revision. The normal and duplicate-input tests passed before and after; only the boundary test detected this particular seed. The later reviews were delegated to the assistant and labelled accordingly.”

The owner must record their own actual walkthrough and check playback. Screen recording and Lark account control are not available through the connected automation tools in this session. The current saved evidence is not a substitute for a recording.

## Seeded defect disclosure and model input

The initial teaching implementation deliberately misreads R5 as `net > 5000`. This is a disclosed seeded defect, not a discovered real-world defect. Repair the source operator; do not edit the example or expectation.

The current checkout implementation uses the correct inclusive comparison, `net >= 5000`. The reproduction script injects the strict comparison into an isolated clone for the demonstration, then repairs it while retaining the same test revision and expectations.

The defect disclosure is kept here, outside the model-facing business specification, so generation is not given the exact implementation mistake. The live provider request contains generation instructions, SPEC.md and scenario focus; it does not include implementation source or this demonstration document. Keep scenario guidance business-focused. SPEC.md still includes worked arithmetic examples, so this is specification-guided generation, not a blind or held-out benchmark.

Moving the disclosure changes the specification hash without changing the v1 business rules, prices, thresholds or examples. Restart the application, generate or load fresh proposals, and review them again before execution. Preserve existing evidence as records of the previous specification snapshot; do not relabel it as evidence from the revised model input.

## Suggested sequence (about 9 minutes)

1. **0:00–0:45 — Problem and boundary.** Engineers need regression cases but must not trust plausible AI expectations without review. Show the fictional spec and limited scope.
2. **0:45–2:00 — Proposals.** Select Live and generate only after credentials/model access have been verified. Show saved prompt, output and model. If live is unavailable, explicitly switch to prepared offline examples and say no live generation is being shown.
3. **2:00–3:15 — Review.** Explain two TEEs: 2 × 2500 = 5000 cents. R5 is inclusive. Show the exact expectation, identity and reviewer reason. Approve, edit to create a new pending revision, and reapprove only after checking the change.
4. **3:15–5:30 — Defect and repair.** Run `python scripts/reproduce_defect.py --pause`. Explain the disclosed source mutation, the failed assertion and the responsible shipping line. Press Enter to apply the one-operator source repair. Show the same revision passes and all 15 reference scenarios pass. The script performs actual HTTP calls; it is not replayed output.
5. **5:30–6:15 — Preserved evidence.** Stop the normal server and start it on the replay database path printed by the command. Select original failure and linked retest. Show unchanged expected values and different source hashes.
6. **6:15–7:15 — Incorrect test.** Load the constructed incorrect example. R4 makes net 4500; R5 requires shipping 500. Reject, correct shipping/total and rationale, save a new revision, reapprove and execute. Explain that the example was deliberately authored, not a genuine model mistake.
7. **7:15–9:00 — Architecture and limits.** Explain structured data versus executable tests, one app plus SQLite, human review versus deterministic assertions, exact personal contribution and what remains unverified. Optionally show the saved environment failure and recovery from the HTTP workflow evidence.

## Browser verification and recording checklist (complete remaining items on the presentation laptop)

1. Start with a new database. Open http://127.0.0.1:8765 in the presentation browser. Check the page at laptop width and 800px width; no overlap or clipped controls.
2. Tab through proposal source, generation, reviewer, reason, editor, save, approve, reject, execute and retest. Confirm visible focus and accessible names. Try empty review fields and malformed JSON; confirm clear errors and that drafts remain.
3. Load offline proposals, review/approve/execute one, edit it, confirm execution is blocked until the new revision is approved, and verify the older run retains its original expectation. Reject a proposal and confirm it cannot execute.
4. Inspect original and retest records; download JSON and compare IDs. Restart on the same database and confirm history persists.
5. Test missing provider credentials explicitly. Configure credentials outside the recording, restart, and perform one successful live generation before claiming it works. Capture provider model, latency, usage and validation count from the saved attempt.
6. Start a screen recording with the laptop's built-in recorder or an already installed trusted recorder. Record the browser and terminal core flow, including source fix and unchanged-revision retest. Keep credentials, confidential prompts, notifications and unrelated tabs out of view.
7. Stop recording, play it back, and verify readable expectations, actuals and IDs. Label playback as recorded execution; distinguish offline fixtures from live generation. Save an ordinary video file. Recording remains outstanding until this actually happens.

## Technical questions and concise answers

| Question | Answer to defend |
|---|---|
| Why AI here? | It suggests scenario variations from prose. One saved generation produced three schema-valid proposals and one reviewed case detected the disclosed seed; time savings and general model quality are unmeasured. |
| Where do expected values come from? | The independent specification and explicit arithmetic; never the checkout function being tested. Human review adjudicates the business meaning. |
| What if the model is wrong? | Validation rejects malformed structure; review must catch plausible but wrong expectations. Editing creates a new unapproved revision. |
| Is every red result a product defect? | No. Compare the request, fixture, expected value and actual response with the specification. Record a separate diagnosis; environment failures have their own outcome. |
| Why structured tests? | They expose inputs and assertions without allowing arbitrary model-generated execution. The cost is a smaller supported operation set. |
| How do retries preserve truth? | Every attempt is append-only and links to its parent. Same-revision retests cannot replace expectations or erase earlier failures. |
| What is the fixture preparation? | The immutable catalog-v1 is embedded in the local target and copied/hashed into evidence. Quotes do not decrement inventory; every request starts with the same catalog. |
| What did you personally decide? | The owner supplied direction and constraints, accepted R1–R6, ran Windows checks and guided reproduction, and reviewed/executed one generated boundary case. Explain only work actually done; assistant implementation and replay work remain disclosed. |
| Why this stack? | Standard-library Python plus SQLite avoids install complexity. One process is easy to inspect; it provides less deployment realism and isolation. |
| What changes at scale? | Isolate workers and targets, add authentication, transactional job states, cancellation, explicit fixture lifecycle, stronger schema tooling and tamper-resistant evidence retention after validating the need. |
| What is verified? | Real HTTP assertions, reference and generated-case source repair/retest, review gates, history, selected browser checks, a saved live generation and owner rule acceptance. Full owner rehearsal/recording, independent human review of delegated cases and productivity measurement remain outstanding. |

## Explain-back prompts for the owner

Before presenting, explain in your own words:

- Why do two TEEs pay shipping with SAVE10 but not without it?
- What exact evidence lets you call the seeded mismatch a product defect rather than a bad test?
- Why is the original run still useful after a successful retry?
- Which decisions came from your brief, which came from assistant suggestions, and which have you personally checked or changed?

Do not memorize an answer you cannot trace to the code and saved evidence.
