# Article 10 Sources — Consent Has a Causal Lifetime

**Article ID:** I001-RN-CCL  
**Article:** [`10-consent-has-a-causal-lifetime.md`](10-consent-has-a-causal-lifetime.md)  
**Last verified:** 2026-08-15

---

## Evidence policy

This companion separates:

- public architecture proposals;
- public implementation reports;
- verified repository facts;
- RESONANCE design inference;
- explicit non-claims.

The article does **not** claim that CrewAI, AG2, or another framework has adopted the Authorization Consumption Boundary (ACB) model.

Where a third-party commenter reports production or live-ledger behavior, this file treats it as a **public reported observation** unless independently reproduced here.

---

## S1 — CrewAI GuardrailProvider issue

**Source:** `crewAIInc/crewAI#4877`  
**Title:** `[FEATURE] GuardrailProvider interface for pre-tool-call authorization`  
**Type:** Public GitHub issue / architecture discussion

Canonical issue:

https://github.com/crewAIInc/crewAI/issues/4877

The issue proposes a provider-agnostic authorization seam layered over CrewAI's existing pre-tool-call hook path. The public discussion later expands into async/human approval, deferred workflow state, provenance, occurrence identity, stale consent, and exact decision binding.

### Supported use in Article 10

- the thread genuinely discusses ALLOW/DENY plus deferred human/external approval;
- the thread contains proposals to persist authorization decisions rather than keep an in-process pause alive;
- the thread contains explicit discussion of stale consent and binding authorization to normalized execution scope.

### Non-claim

Article 10 is not a description of current CrewAI production behavior unless a specific source below says so.

---

## S2 — `atomicdjt`: durable deferred tool outcome

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5291853141

**Classification:** Public architecture proposal

The comment proposes:

```text
before_tool_call
  -> ALLOW | DENY | DEFER(decision_id, continuation_descriptor)
```

with a durable pending authorization record, a typed `tool_deferred` result, ordinary dependency blocking for downstream work, and a fresh continuation/replay after an external resolver supplies allow/deny.

The same proposal recommends binding the pending decision to a digest including at least:

```text
tool_name
normalized_args
agent / crew identity
policy version
relevant state / version
```

and re-checking that binding plus freshness-sensitive conditions before execution.

It also suggests stable `decision_id`, status, and policy/provenance metadata on `GuardrailDecision`, including synchronous allow/deny decisions.

### What this supports

- DEFER can be modeled as durable workflow state rather than a long-lived coroutine;
- stale consent is a real design concern at deferred-resolution time;
- exact execution-scope binding is a useful authorization primitive;
- authorization facts benefit from durable IDs and provenance.

### What this does not prove

- that the exact proposed API has been merged into CrewAI;
- that digest binding alone closes every TOCTOU window;
- that one-shot consumption is universally required.

---

## S3 — `babyblueviper1`: semantic decision identity vs occurrence identity

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5293583170

**Classification:** Public implementation report / code-trace report

The commenter reports tracing a ledger implementation in which `verdict_outcome` cites a semantic `decision_ref` but does not carry a separate exact occurrence pointer such as `cites_event_id`.

The report states that multiple separately issued signed events can share the same `decision_ref` because the semantic reference is derived from a fixed content preimage while event-specific data such as creation time/signature occurrence is distinct.

The commenter reports a live-ledger case where two distinct signed events carried the same semantic decision reference and concludes that a verifier holding only the semantic reference cannot prove which exact authorization occurrence was intended.

The proposed additive fix is an optional exact event citation plus explicit ambiguity on legacy rows where a semantic ref resolves to multiple candidate occurrences.

### Supported design inference

```text
semantic decision identity
        !=
authorization occurrence identity
```

### Evidence-strength note

The reported live-ledger counts and production characterization are statements by the public commenter. Article 10 does not independently re-run that external ledger measurement and therefore does not elevate those numbers to independently verified RESONANCE facts.

---

## S4 — `babyblueviper1`: stale-consent relation to `revalidate_if`

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5293659410

**Classification:** Public cross-thread architecture analysis

The comment explicitly connects the stale-consent seam to `safal207`'s AG2 `PreflightVerdict.revalidate_if` contract and notes that the CrewAI-side DEFER-resolve boundary adds a distinct execution-scope binding problem.

It also endorses stable `decision_id` + status + provenance as useful even outside the deferred path.

### What this supports

- freshness invalidation and exact execution-scope binding are related but distinct controls;
- authorization-time binding is not automatically the same as resolve-time binding;
- denial/deferral should be inspectable facts rather than inferred absences.

---

## S5 — `babyblueviper1`: observer-vantage split shipped

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5293642732

**Classification:** Public implementation report

The commenter reports shipping an additive split between:

```text
outcome_observation_vantage
```

and:

```text
decision_vantage_resolution
```

while preserving legacy `outcome_vantage` compatibility, with a reported 103-test passing ledger suite and commit `ca48bd7`.

### Relevance to Article 10

This is supporting context for a broader pattern used throughout RESONANCE:

> identities and epistemic/causal roles that answer different questions should remain independently representable instead of being collapsed into one field.

Article 10 applies the same separation discipline to semantic decision identity, authorization occurrence, and execution occurrence.

### Evidence-strength note

