---
name: graph-field-orientation
description: Rank candidate work transitions by Graph–Field Dynamics tension and actionability without granting execution authority.
---

# Graph–Field Orientation

Use this skill when an agent knows the relevant system or work graph but must decide **where to look or work next**.

## Inputs

Require a bounded set of candidate work nodes/transitions. For each candidate, collect evidence for:

- divergence;
- uncertainty;
- blast radius;
- freshness gap;
- open pressure;
- opportunity;
- blockedness.

Do not silently convert missing evidence into certainty. Mark heuristic estimates as heuristic.

## Workflow

1. **State intent.** What system outcome are we trying to improve or understand?
2. **Bound the graph.** Prefer work transitions over repository-level blobs.
3. **Collect current evidence.** Exact heads, open/closed state, verification results, explicit next transitions, blockers and authority boundaries.
4. **Score the local field.** Use the v0.1 formula from `protocols/GRAPH_FIELD_DYNAMICS_V0_1.md`.
5. **Diffuse one hop.** Apply only declared adjacency and the configured bounded diffusion coefficient.
6. **Separate tension from actionability.** A blocked hotspot remains important but should not masquerade as the next executable task.
7. **Rank hotspots.** Return the top candidates with their evidence and the reason each moved up or down.
8. **Causal zoom.** On the highest actionable node, identify the first meaningful divergence and the smallest discriminating next test.
9. **Hand off.** Execution, merge, deployment, external effects and security actions go through their native authority-aware workflow.
10. **Observe and recompute.** Outcomes update evidence; they do not retroactively rewrite the pre-action field score.

## Required output

Return:

- top actionable hotspot;
- highest raw-tension hotspot if different;
- top 3 field ranking;
- important blocked hotspots;
- evidence gaps;
- one next safe transition;
- explicit authority boundary.

Always preserve:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

## Human / SELF rule

If a human or SELF node is present, do not score intrinsic worth, lovability or human value. Observable outcomes may change strategy and evidence only.

Operational invariant:

> **Failure updates the model of action, not the worth of the actor.**

## Anti-patterns

Do not:

- rank repositories only because they are busy;
- equate repeated attention with truth;
- let a high field score grant authority;
- erase a blocked hotspot from the report;
- treat `HOLD` as an error that must be forced to `ACCEPT`;
- optimize Presence Space;
- hide heuristic inputs behind false numerical precision;
- keep tuning coefficients until a preferred node wins.

## Executable reference

```bash
python3 skills/graph-field-orientation/score_graph_field.py \
  skills/graph-field-orientation/examples/neo-resonance-2026-08-15.json \
  --pretty
```

The scorer is deterministic, dependency-free and advisory-only.
