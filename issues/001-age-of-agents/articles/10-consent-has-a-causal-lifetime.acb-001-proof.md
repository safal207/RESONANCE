# Article 10 Executable Evidence Addendum — ACB-001

**Article:** [`Consent Has a Causal Lifetime`](10-consent-has-a-causal-lifetime.md)  
**Article ID:** I001-RN-CCL  
**Executable contract:** ACB-001 — Authorization Consumption Boundary  
**Verified:** 2026-08-15

---

## Result

The execution boundary proposed in Article 10 now has a runnable reference conformance implementation in `safal207/pythiaLabs`.

Canonical development PR:

https://github.com/safal207/pythiaLabs/pull/260

Exact verified head:

```text
c989776bc366673a2b7fddf57c653fe3b914db41
```

Canonical GitHub Actions run for that exact head:

https://github.com/safal207/pythiaLabs/actions/runs/31865527490

Observed result:

```text
workflow: ACB conformance
status: completed
conclusion: success
head: c989776bc366673a2b7fddf57c653fe3b914db41
```

Local reference run before publication:

```text
18 tests
18 passed
0 failed
```

The remote workflow executes the same Python `unittest` conformance suite on GitHub Actions / Python 3.12.

---

## Executable package

```text
standards/agent-continuity/authorization-consumption/
├── ACB-001-AUTHORIZATION-CONSUMPTION-BOUNDARY.md
├── schema/
│   ├── authorization-occurrence.schema.json
│   ├── proposed-execution.schema.json
│   └── consumption-receipt.schema.json
├── conformance/
│   ├── acb_reference.py
│   ├── test_acb_conformance.py
│   └── requirements.txt
└── fixtures/
    ├── accepted-consumption.json
    └── rejected-consumption-cases.json
```

CI:

```text
.github/workflows/acb-conformance.yml
```

---

## What is mechanically checked

The reference suite now attempts to falsify the Article 10 model across these boundaries:

1. exact scope match succeeds;
2. normalized arguments change after approval → blocked;
3. actor changes after approval → blocked;
4. authority epoch changes after approval → blocked;
5. declared freshness condition changes → blocked;
6. declared current freshness value is missing → blocked;
7. one-shot authorization is consumed by `X1`, then retry `X2` attempts reuse → blocked;
8. reusable authorization works only under an explicit bounded use policy;
9. cancellation before effect crossing → blocked;
10. supersession before effect crossing → blocked;
11. two signed authorization occurrences may share one semantic `decision_ref` while remaining independently addressable;
12. lookup by semantic ref alone becomes `OCCURRENCE_AMBIGUOUS` when multiple occurrences exist;
13. wrong `decision_event_id` / `decision_ref` pairing fails closed;
14. deferred / denied / expired / stale / revoked / superseded / cancelled / consumed authorization cannot be consumed;
15. policy-version drift fails closed;
16. a retry may carry a new `execution_id` without changing the frozen execution-scope digest — reuse permission remains a separate usage-policy decision.

The suite therefore keeps three identities separate:

```text
semantic decision identity
        !=
authorization occurrence identity
        !=
execution occurrence identity
```

---

## ACB reference boundary

The reference implementation computes a canonical execution-scope digest over:

```text
logical_operation_id
tool_name
normalized_args
actor_ref
policy_version
authority_ref
authority_epoch
relevant_state_refs
```

and then separately checks named freshness predicates from `revalidate_if`.

A successful one-shot transition is:

```text
resolved_allow
      ↓
exact occurrence recovered
      ↓
scope digest matches
      ↓
freshness conditions match
      ↓
usage policy permits consumption
      ↓
CONSUMED by execution X1
```

A later execution `X2` cannot reuse that occurrence merely because the semantic decision still means `ALLOW`.

---

## Composition with ACI-001

ACB-001 intentionally remains separate from the existing Authority Causality Invariant.

```text
ACI-001
Does this actor currently have authority over the effect/resource?

ACB-001
Which exact authorization occurrence may this exact execution consume?
```

A high-consequence runtime may compose them:

```text
current authority admissible
AND
current authorization consumable
        ↓
release effect
```

This preserves the Article 10 rule:

> **Valid historical consent does not imply current execution authority.**

---

## Evidence classification

| Statement | Classification |
|---|---|
| ACB-001 files exist on `pythiaLabs` PR #260 | Verified repository fact |
| Exact head is `c989776bc366673a2b7fddf57c653fe3b914db41` | Verified repository fact |
| GitHub Actions run `31865527490` completed successfully | Verified CI result |
| Local reference suite ran 18/18 | Reproduced local conformance result |
| ACB is merged into CrewAI | **Not claimed** |
| ACB is merged into AG2 | **Not claimed** |
| ACB provides distributed atomicity across arbitrary external side effects | **Not claimed** |
| ACB eliminates every TOCTOU race | **Not claimed** |

---

## Current status

The implementation is currently carried by a **draft pull request** in `pythiaLabs`.

Therefore the strongest accurate statement is:

> ACB-001 is an executable, remotely green reference contract on an exact published branch head; it is not yet claimed as a merged vendor or production standard.

This converts Article 10's proposed falsification surface from prose into a runnable artifact without overstating adoption.
