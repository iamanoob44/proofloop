# Demonstration and defense

This is a proposed 7–10 minute demonstration, not a prescribed duration. It is not yet rehearsed with the owner. No recording exists yet.

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

## Exact browser verification and recording steps (outstanding)

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
| Why AI here? | It can suggest scenario variations from prose. This prototype has not yet measured time savings or live model quality. |
| Where do expected values come from? | The independent specification and explicit arithmetic; never the checkout function being tested. Human review adjudicates the business meaning. |
| What if the model is wrong? | Validation rejects malformed structure; review must catch plausible but wrong expectations. Editing creates a new unapproved revision. |
| Is every red result a product defect? | No. Compare the request, fixture, expected value and actual response with the specification. Record a separate diagnosis; environment failures have their own outcome. |
| Why structured tests? | They expose inputs and assertions without allowing arbitrary model-generated execution. The cost is a smaller supported operation set. |
| How do retries preserve truth? | Every attempt is append-only and links to its parent. Same-revision retests cannot replace expectations or erase earlier failures. |
| What is the fixture preparation? | The immutable catalog-v1 is embedded in the local target and copied/hashed into evidence. Quotes do not decrement inventory; every request starts with the same catalog. |
| What did you personally decide? | The owner supplied product direction and evidence/scope constraints. Proposed rules and assistant implementation still require owner review. Add only decisions actually made, not a memorized fictional contribution story. |
| Why this stack? | Standard-library Python plus SQLite avoids install complexity. One process is easy to inspect; it provides less deployment realism and isolation. |
| What changes at scale? | Isolate workers and targets, add authentication, transactional job states, cancellation, explicit fixture lifecycle, stronger schema tooling and tamper-resistant evidence retention after validating the need. |
| What is verified? | Real HTTP checkout assertions, same-revision source repair/retest, revision review gates, history and error handling. Browser behavior, successful live generation, owner acceptance and real productivity remain unverified. |

## Explain-back prompts for the owner

Before presenting, explain in your own words:

- Why do two TEEs pay shipping with SAVE10 but not without it?
- What exact evidence lets you call the seeded mismatch a product defect rather than a bad test?
- Why is the original run still useful after a successful retry?
- Which decisions came from your brief, which came from assistant suggestions, and which have you personally checked or changed?

Do not memorize an answer you cannot trace to the code and saved evidence.
