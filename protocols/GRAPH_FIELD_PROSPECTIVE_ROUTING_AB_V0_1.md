# Graph–Field Prospective Routing A/B v0.1

Status: **experimental / prospective / advisory / non-authorizing**

## 1. Purpose

This protocol creates the first calibration-compatible routing comparison for Graph–Field Dynamics (GFD) without inventing a retrospective baseline after an outcome is known.

The experiment is frozen **before either arm is evaluated**:

```text
same work-graph snapshot
        ├─ GFD orientation → treatment node
        └─ FIFO_READY_NODE → baseline node

frozen utility rubric
        ↓
read-only investigation of each selected node
        ↓
raw observed counters + evidence
        ↓
normalized utility under the predeclared rubric
        ↓
comparison
```

P2-1 is not retrofitted into this A/B. Its real outcome remains an unpaired historical observation.

Canonical invariant:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

## 2. Same candidate universe

Treatment and baseline see the same bounded work-node set.

A work node is not an arbitrary open pull request. It is a current Graph–Field work-graph location with explicit supporting evidence and a safe next transition.

This prevents the baseline from selecting unrelated old repository work merely because it predates the current system question.

Completed nodes are excluded. Explicitly blocked nodes remain visible but are ineligible for FIFO execution.

## 3. Treatment: GFD orientation

The treatment arm uses the existing GFD v0.1 scorer unchanged:

```text
Tension = Σ(weight_i × component_i)
Actionability = Tension × (1 - 0.70 × blockedness)
FieldScore = Actionability + bounded one-hop diffusion
```

After the completed P2-1 node is removed from the active graph, the treatment selection is the highest remaining field score.

No outcome data may enter the treatment score.

## 4. Baseline: FIFO_READY_NODE

The baseline deliberately ignores GFD components and scores.

Algorithm:

1. use the exact same active work-node set;
2. remove nodes explicitly marked `eligible=false`;
3. sort by `ready_since` ascending;
4. break exact timestamp ties by node id ascending;
5. select the first node.

`ready_since` must point to evidence showing when the current work node became concretely inspectable. It must not use an unrelated older PR from the same repository.

The FIFO baseline is intentionally simple. Its purpose is to test whether field-based routing adds value beyond an obvious queue discipline, not to construct the strongest possible competing optimizer.

## 5. Frozen utility rubric

The utility dimensions and weights are inherited from Graph–Field Calibration v0.2:

| Dimension | Weight | Raw rule before normalization |
|---|---:|---|
| `useful_finding` | 0.30 | 0 = no supported finding; 0.5 = exact evidence confirms state but does not alter the next safe action; 1 = evidence-backed finding materially changes the next safe action |
| `information_gain` | 0.25 | 0 = no uncertainty resolved; 0.5 = resolves one concrete work item; 1 = resolves uncertainty affecting at least 3 work items or a system-level contract |
| `blocked_work_avoidance` | 0.15 | 0 = none; 0.5 = prevents one blocked/stale action; 1 = prevents at least 2 |
| `stale_evidence_catch` | 0.10 | 0 = no exact subject/evidence drift found; 1 = exact drift requiring revalidation is found |
| `downstream_rework_avoidance` | 0.20 | 0 = none; 0.5 = redirects/replaces 1–2 otherwise separate reviews/actions; 1 = redirects/replaces at least 3 |

Utility is:

```text
U = 0.30F + 0.25I + 0.15B + 0.10S + 0.20R
```

Every normalized value must be accompanied by raw evidence counters or an exact binary observation. The rubric may not be changed after either outcome is inspected.

## 6. Frozen experiment for 2026-08-15

The first prospective comparison freezes the post-P2-1 graph.

Expected treatment:

```text
GFD → cml-memory-proposal-pressure
```

Expected baseline:

```text
FIFO_READY_NODE → liminaldb-codeql-dependency
```

The FIFO selection is based on the current relevant CodeQL dependency work node becoming inspectable on 2026-07-31, earlier than the current CML proposal-pressure queue and later work nodes.

The ProofPath organizational-independence node remains visible but ineligible because it awaits an external operator. No experiment may fabricate that independence to make the node executable.

## 7. Outcome discipline

The freeze record contains no arm outcome, normalized utility, advantage, winner, or weight proposal.

Valid lifecycle:

```text
FROZEN_BEFORE_OUTCOME
→ treatment observation
→ baseline observation
→ rubric scoring
→ PAIRED_OBSERVED
→ calibration eligibility check
```

Invalid lifecycle:

```text
observe one arm
→ change ready_since / candidate set / rubric
→ score the other arm
```

Any mutation to the frozen selection inputs creates a new experiment identity rather than rewriting this one.

## 8. Authority boundary

The experiment is read-only routing research.

It may not:

- merge or close candidate PRs;
- deploy software;
- write production state;
- execute payments or financial actions;
- grant security approval;
- fabricate an external operator;
- mutate canonical GFD weights.

Every freeze receipt must state:

```text
mode = ADVISORY_ONLY
authority_granted = false
calibration_allowed = false
weight_update_allowed = false
```

## 9. Falsification

A useful field model must survive comparison with a simpler policy.

If FIFO repeatedly matches or beats GFD under the same frozen utility rubric and comparable investigation budget, reduce the role of GFD or discard the unsupported components.

A single win does not validate the model. The first A/B provides one paired observation only; the existing calibration confidence rule still treats 1–4 observations as `INSUFFICIENT`.
