# Article 12 Sources — Evidence Must Bind the Transition

**Article ID:** I001-RN-EBT  
**Article:** [`12-evidence-must-bind-the-transition.md`](12-evidence-must-bind-the-transition.md)  
**Last verified:** 2026-08-15

---

## Evidence policy

This companion separates:

- public implementation verification reports;
- public architecture proposals;
- RESONANCE design synthesis;
- previously published RESONANCE contracts;
- explicit non-claims.

Article 12 does **not** claim that CrewAI or LangGraph has adopted the proposed Evidence-Bound Transition model, `ELR-I9`, or Terminality Binding as a vendor-native guarantee.

Where a public commenter reports code inspection, CI state, test counts, or behavior, that evidence remains classified as a **public verification / implementation report** unless RESONANCE independently reproduces it against the referenced repository state.

---

## S1 — CrewAI GuardrailProvider discussion

**Source:** `crewAIInc/crewAI#4877`  
**Type:** Public GitHub architecture / implementation discussion

Canonical issue:

https://github.com/crewAIInc/crewAI/issues/4877

The thread began around provider-agnostic pre-tool-call authorization and later expanded into durable deferral, authorization occurrence identity, freshness, use-time revalidation, execution binding, observer provenance, and replay/TOCTOU boundaries.

### Supported use in Article 12

The thread provides a real public setting in which historical verification, use-time admissibility, and execution occurrence become distinct architectural questions.

---

## S2 — `babyblueviper1`: use-time revalidation verified and next TOCTOU named

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5301964686

**Classification:** Public implementation verification report + cross-system architecture observation

The commenter reports independently checking:

- `headRefOid` at `99cbc15`;
- green conformance CI;
- 24 tests in `test_elr_conformance.py` plus 6 in `test_elr_use_time.py`;
- direct implementation behavior of `revalidate_receipt_for_use()`.

The report states that `verify_receipt()` remains historical, while use-time revalidation replays selected edges against `current_context` through the existing availability primitive.

The same comment identifies a remaining TOCTOU boundary between successful revalidation and actual execution and compares a `use_token` / `context_digest` approach to optimistic concurrency / compare-and-swap.

It also reports that the commenter's own `/review` verdict design intentionally has no built-in expiry/TTL and therefore carries an analogous unresolved freshness question.

### What this supports

- historical verification and current admissibility can be intentionally separate semantics;
- use-time revalidation can still leave a later revalidation-to-execution race;
- the same failure shape was recognized across more than one system by the public commenter.

### Evidence-strength note

The exact test count, code trace and external-system characterization are statements in the public verification report. Article 12 does not independently elevate them to vendor guarantees.

---

## S3 — `safal207`: ELR-I9 — Execution Binding

**Source comment:**

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5302214044

**Classification:** RESONANCE-adjacent public architecture proposal

The comment proposes:

```text
ELR-I9 — Execution Binding
```

with the invariant that a successful use-time revalidation may authorize only the specific execution occurrence/context it was bound to, and that consumption should fail closed if the relevant context/version changed.

The proposed semantic chain is:

```text
historical validity
        ->
current admissibility
        ->
execution-bound authorization
```

The comment explicitly favors keeping `verify_receipt()` historical rather than silently making its meaning time-dependent.

### Supported design inference

```text
valid evidence
!=
automatic permission for an arbitrary later execution
```

---

## S4 — LangGraph cancellation issue

**Source:** `langchain-ai/langgraph#5672`  
**Type:** Public GitHub issue / cancellation + streaming + persistence discussion

Canonical issue:

https://github.com/langchain-ai/langgraph/issues/5672

The thread discusses loss or rollback of user-visible streamed state around run cancellation, checkpoint/history behavior, persistence boundaries, transport semantics, and recovery.

Article 09 already distilled this discussion into a separate durability-boundary article.

---

## S5 — `atomicdjt`: happens-before cancellation contract

**Source comment:**

https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5301563787

**Classification:** Public architecture proposal

The comment distinguishes explicit user cancellation from transport interruption and proposes the testable ordering:

```text
C = cancellation accepted
P = bounded persistence/drain outcome established
T = terminal interrupted state published

assert C < P < T
```

`P` may be a receipt such as:

```text
durable | partial | abandoned
```

with the relevant durable checkpoint / stream sequence attached.

The proposal specifically calls for crash-boundary tests around:

- crash after `C` before `P`;
- crash after `P` before `T`;
- recovery without terminal publication unsupported by persistence outcome;
- explicit separation of socket/network interruption from intentional cancellation.

### What this supports

- persistence knowledge should precede terminal publication when cancellation completion is used as a synchronization boundary;
- a persistence outcome can be explicit even when it is partial or abandoned;
- transport lifecycle and intentional cancellation lifecycle should remain distinguishable.

---

## S6 — `safal207`: Terminality Binding

**Source comment:**

https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5302243548

**Classification:** RESONANCE-adjacent public architecture proposal

The comment argues that `C < P < T` gives temporal ordering but not yet an explicit causal dependency.

It proposes binding a terminal transition to the exact persistence receipt it depends on, with a shape similar to:

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

The resulting crash semantics are:

