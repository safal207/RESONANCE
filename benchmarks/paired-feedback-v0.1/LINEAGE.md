# Presentation-lineage audit and the A/B/C gate


The continuation separates `answer_id` (every issued rendering/review marker) from
`fact_revision` (changed context or an accepted evaluated proof). Presentation-only
changes and pending-review markers retain the factual revision. A delayed evidence
or outcome event may refer to an earlier answer in that revision, but its receipt
must still match that exact earlier answer and all existing scope/time bindings.
A new evaluated proof is a barrier even when its verdict is unchanged; returning
to an earlier context name does not revive older receipts.

Current-answer outcome attribution is unchanged. `related_outcome_observations`
shows earlier-answer records in the same factual revision with the original
`answer_id`; `related_outcome_basis=RECORDED_FOR_EARLIER_ANSWER` does NOT mark the
current answer successful. Different factual revisions remain separate. Initial
state and persisted-history migration are not supported; regenerate with
`initial_state`. The host remains the trusted receipt and state boundary.

Reproduce the before/after audit from a checkout containing the pinned parent:

```sh
cd benchmarks/paired-feedback-v0.1
python verify.py --out results
git show 0d83d3e767756e40b5fceab4fe207a524c152ede:benchmarks/paired-feedback-v0.1/paired.py > /tmp/paired_before.py
python lineage_probe.py --baseline /tmp/paired_before.py --out results
python prepare_abc.py --out results/abc-smoke
```

Open `results/lineage-audit.html`. The audit requires the exact baseline SHA-256.
Observed: all 52 unchanged original tests plus 20 new test methods passed; the
12 original temporal cases and eight old demo endpoints still pass. The new
21 presentation/receipt-binding perturbations passed 6/21 in the pinned baseline
and 21/21 in the candidate. These are overlapping variants of one fixture, NOT
independent tasks or LLM accuracy rates. Short-from-start and later-shortened
answers are separately exercised.

The exported A/B/C packet contains **18 planned two-turn development episodes**
(6 open task families x 3 arms, one repeat), NOT executed model responses.
A is full R5, B is brief R5, C is brief R5+P. All receive identical substantive
feedback and may ask useful questions. Freeze one model, parameters and total
episode budget before execution; keep input, output and any reported reasoning
usage, latency, errors and abandoned runs. Exclude `operator-key.json` and
`assessor-oracle.json` from model inputs. Deliver turn 1 only after turn 0.
This is a matched-feedback smoke test, not a human interaction experiment;
response style can reveal the arm even when labels are withheld. No isolated
model execution adapter or scorer has been run or claimed here.
