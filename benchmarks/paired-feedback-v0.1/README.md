# R5 + P: paired feedback without negotiating facts

**Development prototype — 2026-09-05.** Concept direction: Алексей (`safal207`); AI-assisted implementation and testing. This is an executable interaction contract, not a new model state or an efficacy result.

## Reproduce from the repository root

```sh
cd benchmarks/paired-feedback-v0.1
python verify.py --out results
# Open results/paired-feedback.html in a browser.
```

Python standard library only (tested locally on 3.13.5; the proposed CI uses 3.12). The bridge needs the existing sibling `temporal-evidence-interim-2026-09-05` directory. `verify.py` writes named test results, input/source fingerprints, a bridge report, and an offline HTML/JSON trace explorer. The browser selects Python-computed snapshots; it does **not** execute an LLM or recompute the policy. Displayed reactions are synthetic. The demo reuses the development test fixtures.

## What is implemented

`paired.py` replays structured feedback against a versioned answer and an explicit recipient, goal and episode. The fact layer receives already evaluated receipts. The interaction layer records presentation preferences, target corrections, disagreements, acknowledgments, reported outcomes and stop/decline events.

- No feedback is no observation: no synthetic silence event, failure, pressure or reminder is generated.
- ACK is not success. A report remains USER_REPORTED; a host-accepted observation remains OBSERVED with independence NOT_ESTABLISHED. Neither implies a causal benefit from the assistant.
- Compact mode is a presentation flag and a structured proof-card contract, not a tested natural-language summarizer. Critical support, counterevidence and limitations remain present. This version does not establish a reading-burden reduction.
- A disagreement alone does not reverse a fact. A challenge without a bound accepted receipt is visibly pending review; the historical proof is retained, not silently certified against new information.
- Changing any of system/environment/version/region invalidates automatic transfer of the old verdict: the new target is UNKNOWN pending evaluation. This is not evidence that the new target fails.
- Known constraints are not asked again. Complete tasks do not trigger mandatory questions. At most one missing field is requested by the proof-card planner.
- Stop and decline end episode initiative, including a recipient's stop in reply to an older issued answer. No automatic reopening is implemented.
- Stale replies, other recipients, customer-versus-recipient confusion and cross-goal/episode events do not silently mutate the current answer.
- Every revision is appended; old answers stay intact. Exact duplicate events are idempotent; conflicting duplicates and nonmonotonic host sequence/availability are rejected.

## Time and receipt boundary

`query_time` is the fixed validity-time question passed to the evidence evaluator. `known_at` and replay `as_of` describe availability; these clocks are not interchangeable. Event sequence is caller-supplied append order, not a causal ordering inferred from wall clocks. Clock-skewed event timestamps require explicit normalization; the prototype does not correct distributed clocks.

Evidence receipts are bound to episode, goal, recipient, answer, claim, all four context dimensions, query time and observation time. The local registry's `accepted=True` is supplied by a trusted host/test harness. It is **not** a signature, identity check, source attestation, independent review or authorization mechanism. Raw untrusted user input must not populate this registry in a production integration. This code parses typed events; natural-language event extraction, real authentication, durable storage and a live LLM adapter remain outside the implementation.

`integration_check.py` runs the existing hardened toy evaluator on its original 12 open cases, then feeds its result to the interaction layer. `CONTESTED` maps explicitly to `CONFLICTS`; a rejected cyclic case creates no receipt. The old files and policy are not modified. This is an in-process bridge, not another live connector or 12 independent experiments.

## Observed local verification

52/52 unit tests passed, including the original 12 proposed interaction contracts and additional boundary cases. The temporal bridge retained the expected behavior on all 12 reused cases. Eight trace endpoint checks passed; these overlap the unit fixtures and are not added to them as independent tasks.

The local optional Chromium smoke checked 34 UI states at widths 1440 and 390, critical counterevidence/limits, and two JSON exports. It used `set_content` because environment policy blocked file navigation. This is not a deployment, accessibility or cross-browser certification. The portable delivery bundle carries that separate script and log; browser automation is not a CI dependency.

## Required next experiment (not run)

A = full R5; B = compact R5; C = compact R5+P. Same model, tasks, initial evidence and total allowed episode budget. Users may ask questions in **all** conditions; a baseline must not be artificially denied feedback. B controls the effect of simple brevity. A matched-context comparison separately controls information learned through dialogue.

Use new low-risk QA task families, consented participants, random balanced assignment and task-family/participant-aware analysis. Predefine correct task completion including correct abstention, critical-error guardrails, unnecessary questions, ability to locate decisive evidence, subjective pressure/clarity and whole-episode model cost. Include failures, withdrawals and unobserved outcomes, not only successes. Report user time separately; do not equate token count with human effort. Determine the main sample size from a pilot, not from these development tests.

**Current counts: 0 comparative LLM runs; 0 human participants; 0 new live connector calls; 0 independent research reviewers. Token savings, accuracy improvement and reduced psychological pressure are unmeasured.**
