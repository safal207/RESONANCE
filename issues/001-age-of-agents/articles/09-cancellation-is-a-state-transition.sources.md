# Sources — Article 09: Cancellation Is a State Transition

**Article ID:** I001-RN-CDB  
**Status:** Evidence ledger  
**Last verified:** 2026-08-15

This file separates current vendor documentation, public issue reports, public design discussion, and RESONANCE inference. It must not be read as proof that every reported failure reproduces on every current LangGraph deployment.

---

## S1 — Public issue

**Source:** `langchain-ai/langgraph#5672`  
**Title:** Run Cancellation Causes Loss of Streamed State Not Yet Persisted as a Checkpoint  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672>  
**Type:** Public bug report / discussion  
**Use:** Establishes the reported UX/runtime failure and its history.  
**Limit:** The issue originated against older versions/configurations; its original causal explanation is not automatically current implementation truth.

---

## S2 — OSS persistence contract

**Source:** LangGraph documentation — Persistence  
**URL:** <https://docs.langchain.com/oss/python/langgraph/persistence>  
**Type:** Current official documentation  
**Verified:** 2026-08-15  
**Relevant facts:**

- checkpoints are saved at super-step boundaries;
- successful node/task writes may be persisted as pending writes before a full `StateSnapshot` checkpoint exists;
- pending writes support fault-tolerant resume without recomputing successful work.

**Use:** Rejects the overbroad claim that current LangGraph only persists state at complete run termination.

---

## S3 — Agent Server cancellation guide

**Source:** LangChain documentation — How to cancel a run  
**URL:** <https://docs.langchain.com/langsmith/cancel-run>  
**Type:** Current official documentation  
**Verified:** 2026-08-15  
**Relevant facts:**

- `interrupt` stops the worker and marks the run `interrupted`;
- run record and checkpoints are retained;
- thread state at the last completed step is preserved;
- `wait=True` blocks until the run has been fully cancelled and is described as useful when the caller wants the final state / created checkpoints;
- `rollback` has different semantics and removes the run/checkpoints.

**Limit:** This documentation does not itself state that every streamed event emitted before cancellation becomes durable graph state.

---

## S4 — Cancel Run API

**Source:** Agent Server API — Cancel Run  
**URL:** <https://docs.langchain.com/langsmith/agent-server-api/thread-runs/cancel-run>  
**Type:** Current official API reference  
**Verified:** 2026-08-15  
**Relevant facts:**

- endpoint supports `wait`;
- `action` values include `interrupt` and `rollback`.

**Use:** Defines the public cancellation surface discussed by the conformance proposal.

---

## S5 — Stream API / transport lifecycle

**Source:** Agent Server API — Create Run, Stream Output  
**URL:** <https://docs.langchain.com/langsmith/agent-server-api/thread-runs/create-run-stream-output>  
**Type:** Current official API reference  
**Verified:** 2026-08-15  
**Relevant facts:**

- `durability` supports `sync`, `async`, `exit`;
- `stream_resumable` controls persistence of stream chunks for resumable streaming;
- `on_disconnect` supports `cancel` or `continue`.

**Use:** Supports the claim that run durability, stream persistence, and disconnect behavior are distinct API surfaces.

---

## S6 — Cancellation cleanup root-cause hypothesis

**Author:** `gautamvarmadatla`  
**Comment:** `3940007464`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-3940007464>  
**Type:** Public implementation analysis / hypothesis  
**Use:** Identifies `AsyncBackgroundExecutor`, `AsyncPregelLoop.__aexit__`, cancellation and pending `aput/aput_writes` drain as a possible persistence boundary.  
**Limit:** Public analysis by a participant, not an official maintainer guarantee.

---

## S7 — Maintainer signal

**Author:** `christian-bromann`  
**Comment:** `4255974079`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-4255974079>  
**Type:** Maintainer public comment  
**Relevant statement:** Team was actively looking into the issue while rethinking streaming primitives.  
**Use:** Confirms maintainer awareness at that point in the issue timeline.  
**Limit:** Does not specify final ownership or guarantee a particular fix.