The deployment/test statement is a public report by the commenter unless separately reproduced in the referenced repository/runtime.

---

## S6 — AG2 pre-flight verification proposal

**Source:** `ag2ai/ag2#3156`  
**Author:** `safal207`  
**Title:** `[Feature Request]: Pre-flight verification layer for intent-bound external evidence before tool execution`

Canonical issue:

https://github.com/ag2ai/ag2/issues/3156

**Classification:** Verified public proposal / repository fact

The proposal distinguishes:

```text
logical_operation_id
```

from:

```text
execution_id
```

so retries/re-drives can remain concrete execution attempts under one logical operation.

It defines an intent-bound `PreflightVerdict` carrying:

```text
verdict_id
intent_ref
decision
verifier_id
authority_basis
evidence_refs
issued_at
expires_at
revalidate_if
```

and states that a verdict must not authorize an action carrying a different `intent_ref`.

The proposal's failure semantics explicitly include:

- mismatched evidence;
- missing required evidence;
- expired/stale verdict;
- retry with new `execution_id`;
- verifier timeout/error;
- canonical binding rather than producer-asserted labels.

### Supported design inference

```text
logical operation identity
        !=
execution occurrence identity
```

and

```text
historical verdict validity
        !=
automatic execution-time validity
```

---

## S7 — Article 08: Authority Has a History

Canonical article:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/08-authority-has-a-history.md

Article 08 introduces authority causality and the invariant:

```text
correct knowledge
!=
current authority
```

It models versioned authority state, transfer/revoke, and stale-writer rejection.

### Relationship to Article 10

Article 10 composes, but does not replace, that layer:

```text
historically valid consent
!=
current execution authority
```

An unchanged approval scope is still insufficient if the actor's authority was revoked or superseded before execution.

---

## S8 — Article 09: Cancellation Is a State Transition

Canonical article:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/09-cancellation-is-a-state-transition.md

Article 09 distinguishes execution state, visible stream state, durable state, and terminal lifecycle state, and argues that explicit cancellation should leave a machine-readable boundary for safe resume.

### Relationship to Article 10

A pending or resolved authorization can be superseded by cancellation. A recovered continuation must not silently resurrect execution permission from a pre-cancel workflow state.

---

## S9 — RESONANCE design inference: Authorization Consumption Boundary

**Classification:** New design proposal in Article 10

The following are not quoted as existing CrewAI or AG2 contracts:

```text
Authorization Consumption Boundary (ACB)
consumed_by_execution_id
one-shot authorization consumption
Causal Permission Graph
```

These are RESONANCE synthesis primitives derived from the public seams above.

The core proposed check is:

```text
exact authorization occurrence known
AND semantic scope matches
AND freshness predicates hold
AND authority/policy state remains admissible
AND usage policy permits consumption
AND execution occurrence is bound to that consumption
```

Only then should consequential execution cross the authorization boundary.

---

## Claim map

| Claim | Evidence | Strength |
|---|---|---|
| CrewAI issue #4877 discusses provider-agnostic pre-tool authorization | S1 | Verified public issue fact |
| Durable `DEFER` rather than long-lived suspension was proposed | S2 | Public architecture proposal |
| Deferred approval should be bound to normalized execution scope and freshness state | S2 | Public architecture proposal |
| A semantic decision reference can differ from exact issued occurrence | S3 | Public implementation report + strong design consequence |
| `revalidate_if` exists in the AG2 proposal | S6 | Verified public proposal fact |
| `logical_operation_id` and `execution_id` are intentionally distinct in that proposal | S6 | Verified public proposal fact |
| CrewAI has adopted ACB | None | **Not claimed** |
| AG2 has adopted ACB | None | **Not claimed** |
| Every approval must be one-shot | None | **Not claimed** |
| Digest revalidation alone eliminates every TOCTOU race | None | **Not claimed** |
| ACB is formally proven safe/live | None | **Not claimed** |

---

## Explicit non-claims

Article 10 does not claim:

- a vendor-native CrewAI implementation of `DEFER`;
- a vendor-native AG2 implementation of ACB;
- universal transactional atomicity between authorization consumption and external side effects;
- Byzantine fault tolerance;
- cryptographic issuer identity in every runtime;
- universal one-shot semantics;
- elimination of all distributed TOCTOU races;
- formal verification of safety/liveness;
- that timestamps alone establish causal binding;
- that a semantic decision hash is defective merely because multiple historical occurrences share it.

The narrow claim is:

> When a consequential execution is justified by authorization, semantic decision identity, exact authorization occurrence, freshness/admissibility state, and concrete execution consumption answer different questions and should remain independently inspectable when the system's risk model requires them.

---

## Proposed falsification suite

A future executable conformance suite should attempt at least:

```text
A. approved scope == executed scope -> admissible
B. normalized args mutate after approval -> blocked
C. actor/authority epoch changes -> blocked or explicit revalidation path
D. one-shot occurrence reused by X2 -> blocked
E. E1 and E2 share semantic D -> still independently addressable
F. outcome cites only ambiguous D -> occurrence ambiguity surfaced
G. cancellation supersedes pending continuation -> old approval path not resurrected
H. freshness predicate changes between resolve and consumption -> blocked/revalidated
```

A reference implementation should clearly state where it can and cannot make the `revalidate -> consume -> execute` boundary atomic.
