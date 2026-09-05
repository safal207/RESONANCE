# Payment recovery demo publication

Route: `/RESONANCE/payment-recovery-demo.html`.

This adds one isolated page and two CSS files. Existing home pages, article content, feeds, analytics configuration, domain/DNS, publication scripts and deployment workflow are unchanged. The existing Pages pipeline builds and deploys the page after publication.

## Presentation

Six native HTML accordion scenarios, English/Russian CSS language switch, event-sequence highlight animation, visible animation-off checkbox, reduced-motion support, and a native read-only post text field. No custom JavaScript is shipped or required for the demo controls. Protocol event labels stay literal across languages.

The animation highlights an already recorded trace. Results remain explicitly labeled recorded; no fake browser-side Python execution, live payment agent, partial-trace verdict or provider enforcement is implied.

## Evidence

ContractGraph-QA draft PR: https://github.com/safal207/ContractGraph-QA/pull/159
Evidence commit: `f842d54679ac0826e2bc635dcd10a321f6d03631`.
Evaluator baseline: `776a43cd554fd25c9f9a4a258c7818719f81cac3`.
Successful exact-head offline evidence run: https://github.com/safal207/ContractGraph-QA/actions/runs/33997952511

The four original expected verdicts match (two PASS and two FAIL); 47 baseline tests include 46 passes and one expected failure; the isolated candidate passes 50 tests. These are bounded tests, not a safety rate. The candidate is not applied or merged into ContractGraph-QA.

## Verification boundary

The HTML/CSS prototype passed 60 Chromium combinations (six scenarios, two languages, five viewport widths) plus animation-off and reduced-motion checks, using `set_content` with the corresponding CSS. That is not a hosted-delivery or Safari/Firefox result. The uploaded variant keeps the protocol labels literal; its exact source artifact must be checked separately before publication. `scripts/verify-payment-recovery-demo.py` checks the six static verdict/event/flag/hash projections and explicit boundary labels. It does not replace browser QA.

Do not claim production safety, a real duplicate charge, independent audit, complete/authentic external evidence, a shipped fix, model superiority or OpenAI endorsement. Unknown-stop is native FAIL with noncritical APR-009, not a native HOLD.

The ready-to-copy English post is included in the page. Website publication does not authorize posting it to X; no social post was sent by this change.
