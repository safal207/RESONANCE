---
name: graph-field-orientation
description: Route and apply Graph–Field operators for orientation, recovery, and outcome calibration without granting execution authority.
---

# Graph–Field Orientation

Use this skill when an agent knows a bounded system/work graph but must decide either **where to look/work next**, **where to re-enter after context loss**, or **how to evaluate an operator after an observed outcome**.

The skill is the entrypoint for the Graph–Field Operator Family defined in `protocols/GRAPH_FIELD_OPERATOR_FAMILY_V0_1.md`, with outcome calibration defined in `protocols/GRAPH_FIELD_CALIBRATION_V0_2.md`.

## Choose the operator first

### OrientationOperator

Use when the question is:

> Where should attention or work go next?

Inputs are bounded work nodes/transitions with evidence for:

- divergence;
- uncertainty;
- blast radius;
- freshness gap;
- open pressure;
- opportunity;
- blockedness.

Executable reference: `score_graph_field.py`.

### RecoveryOperator

Use when the question is:

> Where should the agent re-enter after interruption or context loss?

Do **not** implement a second recovery scorer here. Consume the existing CML Focus–Field Recovery result when available. CML owns recovery-specific semantics such as concept/value/goal/causal fit, current-state applicability and information quality.

Normalize a serialized CML Focus–Field v0.2 decision through `operator_family.py` only after preserving its `trusted_continuation` state.

`reanchored_exploratory` is useful context, not a trusted continuation.

### CalibrationLoop

Use only after an operator selection has led to an independently observable outcome.

The calibration question is:

> Did this selected route create more evidence-backed utility than a declared simpler baseline, and does that justify a bounded weight proposal for later testing?

Calibration requirements:

- preserve the original pre-action field snapshot;
- freeze the utility definition before interpreting the outcome;
- require outcome evidence and baseline evidence;
- never treat `field_score` as a probability of success;
- produce a proposal only; never mutate canonical weights automatically;
- evaluate any proposal on held-out observations before considering a configuration change.

Executable reference: `calibrate_graph_field.py`.

## Shared workflow

1. **State intent.** What system outcome are we trying to improve, recover or understand?
2. **Choose operator.** Orientation for next-work routing; Recovery for context re-entry.
3. **Bound the graph.** Prefer explicit nodes/transitions over repository-level blobs.
4. **Collect current evidence.** Exact heads, open/closed state, verification results, blockers and authority boundaries.
5. **Project the domain field.** Use the selected operator's own field channels; do not force one universal coefficient vector across domains.
6. **Rank/select.** Preserve decomposition and source semantics.
7. **Separate selection from trust/actionability.** A selected point may still be blocked, exploratory, stale or untrusted.
8. **Normalize if crossing repositories.** Use the common advisory envelope; do not duplicate CML verification logic in RESONANCE.
9. **Causal zoom.** On an actionable candidate, identify the first meaningful divergence and smallest discriminating next test.
10. **Hand off.** Execution, merge, deployment, external effects, payments and security actions go through native authority-aware workflows.
11. **Observe.** Record what happened separately from the pre-action field snapshot.
12. **Calibrate only with evidence.** Compare observed utility with a frozen simpler baseline and emit a bounded proposal.
13. **Recompute later.** A reviewed future configuration may change later fields; it never rewrites the historical field score.

## Orientation output

Return:

- top actionable hotspot;
- highest raw-tension hotspot if different;
- top 3 field ranking;
- important blocked hotspots;
- evidence gaps;
- one next safe transition;
- explicit authority boundary.

## Recovery output

Preserve at minimum:

- selected anchor or `None`;
- recovery state;
- score;
- `trusted_continuation`;
- rewind steps saved when available;
- source revision/contract;
- explicit authority boundary.

A trusted recovery candidate is only ready for a **separate authority check**. It is not execution authority.

## Calibration output

Preserve at minimum:

- observation count;
- observed utility and baseline utility per observation;
- advantage per observation;
- current weights;
- proposed weights and deltas;
- coarse sample-size confidence;
- explicit `apply_recommended=false`;
- explicit authority boundary;
- held-out evaluation as the required next check.

Always preserve:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

## Human / SELF rule

If a human or SELF node is present, do not score intrinsic worth, lovability or human value. Observable outcomes may change strategy and evidence only.

Operational invariant:

> **Failure updates the model of action, not the worth of the actor.**

Values may orient or constrain selection. They must not become a numerical score of human dignity.

## Anti-patterns

Do not:

- create a new scorer when an existing operator already owns the domain semantics;
- collapse orientation and recovery coefficients into one universal formula;
- rank repositories only because they are busy;
- equate repeated attention with truth;
- let a high field score grant authority;
- erase a blocked hotspot from the report;
- promote exploratory recovery into trusted continuation;
- treat `HOLD`/`defocus` as errors that must be forced to acceptance;
- infer calibration success from attention volume;
- use `field_score` as a probability without a separate calibration model;
- retroactively rewrite a pre-action score after seeing the outcome;
- auto-apply calibration weights;
- optimize Presence Space;
- hide heuristic inputs behind false numerical precision;
- keep tuning coefficients until a preferred node wins.

## Executable references

Orientation:

```bash
python3 skills/graph-field-orientation/score_graph_field.py \
  skills/graph-field-orientation/examples/neo-resonance-2026-08-15.json \
  --pretty
```

Calibration control:

```bash
python3 skills/graph-field-orientation/calibrate_graph_field.py \
  skills/graph-field-orientation/examples/synthetic-calibration-v0.2.json \
  --pretty
```

Cross-operator normalization is provided by `operator_family.py` and tested against a serialized CML Focus–Field v0.2 compatibility fixture.

All outputs remain advisory-only.
