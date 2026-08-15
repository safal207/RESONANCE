# Article 13 Sources — Evidence Must Bind the Transition

**Article ID:** I001-RN-EBT  
**Article:** [`13-evidence-must-bind-the-transition.md`](13-evidence-must-bind-the-transition.md)  
**Last verified:** 2026-08-15

---

## Evidence policy

This companion separates:

- public implementation verification reports;
- public architecture proposals;
- RESONANCE design synthesis;
- previously published RESONANCE contracts;
- explicit non-claims.

Article 13 does **not** claim that CrewAI or LangGraph has adopted the proposed Evidence-Bound Transition model, `ELR-I9`, or Terminality Binding as a vendor-native guarantee.

Where a public commenter reports code inspection, CI state, test counts, or behavior, that evidence remains classified as a **public verification / implementation report** unless RESONANCE independently reproduces it against the referenced repository state.

---

## S1 — CrewAI GuardrailProvider discussion

**Source:** `crewAIInc/crewAI#4877`  
**Type:** Public GitHub architecture / implementation discussion

https://github.com/crewAIInc/crewAI/issues/4877

The thread expanded from provider-agnostic pre-tool-call authorization into durable deferral, authorization occurrence identity, freshness, use-time revalidation, execution binding, observer provenance and replay/TOCTOU boundaries.

---

## S2 — `babyblueviper1`: use-time revalidation verified; next TOCTOU named

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5301964686

**Classification:** Public implementation verification report + architecture observation

The commenter reports independently checking:

- `headRefOid` at `99cbc15`;
- green conformance CI;
- 24 tests in `test_elr_conformance.py` plus 6 in `test_elr_use_time.py`;
- direct behavior of `revalidate_receipt_for_use()`.

The report states that `verify_receipt()` remains historical while use-time revalidation checks selected edges against `current_context`.

The same comment identifies the next TOCTOU seam between successful revalidation and actual execution and compares a `use_token` / `context_digest` approach to optimistic concurrency / compare-and-swap.

### Evidence-strength note

The exact code/test verification is a public commenter report; Article 13 does not elevate it to a CrewAI vendor guarantee.

---

## S3 — `safal207`: ELR-I9 — Execution Binding

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5302214044

**Classification:** Public architecture proposal

Proposed invariant:

```text
ELR-I9 — Execution Binding
```

A successful use-time revalidation may authorize only the specific execution occurrence/context it was bound to; consumption should fail closed if the relevant context/version changed.

Semantic chain:

```text
historical validity
        ->
current admissibility
        ->
execution-bound authorization
```

The proposal explicitly keeps `verify_receipt()` historical rather than making historical verification semantics silently time-dependent.

---

## S4 — LangGraph cancellation issue

**Source:** `langchain-ai/langgraph#5672`  
**Type:** Public GitHub issue / streaming + cancellation + persistence discussion

https://github.com/langchain-ai/langgraph/issues/5672

Article 09 previously distilled this thread into a cancellation durability / resume-authority contract.

---

## S5 — `atomicdjt`: happens-before cancellation contract

https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5301563787

**Classification:** Public architecture proposal

The comment proposes:

```text
C = cancellation accepted
P = bounded persistence/drain outcome established
T = terminal interrupted state published

assert C < P < T
```

with `P` allowed to be:

```text
durable | partial | abandoned
```

and with explicit separation between intentional cancellation and transport interruption.

It also proposes crash-boundary tests after `C` before `P`, after `P` before `T`, and on restart.

---

## S6 — `safal207`: Terminality Binding

https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5302243548

**Classification:** Public architecture proposal

The comment argues that temporal order does not yet identify the concrete persistence outcome supporting a terminal claim.

Proposed shape:

```text
CancellationReceipt {
  cancellation_id
  cause
  persistence_outcome
  last_visible_seq
  last_durable_seq
  persistence_receipt_id
}

TerminalTransition {
  state: interrupted
  cancellation_id
  persistence_receipt_id
}
```

Proposed recovery semantics:

```text
C without P -> recovery/indeterminate, not terminal
C + P without T -> recovery may publish T idempotently
T without referenced P -> invalid state
transport interruption -> separate causal branch
```

---

## S7 — Article 09: Cancellation Is a State Transition

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/09-cancellation-is-a-state-transition.md

Article 09 separates user-visible stream state, durable graph state and terminal lifecycle state.

