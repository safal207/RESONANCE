# ELR-001 Executable Evidence — Evidence Logistics Routing

**Parent article:** [Evidence Has a Route](./11-evidence-has-a-route.md)  
**Protocol:** ELR-001 — Evidence Logistics Routing  
**Implementation repository:** `safal207/pythiaLabs`  
**Draft PR:** `#261`  
**Exact head:** `ef31ec51910b66be74c1e2fed5852381771feb49`  
**Canonical CI run:** `31873923086`  
**Result:** **SUCCESS**  
**Date:** 2026-08-15

---

## What became executable

Article 11 proposed a routing rule:

> **First filter by hard proof obligations. Then choose the lowest-cost admissible route.**

ELR-001 turns that rule into a bounded reference contract.

The implementation models a directed proof graph whose edges carry:

```text
provides[]
bindings{}
cost{}
```

A routing request binds the selection to:

```text
action_scope_digest
authority_epoch
policy_version
state_version
now_tick
risk_tier
reversibility
required_proofs[]
cost_weights{}
```

The reference router runs Dijkstra over:

```text
(graph node, accumulated proofs)
```

rather than graph node alone.

This makes proof accumulation part of the search state.

---

## Why the order matters

ELR-001 does **not** optimize a mixed score such as:

```text
cost + safety_penalty
```

Instead it first excludes paths whose contextual bindings fail or whose accumulated proof set cannot satisfy the hard obligations.

Only the surviving paths enter cost optimization.

The executable invariant is therefore:

```text
inadmissible path
    ↓
removed before optimization

admissible paths
    ↓
lowest weighted cost selected
```

A zero-cost unsafe shortcut cannot win.

---

## Reference behavior

The published fixture contains multiple candidate routes.

For a low-risk reversible request requiring only current authority and scope binding, the reference router selects:

```text
START
  ↓ sync-check
SYNC
  ↓ sync-execute
EXECUTE
```

For a high-risk irreversible request requiring fresh evidence, an independent verifier, human approval, exact occurrence binding and one-shot consumption, it selects:

```text
START
  ↓ independent-verifier
VERIFY
  ↓ human-defer-resolve
HUMAN
  ↓ consume-and-execute
EXECUTE
```

Thus `sync` versus `async` is not hard-coded as the policy. It emerges from the proof obligations and currently admissible graph.

---

## Conformance evidence

The suite contains **24 tests**.

Covered falsification cases include:

- low-risk sync route selection;
- high-risk independent + human + consumption route;
- zero-cost route missing hard proof cannot win;
- reaching `EXECUTE` without required proof is not admissible;
- stale cached evidence reroutes;
- future-dated evidence is rejected;
- authority-epoch drift;
- policy-version drift;
- state-version drift;
- action-scope drift;
- risk ceilings;
- reversible-only shortcuts;
- path-dependent proof accumulation;
- cost weighting among admissible routes only;
- deterministic equal-cost tie-break;
- negative cost rejection;
- invalid graph endpoint rejection;
- duplicate edge-id rejection;
- request/graph digest binding;
- receipt tamper detection;
- path tamper detection even after receipt digest recomputation;
- no-route fail-closed behavior;
- zero-cost cycle termination.

Local pre-publication reference run: **24/24 PASS**.

The canonical remote evidence is the pull-request run on the exact final head:

```text
workflow: ELR conformance
run:      31873923086
event:    pull_request
head:     ef31ec51910b66be74c1e2fed5852381771feb49
result:   success
```

GitHub Actions:
https://github.com/safal207/pythiaLabs/actions/runs/31873923086

Draft PR:
https://github.com/safal207/pythiaLabs/pull/261

---

## Evidence boundary

This result proves a narrower claim than the Article 11 thesis as a whole.

It demonstrates that the reference implementation can, for the published finite graph model:

1. preserve hard proof obligations as non-negotiable constraints;
2. exclude contextually invalid proof edges before optimization;
3. accumulate proofs across a path;
4. select the deterministic lowest-cost admissible path;
5. fail closed when no admissible path exists;
6. produce and independently recompute a route-selection receipt.

It does **not** prove:

- that the policy supplied the correct hard obligations;
- that the cost weights model real-world value correctly;
- that Dijkstra is universally optimal for dynamic or probabilistic evidence networks;
- that the selected route remains valid after state/time/authority changes;
- that the selected action executed;
- formal global safety or liveness;
- adoption by CrewAI, AG2 or another framework.

---

## Relation to the causal stack

```text
ACI
Who may act now?
        ↓
ACB
Which exact permission may this execution consume?
        ↓
ELR
Which admissible proof path should be used here and now?
```

The three questions remain separate.

A route receipt is evidence about route selection. It does not silently become authority, authorization occurrence, execution proof or outcome proof.

---

## Reader falsification remains open

The live Article 11 poll remains open:

https://github.com/safal207/RESONANCE/issues/58

`Agree`, `Partially agree`, and `Disagree` remain useful signals.

A reproducible counterexample to ELR-I1–I7 is stronger than a positive vote.