```text
C without P -> recovery/indeterminate, not terminal
C + P without T -> recovery may publish T idempotently
T without referenced P -> invalid state
transport interruption -> separate causal branch
```

### Supported design inference

```text
happens-before
!=
explicit causal evidence binding
```

---

## S7 — Article 09: Cancellation Is a State Transition

Canonical article:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/09-cancellation-is-a-state-transition.md

Article 09 separates:

```text
user-visible stream frontier
durable graph frontier
terminal lifecycle state
```

and proposes a machine-readable terminal lifecycle receipt plus a cancellation/persistence happens-before boundary.

### Relationship to Article 12

Article 12 adds a stricter requirement when terminal meaning depends on a persistence result:

```text
terminal transition
        -> must cite ->
exact persistence/settlement occurrence
```

---

## S8 — Article 10: Consent Has a Causal Lifetime

Canonical article:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/10-consent-has-a-causal-lifetime.md

Article 10 separates:

```text
semantic decision identity
!=
authorization occurrence identity
!=
execution occurrence identity
```

and proposes an Authorization Consumption Boundary.

### Relationship to Article 12

Article 12 generalizes the same structural requirement from authorization to evidence-dependent state transitions:

```text
exact evidence occurrence
        -> explicit binding ->
exact consequential transition occurrence
```

---

## S9 — Article 11: Evidence Has a Route

Canonical article:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/11-evidence-has-a-route.md

Article 11 treats verification as an evidence-routing problem: hard proof obligations first define the admissible route set; only then may the runtime optimize cost/latency/coordination.

### Relationship to Article 12

Route selection and even successful verification are still not execution authority.

Article 12 adds the final transition edge:

```text
proof obtained
        ↓
bind proof occurrence to transition
        ↓
consume / settle under explicit semantics
```

---

## S10 — RESONANCE synthesis: Evidence-Bound Transition

**Classification:** New design synthesis in Article 12

The following names are RESONANCE synthesis primitives rather than claimed vendor-native terms:

```text
Evidence-Bound Transition (EBT)
Terminality Binding
semantic TOCTOU
EBT-I1 .. EBT-I7
```

The general proposed invariant is:

> A consequential state transition should be causally bound to the exact evidence occurrence that authorizes, validates, or settles it whenever that distinction is required by the system's safety/recovery model.

This is intentionally narrower than a claim of universal distributed transactionality.

The model allows systems to remain non-atomic across external boundaries while still making the gap explicit, versioned, rejectable and recoverable.

---

## Claim map

| Claim | Evidence | Strength |
|---|---|---|
| CrewAI thread contains public discussion of use-time revalidation and revalidation→execution TOCTOU | S1, S2 | Public issue fact / verification report |
| `babyblueviper1` reported direct verification of the revalidation implementation and 30 tests | S2 | Public verification report |
| ELR-I9 / Execution Binding was proposed publicly | S3 | Public design proposal |
| LangGraph thread contains a proposed `C < P < T` cancellation ordering | S4, S5 | Public issue fact / design proposal |
| Explicit cancel and transport interruption were proposed as distinct lifecycle causes | S5 | Public design proposal |
| Terminality Binding was proposed publicly | S6 | Public design proposal |
| CrewAI has adopted ELR-I9 | None | **Not claimed** |
| LangGraph has adopted Terminality Binding | None | **Not claimed** |
| EBT is a formal industry standard | None | **Not claimed** |
| Explicit evidence binding guarantees distributed atomicity | None | **Not claimed** |
| Every transition requires cryptographic receipts | None | **Not claimed** |

---

## Proposed falsification suite

A future portable conformance suite should attempt at least:

```text
EB-1  validate at context N -> mutate to N+1 -> consume token for N -> BLOCK/revalidate
EB-2  bind evidence to X1 -> consume from X2 -> BLOCK unless explicit transfer semantics
EB-3  consume one-shot authorization at X1 -> replay at X2 -> BLOCK
EB-4  terminal T references missing settlement P -> invalid/unreconciled
EB-5  C + P -> crash before T -> restart -> publish T idempotently from exact references
EB-6  C1/P1 and C2/P2 -> T2 cites P1 -> invalid causal binding
EB-7  transport disconnect -> must not silently become explicit cancellation
EB-8  superseded evidence remains historical but does not retain current authority
```

A reference implementation should state which boundaries it can make atomic and which remain protocol-level compare-and-reject boundaries.

---

## Explicit non-claims

Article 12 does not claim:

- official CrewAI adoption of `ELR-I9`;
- official LangGraph adoption of Terminality Binding;
- production guarantees beyond the cited vendor documentation / public issue facts;
- universal one-shot authorization semantics;
- universal cryptographic receipt requirements;
- elimination of all TOCTOU races;
- Byzantine fault tolerance;
- formal proof of EBT safety/liveness;
- that temporal ordering is unimportant;
- that every evidence role requires a separate storage object;
- that partial streamed output should automatically become normal checkpoint state.

The narrow claim is:

> When the meaning or admissibility of a consequential transition depends on a specific evidence occurrence, an explicit causal reference is stronger and more recoverable than relying on adjacency, timestamps, a generic PASS flag, or an unbound historical verdict.
