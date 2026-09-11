# Graph–Field Real Outcome Intake v0.2

Status: **experimental / observed / non-authorizing**

## Purpose

Calibration needs a stage before comparison: a selected transition may have a real, independently verified outcome while no comparable baseline exists yet.

That state must be preserved instead of forcing a baseline or inventing normalized utility after seeing the result.

```text
pre-action snapshot
→ real observed outcome
→ RECORDED_UNPAIRED
→ baseline + utility evidence still required
→ only then calibration-eligible
```

## First real outcome

The first recorded outcome is the P2-1 trust-spine cost/latency measurement selected by the frozen GFD orientation snapshot.

Pre-action selection:

- node: `p2-1-trust-spine-cost-latency`
- field score: `0.800588`
- frozen components: divergence `0.90`, uncertainty `0.65`, blast radius `1.00`, freshness gap `0.40`, open pressure `0.70`, opportunity `1.00`, blockedness `0.05`.

Observed ContractGraph-QA evidence:

- P2-1 draft PR `#63`;
- measured SYSTEM-007 subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329`;
- P2-1 verifier subject `447098344c71dd1e9dd11a69ef7767ddbe106ca0`;
- source run `31879737027`;
- verification run `31883970399` — SUCCESS;
- source job elapsed `45 s`;
- substantive window `35 s`;
- dominant visible measurement group `liminaldb`, `23 s`;
- source evidence artifact `28,222 bytes`;
- provider monetary cost `NOT_MEASURED`.

The result is useful because it produced a discriminating engineering observation: in this run, the durable LiminalDB interval dominates visible substantive latency. That is an observed routing outcome, not proof that the original GFD route was superior to a simpler baseline.

## Calibration gate

The first real record deliberately remains:

```text
utility_annotation_status = UNSCORED
baseline_status = MISSING
eligibility = BASELINE_REQUIRED
weight_update_allowed = false
```

The existing calibration formula is unchanged. It still requires an evidence-backed selected utility **and** an observed simpler baseline under the same frozen utility definition.

A missing baseline is not treated as utility `0`, and the selected outcome cannot be reused as its own baseline.

## Why utility remains unscored

Raw measurements such as `45 seconds`, `23 seconds`, and `28,222 bytes` do not automatically map to the normalized utility dimensions:

- useful finding;
- information gain;
- blocked-work avoidance;
- stale-evidence catch;
- downstream rework avoidance.

Assigning those scores only after seeing the result would introduce hindsight into the calibration loop. A comparison rubric or paired baseline must be fixed before the observation becomes calibration-eligible.

## Authority boundary

Outcome intake emits:

```text
mode = ADVISORY_ONLY
authority_granted = false
weight_update_allowed = false
```

It grants no merge, deployment, execution, mutation, payment, security, production persistence, or external-effect authority.

Canonical invariant remains:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**