---

## S8 — RESONANCE partial-state distinction

**Author:** `safal207`  
**Comment:** `4808573509`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-4808573509>  
**Type:** Public design proposal  
**Core distinction:** persisted partial state is not automatically completed or safe-to-resume graph state.

---

## S9 — RESONANCE visible/durable authority model

**Author:** `safal207`  
**Comments:** `4834862736`, `4835887384`  
**URLs:**

- <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-4834862736>
- <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-4835887384>

**Type:** Public design proposals  
**Core distinctions:**

- last durable checkpoint;
- streamed delta exposed since that checkpoint;
- cancellation/abort transition;
- no silent authority transfer from newer user-visible state back to an older checkpoint;
- visible-state digest and provenance can provide a comparison surface for resume logic.

---

## S10 — Current OSS re-audit signal

**Author:** `TheDarkniteFalls`  
**Comment:** `5003438361`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5003438361>  
**Type:** Public re-audit report  
**Relevant claims:**

- current OSS checkpoints input and completed supersteps;
- successful pending writes are persisted;
- cancellation-cleanup tests exist;
- residual question may sit at Platform / Agent Server wait/drain semantics;
- earlier frontend `getBranchSequence` behavior appears distinct from persistence failure.

**Limit:** Participant audit; should be revalidated against exact current commits before being treated as a release guarantee.

---

## S11 — External ownership request

**Author:** `LB623`  
**Comment:** `5125755493`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5125755493>  
**Type:** Public contribution / ownership request  
**Use:** Explicitly frames the remaining ownership question as OSS Pregel vs Platform / Agent Server and proposes different test paths for each.

---

## S12 — Separate durability classes / terminal record

**Author:** `atomicdjt`  
**Comment:** `5291878115`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5291878115>  
**Type:** Public design proposal  
**Core distinctions:**

- streamed output and checkpointed graph state are different durability classes;
- cancellation can be represented as a first-class terminal record;
- explicit cancellation should be distinguished from transport interruption;
- normal checkpoint invariants should not be weakened merely to preserve visible partial output.

---

## S13 — Cancellation conformance / happens-before proposal

**Author:** `safal207`  
**Comment:** `5300522182`  
**URL:** <https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5300522182>  
**Published:** 2026-08-15  
**Type:** RESONANCE public conformance proposal  
**Proposed invariant:**

```text
cancel requested
  -> Pregel cleanup / pending-write drain attempted
  -> persistence outcome established
  -> terminal run state published
  -> history/state exposed to the client
```

**Proposed record dimensions:**

```text
last_checkpoint_id
last_stream_seq_emitted
last_stream_seq_durable
terminal_durability: durable | partial | abandoned
terminal_cause: explicit_cancel | transport_disconnect | failure
resume_policy: resume | reconcile | restart | block
```

**Proposed conformance path:**

```text
stream e1..ek
-> explicit cancel(wait=true, action="interrupt")
-> fetch run
-> fetch thread history/state
-> verify terminal durability record
-> send next message
-> prove there is no silent rollback to older durable state
```

**Limit:** This is a proposed testable contract, not a statement that Agent Server already exposes these fields.

---

## Evidence classification summary

```text
official current contract
  S2 S3 S4 S5

public reported failure / implementation analysis
  S1 S6 S7 S10

public contribution / design convergence
  S8 S9 S11 S12 S13

RESONANCE architecture inference
  Article 09 synthesis over the boundaries above
```

---

## Editorial guardrails

1. Do not say current LangGraph only checkpoints at full-run completion.
2. Do not say `wait=true` guarantees that every streamed token is durable.
3. Do not collapse task-level pending writes into full graph checkpoints.
4. Do not collapse intentional cancellation into transport disconnect.
5. Do not claim Platform ownership until a current integration reproduction proves the boundary.
6. Preserve the distinction between documented behavior, public participant analysis and RESONANCE proposal.
