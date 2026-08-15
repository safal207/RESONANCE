# ELR-001 Executable Evidence — Evidence Logistics Routing

**Parent article:** [Evidence Has a Route](./11-evidence-has-a-route.md)  
**Protocol:** ELR-001 — Evidence Logistics Routing  
**Implementation repository:** `safal207/pythiaLabs`  
**Draft PR:** `#261`  
**Exact head:** `99cbc155ee3a0e3bced5734af4b1766b396cda25`  
**Canonical CI run:** `31875961467`  
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

A routing request binds selection to action scope, authority epoch, policy version, state version, time, risk, reversibility, required proofs and cost weights.

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

It first excludes paths whose contextual bindings fail or whose proof set cannot satisfy the hard obligations. Only surviving paths enter cost optimization.

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

## External falsification: issuance correctness was not current applicability

After the first executable publication, `babyblueviper1` independently inspected the PR, exact head, CI run and falsification suite and then produced a concrete temporal counterexample.

The first draft had freshness primitives inside `edge_available(...)`, including `valid_until_tick` and `max_evidence_age_ticks`. But `verify_receipt(...)` required:

```text
receipt.evaluated_at_tick == request.context.now_tick
```

before replaying those edge bindings.

That was correct for historical receipt integrity, but it meant the API could answer only:

> **Was this route correctly selected at tick T?**

It could not directly answer the distinct runtime question:

> **Is this old selected route still admissible now at tick T+n?**

Restamping the original request changed the object bound by the receipt digest and therefore correctly failed historical verification before use-time freshness could be evaluated.

The counterexample exposed a real API gap rather than an error in the existing freshness primitive.

---

## The fix: two verification functions for two causal questions

The corrected reference keeps the strict historical verifier and adds:

```text
revalidate_receipt_for_use(
    receipt,
    original_request,
    original_graph,
    current_context,
)
```

The distinction is now explicit:

```text
verify_receipt(...)
= was this selection validly produced at issuance time T?

revalidate_receipt_for_use(..., current_context)
= is the already-selected route still admissible for use at T+n?
```

Use-time revalidation first requires the historical receipt to remain valid, then replays the exact selected edges against the current context for:

```text
valid_until_tick
max_evidence_age_ticks
authority_epoch
policy_version
state_version
action_scope_digest
risk_tier
reversibility
```

If a selected edge is stale or drifted, the result is:

```text
BLOCKED_ROUTE_STALE_OR_DRIFTED
```

The runtime may then issue a fresh routing request and select again.

Use-time revalidation does **not** automatically re-optimize. Current admissibility and current optimality are separate questions.

The new invariant is:

> **Historical verification != current applicability.**

A route receipt that was correct at T is not a timeless permission to use that route later.

---

## Conformance evidence

The suite now contains **30 tests**.

The original 24 cover:

- low-risk sync route selection;
- high-risk independent + human + consumption route;
- zero-cost route missing hard proof cannot win;
- reaching `EXECUTE` without required proof is not admissible;
- stale cached evidence rerouting;
- future-dated evidence rejection;
- authority/policy/state/action drift at selection time;
- risk and reversibility constraints;
- path-dependent proof accumulation;
- cost weighting only among admissible routes;
- deterministic tie-break;
- graph/schema corruption;
- request/graph digest binding;
- receipt and path tamper detection;
- no-route fail closed;
- zero-cost cycle termination.

Six additional tests preserve the external falsification and its repair:

1. historical verification stays bound to the issuance tick;
2. use-time revalidation accepts the selected route before expiry;
3. `valid_until_tick` expiry blocks the old route at later use time;
4. `max_evidence_age_ticks` expiry blocks stale evidence at later use time;
5. authority drift blocks the old route at later use time;
6. a current-time context earlier than issuance fails closed.

Canonical remote evidence:

```text
workflow: ELR conformance
run:      31875961467
event:    pull_request
head:     99cbc155ee3a0e3bced5734af4b1766b396cda25
result:   success
```

GitHub Actions:
https://github.com/safal207/pythiaLabs/actions/runs/31875961467

Draft PR:
https://github.com/safal207/pythiaLabs/pull/261

---

## Evidence boundary

The corrected result demonstrates that the reference implementation can, for the published finite graph model:

1. preserve hard proof obligations as non-negotiable constraints;
2. exclude contextually invalid proof edges before optimization;
3. accumulate proofs across a path;
4. select the deterministic lowest-cost admissible path at evaluation time;
5. fail closed when no admissible path exists;
6. recompute historical route-selection integrity;
7. separately revalidate the selected path against a later current context without mutating the historical request.

It does **not** prove:

- that policy supplied the correct hard obligations;
- that cost weights model real-world value correctly;
- that Dijkstra is universally optimal for dynamic or probabilistic evidence networks;
- that a route remains valid without later use-time revalidation;
- that revalidation and an external side effect are transactionally atomic;
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
ELR selection
Which admissible proof path should be chosen at T?
        ↓
ELR use-time revalidation
Is that selected path still admissible at T+n?
```

This external falsification strengthened the separation rather than weakening it.

The same recurring pattern now appears across the stack:

```text
historically correct
!=
currently applicable
```

A route receipt remains evidence about a past routing decision. Current use requires current proof.

---

## Reader falsification remains open

The live Article 11 poll remains open:

https://github.com/safal207/RESONANCE/issues/58

`Agree`, `Partially agree`, and `Disagree` remain useful signals.

The first concrete counterexample changed the executable contract and added six tests. That is exactly the intended role of the poll and upstream discussion: disagreement that survives inspection becomes part of the protocol's evidence history rather than disappearing.
