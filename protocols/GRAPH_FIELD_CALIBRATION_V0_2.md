# Graph–Field Calibration Loop v0.2

Status: **experimental / advisory / non-authorizing**

## 1. Purpose

Graph–Field Dynamics v0.1 ranks bounded graph locations or transitions. v0.2 adds an outcome-calibration loop without turning one observed result into truth and without allowing the field to rewrite its own authority boundary.

The loop is:

```text
pre-action field snapshot
→ selected candidate
→ separate authority-aware execution path
→ observed outcome
→ evidence-backed utility record
→ compare with a simpler baseline
→ bounded calibration proposal
→ review / later validation
→ future field configuration
```

Canonical invariant remains:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

Calibration never grants merge, deployment, payment, production mutation, security, privilege, or execution authority.

## 2. No retroactive score rewriting

A pre-action field score is an historical observation. Once an action or investigation has started, later outcomes must not rewrite that score.

Store separately:

- `field_snapshot_ref` — what the operator believed before action;
- `observed_outcome` — what happened afterwards;
- `calibration_proposal` — what weights may be worth testing next.

This preserves the difference between prediction and hindsight.

## 3. Field score is not a probability

`field_score` is a routing score, not a calibrated probability that a transition will succeed.

Therefore v0.2 explicitly rejects the shortcut:

```text
prediction_error = observed_success - field_score
```

Instead it compares observed utility of the selected transition with an explicit simpler baseline under the same frozen utility definition.

## 4. Outcome utility

Each observation records normalized `[0,1]` outcome dimensions with evidence references:

| Dimension | Weight |
|---|---:|
| `useful_finding` | 0.30 |
| `information_gain` | 0.25 |
| `blocked_work_avoidance` | 0.15 |
| `stale_evidence_catch` | 0.10 |
| `downstream_rework_avoidance` | 0.20 |

Observed utility:

```text
U = 0.30F + 0.25I + 0.15B + 0.10S + 0.20R
```

The baseline utility must be observed under the same definition. Missing evidence makes the observation ineligible for calibration.

## 5. Advantage signal

For observation `o`:

```text
Adv(o) = U_selected(o) - U_baseline(o)
```

Positive advantage means the selected field route outperformed the declared baseline for that observation. Negative advantage means it underperformed.

No causal claim is made from one observation. Advantage is only a calibration signal.

## 6. Attribution signal

The orientation operator has local components:

```text
divergence
uncertainty
blast_radius
freshness_gap
open_pressure
opportunity
```

For each observation, v0.2 centers component activation around the current weighted mean:

```text
C̄ = Σ w_i C_i
signal_i = Adv × (C_i - C̄)
```

Across a batch:

```text
S_i = mean(signal_i)
raw_i = w_i × (1 + learning_rate × S_i)
proposed_i = raw_i / Σ raw_j
```

The learning rate is bounded to `[0, 0.10]`.

This is deliberately conservative. A component receives relative weight only when it was unusually active in observations where the selected route beat the baseline, and loses relative weight when it was unusually active in observations where the route underperformed.

## 7. Proposal, not mutation

The calibrator always emits:

```text
mode = ADVISORY_ONLY
authority_granted = false
apply_recommended = false
```

It never edits the canonical scorer weights itself.

A later review or experiment may choose to test the proposed weights on held-out observations. Only after out-of-sample comparison should a new weight set become a candidate configuration.

## 8. Minimum evidence discipline

Each calibration observation must include:

- selected node id;
- frozen local components from the pre-action snapshot;
- outcome dimensions;
- baseline utility;
- at least one outcome evidence reference;
- at least one baseline evidence reference.

Synthetic fixtures must identify themselves as synthetic and must never be presented as production evidence.

## 9. Batch confidence labels

v0.2 reports only coarse sample-size posture:

```text
1–4 observations   → INSUFFICIENT
5–19               → NASCENT
20+                → EVALUATE_ON_HOLDOUT
```

Even `EVALUATE_ON_HOLDOUT` is not permission to apply the weights.

## 10. Anti-feedback rule

Invalid:

```text
field selects X
→ X receives more attention
→ attention itself becomes positive outcome evidence
→ X's weights increase
```

Valid:

```text
field selects X
→ independent observable work happens
→ evidence-backed outcome is recorded
→ same utility definition compares X with baseline
→ bounded calibration proposal is produced
```

## 11. Human / SELF boundary

No human worth, lovability, dignity, or intrinsic value may be an outcome dimension or calibration target.

> **Failure updates the model of action, not the worth of the actor.**

## 12. Next falsification stage

The first real use of this loop should follow a measured trust-spine experiment such as P2-1. Freeze the utility definition before seeing the result, retain the original field snapshot, compare with one or more simple routing baselines, then test any proposed weight change on held-out transitions.

If the calibrated proposal does not outperform the current weights out-of-sample, discard the proposal.