Article 13 adds:

```text
terminal transition
        -> exact causal reference ->
persistence/settlement occurrence
```

when terminal semantics depend on that persistence result.

---

## S8 — Article 10: Consent Has a Causal Lifetime

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/10-consent-has-a-causal-lifetime.md

Article 10 separates:

```text
semantic decision identity
!=
authorization occurrence identity
!=
execution occurrence identity
```

Article 13 generalizes the binding form from authorization consumption to evidence-dependent transitions.

---

## S9 — Article 11: Evidence Has a Route

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/11-evidence-has-a-route.md

Article 11 treats verification as evidence routing under proof obligations.

Article 13 adds the next edge:

```text
proof obtained
        ↓
bind exact evidence occurrence to exact transition
        ↓
consume / settle under explicit semantics
```

---

## S10 — Article 12: A Diagnostic Nobody Can See Is Not a Signal

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/12-a-diagnostic-nobody-can-see-is-not-a-signal.md

Article 12 establishes a closely related but distinct boundary:

```text
recorded owner/relation
!=
operationally reachable/executable relation
```

and distinguishes causal read basis, predecessor CAS, reachability and exact handoff acknowledgement.

Article 13 composes with that result: a fact outside the decision/transition path cannot protect the transition merely because it exists somewhere in the system.

---

## S11 — RESONANCE synthesis: Evidence-Bound Transition

**Classification:** New design synthesis in Article 13

The following terms are RESONANCE synthesis primitives rather than claimed vendor-native terminology:

```text
Evidence-Bound Transition (EBT)
Terminality Binding
semantic TOCTOU
EBT-I1 .. EBT-I7
```

General proposed invariant:

> A consequential state transition should be causally bound to the exact evidence occurrence that authorizes, validates or settles it whenever that distinction matters to the system's safety or recovery model.

This is narrower than a claim of universal distributed transactionality.

---

## Claim map

| Claim | Evidence | Strength |
|---|---|---|
| CrewAI thread publicly discusses use-time revalidation and revalidation→execution TOCTOU | S1, S2 | Public issue fact / verification report |
| `babyblueviper1` reported direct verification of the revalidation implementation and 30 tests | S2 | Public verification report |
| ELR-I9 / Execution Binding was proposed publicly | S3 | Public design proposal |
| LangGraph thread contains a proposed `C < P < T` cancellation ordering | S4, S5 | Public issue fact / design proposal |
| Explicit cancel and transport interruption were proposed as distinct lifecycle causes | S5 | Public design proposal |
| Terminality Binding was proposed publicly | S6 | Public design proposal |
| CrewAI has adopted ELR-I9 | None | **Not claimed** |
| LangGraph has adopted Terminality Binding | None | **Not claimed** |
| EBT is an industry standard | None | **Not claimed** |
| Evidence binding guarantees distributed atomicity | None | **Not claimed** |

---

## Proposed falsification suite

```text
EBT-1  validate context N -> mutate to N+1 -> consume token for N -> BLOCK/revalidate
EBT-2  bind evidence to X1 -> consume from X2 -> BLOCK unless explicit transfer semantics
EBT-3  consume one-shot A1 at X1 -> replay at X2 -> BLOCK
EBT-4  terminal T references missing P -> invalid/unreconciled
EBT-5  C + P -> crash before T -> restart -> idempotently publish T from exact references
EBT-6  C1/P1 and C2/P2 -> T2 cites P1 -> invalid causal binding
EBT-7  transport disconnect -> must not silently become explicit cancellation
EBT-8  superseded evidence remains historical but loses implicit current authority
```

---

## Explicit non-claims

Article 13 does not claim:

- official CrewAI adoption of `ELR-I9`;
- official LangGraph adoption of Terminality Binding;
- production guarantees beyond cited public evidence;
- universal one-shot authorization semantics;
- universal cryptographic receipt requirements;
- elimination of all TOCTOU races;
- Byzantine fault tolerance;
- formal EBT safety/liveness proof;
- that temporal ordering is unimportant;
- that every evidence role requires a separate storage object;
- that partial streamed output should automatically become normal checkpoint state.

The narrow claim is:

> When a consequential transition depends on a specific evidence occurrence, an explicit causal reference is stronger and more recoverable than adjacency, timestamps, a generic PASS flag or an unbound historical verdict.
