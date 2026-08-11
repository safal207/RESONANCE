# The Missing Trust Layer

**Deck:** Agent systems already have pieces of safety, observability, state management and provenance. What they still lack is a common way to prove that an action was allowed, causally understood, recoverable and correctly verified across its full trajectory.

**By:** RESONANCE Editorial

**Status:** Verified / Published

**Last verified:** 2026-08-11

## Signal

The agent stack is becoming more operational and more distributed.

OpenAI's Agents SDK exposes loops, tools, handoffs, sessions, guardrails, human-in-the-loop mechanisms and tracing. The Agent2Agent protocol defines stateful tasks with lifecycle states, timestamps, histories and artifacts. OpenTelemetry exists to reconstruct causal paths across distributed services. Durable-execution systems such as Temporal preserve workflow progress across crashes and outages. Sigstore binds artifacts to identity, timestamps and auditable verification evidence.

These systems solve different parts of the same deeper problem: once software can act across tools and time, trust cannot be represented by a final answer alone.

## Why it matters

For an agent that changes state, correctness is a property of a trajectory.

A final result can look correct even when:

- the wrong actor initiated it;
- a tool call was unauthorized for that phase;
- an intermediate transition violated an invariant;
- the system retried a non-idempotent operation;
- a partial failure left external state inconsistent;
- a later agent inherited incomplete or misleading context;
- logs recorded events but not the causal relationship between them;
- an artifact exists but its provenance cannot be independently verified.

The engineering question therefore changes from **"Did the model produce the right output?"** to **"Can we prove that the whole action path was legitimate, causally coherent, recoverable and evidenced?"**

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | Production agent runtimes are exposing orchestration, guardrails, state/session handling, human intervention and tracing as first-class primitives. | Verified fact | High | S-009, S-010 |
| C2 | Agent interoperability standards model work as stateful tasks with lifecycle states, timestamps, history and artifacts. | Verified fact | High | S-011 |
| C3 | Distributed observability requires propagated context to reconstruct causal relationships across service boundaries, not merely isolated logs. | Verified fact | High | S-012 |
| C4 | Recovery from crashes and outages is a distinct execution property that can be engineered independently of model quality. | Verified fact | High | S-013 |
| C5 | Verifiable provenance can bind an artifact to identity, digest, timestamp and a publicly auditable record rather than relying on self-report. | Verified fact | High | S-014 |
| C6 | A trustworthy agent system benefits from an integrated model of state + causality + phase + transition + time + recovery + verification + evidence. | Editorial inference / proposed framework | Medium-high | C1-C5 synthesis |

## Evidence

### S-009 — OpenAI Agents SDK

OpenAI documents a production agent runtime with an agent loop, handoffs, sandbox agents, guardrails, tools, sessions, human-in-the-loop support and built-in tracing.

This supports a narrow claim: modern agent runtimes need more than model invocation. It does not prove that one SDK design is a universal architecture.

### S-010 — OpenAI guardrails and tracing

OpenAI's documentation distinguishes input/output guardrails from tool guardrails and documents trace/span structures for agent activity and handoffs.

The same documentation also exposes boundaries: tool guardrails do not wrap every possible hosted or built-in tool path. That limitation is important counter-evidence against treating a single guardrail mechanism as a complete trust layer.

### S-011 — A2A task lifecycle

The Agent2Agent specification defines a task as a stateful unit of work. Tasks move through explicit lifecycle states and carry status timestamps, history and generated artifacts.

This is direct evidence that state, time and output artifacts are protocol-level concerns once agents coordinate across systems.

### S-012 — OpenTelemetry causal context

OpenTelemetry context propagation correlates traces, logs and other signals across process and network boundaries. Its documentation explicitly describes trace context as a way to build causal information across distributed services.

This is not an AI-specific control. That is precisely why it matters: causality is a systems property, not a prompt property.

### S-013 — Temporal durable execution

Temporal documents durable execution that resumes application progress after crashes, network failures and infrastructure outages.

The lesson is architectural rather than vendor-specific: recovery semantics are a separate layer of correctness. A model may choose the right next action and the surrounding workflow may still fail operationally.

### S-014 — Sigstore verification and provenance

Sigstore's Cosign can verify signed artifacts and attestations using identity, artifact digests, timestamps, certificates and transparency-log evidence.

Sigstore also documents what it does *not* guarantee. This is useful discipline: an evidence mechanism should state its trust assumptions and failure boundaries rather than turn "verified" into a magic word.

## The missing layer is not a missing product

The phrase **missing trust layer** can be misunderstood.

Many of the primitives already exist:

- authorization systems decide who may access resources;
- agent SDKs expose guardrails and approvals;
- protocols model task state;
- tracing systems capture execution paths;
- durable runtimes recover workflows;
- signing systems attest artifacts and provenance.

What is missing is a **shared verification model that connects these primitives around an agent action trajectory**.

Today an operator can often answer each of these questions in a different subsystem:

- Who acted? — identity provider.
- What tool was called? — agent trace.
- What changed? — application logs or database history.
- Was the action allowed? — policy engine.
- What happened after failure? — workflow engine.
- What artifact was produced? — storage or CI.
- Can the artifact be authenticated? — attestation system.

The hard part is proving that these answers describe the **same causal path**.

## The RESONANCE Trust Graph

We propose a compact model for reasoning about agent correctness:

```text
STATE
  + CAUSALITY
  + PHASE
  + TRANSITION
  + TIME
  + RECOVERY
  + VERIFICATION
  + EVIDENCE
```

This is a proposed editorial and engineering framework, not an established industry standard.

### 1. State

What is true before and after the action?

An action cannot be evaluated without knowing the state against which it was valid. "Refund payment" means something different before capture, after settlement, during a dispute, or after a previous refund.

### 2. Causality

What caused this action and what did this action cause?

Chronological adjacency is not enough. Two events can occur next to each other without one causing the other. A trustworthy system should preserve parent-child or otherwise explicit causal links where possible.

### 3. Phase

Where are we in the larger workflow?

Some actions are legal only during a specific phase: planning, approval, execution, verification, settlement, rollback, escalation. A permission without phase can be too broad.

### 4. Transition

Which state change is being attempted?

Represent the action as a transition rather than a vague intent:

```text
S0 --[actor/action]--> S1
```

Then attach invariants to the edge and destination.

### 5. Time

When did the state, authorization and evidence apply?

Agent work is increasingly asynchronous. A permission valid at planning time may be stale at execution time. A task can be retried after external state has changed. Timestamps and ordering become part of correctness.

### 6. Recovery

What is the defined return path after partial failure?

Recovery is not simply "retry." Safe recovery may require idempotency, compensation, rollback, reconciliation, human escalation or explicit abandonment.

### 7. Verification

Which invariant tells us the transition was acceptable?

Verification needs a checkable condition. Examples:

- balance never becomes negative;
- a refund cannot exceed captured value;
- production write requires approval token bound to the current operation;
- artifact digest must match the reviewed build;
- task may enter `completed` only after required evidence exists.

### 8. Evidence

What survives after execution so another observer can check the claim?

Evidence can include traces, state snapshots, diffs, receipts, signatures, attestations, policy decisions, timestamps, test results and human approvals.

Evidence is not the same as logging everything. Useful evidence is **bound to a claim and a transition**.

## A minimal trust record

A practical implementation could emit one record for every material transition:

```json
{
  "trajectory_id": "tr_01...",
  "actor": "agent://refund-specialist",
  "phase": "execution",
  "state_before": "captured",
  "action": "refund",
  "state_after": "refunded",
  "time": "2026-08-11T08:00:00Z",
  "cause": "approved_refund_request:r_42",
  "invariants": ["refund_total <= captured_total"],
  "recovery": "reconcile_or_compensate",
  "evidence": ["trace:...", "receipt:...", "policy:..."],
  "verification": "passed"
}
```

The exact schema will vary. The important idea is that the record binds identity, state, transition, time, cause, recovery and proof together.

## Causal model

```text
models gain tools and longer execution horizons
        ↓
agent actions cross process / service / human boundaries
        ↓
state and permissions become distributed
        ↓
failures become partial, asynchronous and causally ambiguous
        ↓
logs and final outputs alone become insufficient
        ↓
trust requires linked state + causality + recovery + evidence
```

## Counter-evidence and alternative explanations

### Alternative A — existing observability is enough

Distributed tracing can reconstruct a great deal of causality. But observability usually tells us **what happened**, not necessarily whether the transition was authorized, whether a domain invariant held, or whether an artifact is trustworthy.

### Alternative B — guardrails are the trust layer

Guardrails are important, but they are checks around selected inputs, outputs or tool calls. They do not automatically provide durable recovery, cross-system causal provenance or application-specific invariants.

### Alternative C — workflow engines already solve this

Durable execution solves a crucial part of the problem: progress and recovery. It does not by itself prove model intent, authorization semantics, artifact provenance or domain correctness.

### Alternative D — no new layer is needed; just integrate existing tools

This may ultimately be correct. The "trust layer" could emerge as conventions and integrations rather than a new platform. RESONANCE's claim is therefore architectural: **the guarantees must be connected**, not that a new vendor category must exist.

## Failure taxonomy

The Trust Graph gives us a practical failure taxonomy:

| Dimension | Example failure |
|---|---|
| State | agent acts on stale balance |
| Causality | action cannot be tied to the request that triggered it |
| Phase | production write happens before approval |
| Transition | illegal state edge is accepted |
| Time | authorization expires before execution |
| Recovery | retry duplicates a non-idempotent payment |
| Verification | success is declared without checking the invariant |
| Evidence | no durable artifact proves what changed |

This is useful for QA because it turns "agent safety" into testable system behavior.

## Verification

Checks performed before publication:

- [x] Material factual claims traced to primary documentation
- [x] A2A lifecycle and timestamp semantics checked against the current official specification
- [x] OpenAI guardrail limitations preserved rather than omitted
- [x] OpenTelemetry causal-context claim checked against official documentation
- [x] Recovery claim checked against Temporal's official documentation
- [x] Sigstore guarantees and limitations both represented
- [x] Proposed Trust Graph explicitly labeled as RESONANCE inference, not an industry standard
- [x] Alternative explanations preserved

## Implications

### For agent builders

Treat the action trajectory as a product surface. Design identity, approval, state, trace, retry/recovery and evidence together rather than as unrelated middleware.

### For QA

Move from testing isolated outputs toward testing **state graphs and evidence-bearing transitions**. A test should be able to say not only that an outcome was wrong, but which invariant failed, at which transition, under which causal path.

### For security

Least privilege remains necessary but insufficient. The meaningful unit is increasingly contextual authorization: actor + action + resource + state + phase + time.

### For science

The same model applies to AI-generated research workflows: hypothesis → evidence acquisition → transformation → analysis → claim → review. Provenance and reproducibility are trajectory properties.

### For Web3 and finance

Transactions already expose why state transitions, invariants, idempotency, receipts and replay protection matter. Agentic finance makes these constraints more urgent because the actor choosing transitions can now be probabilistic.

## What to build now

A useful MVP for a trust layer does not need to control everything.

Start with five primitives:

1. **Trajectory ID** — one identity for the whole action path.
2. **State transition record** — before, action, after.
3. **Invariant check** — machine-verifiable condition attached to the transition.
4. **Recovery contract** — retry, compensate, reconcile, escalate or stop.
5. **Evidence bundle** — trace + policy decision + artifact/receipt + verification result.

Then make failures reproducible.

The strongest trust system is not the one that says **"safe."**

It is the one that can say:

> **Here is the path. Here is what changed. Here is why it was allowed. Here is the invariant. Here is the recovery behavior. Here is the evidence. Check it yourself.**

## Primary sources

1. OpenAI Agents SDK — https://openai.github.io/openai-agents-python/
2. OpenAI Agents SDK Guardrails — https://openai.github.io/openai-agents-python/guardrails/
3. OpenAI Agents SDK Tracing — https://openai.github.io/openai-agents-python/ref/tracing/
4. A2A Protocol Specification — https://github.com/a2aproject/A2A/blob/main/docs/specification.md
5. OpenTelemetry Context Propagation — https://opentelemetry.io/docs/concepts/context-propagation/
6. Temporal Documentation — https://docs.temporal.io/
7. Sigstore / Cosign verification — https://docs.sigstore.dev/cosign/verifying/verify/
8. Sigstore Security Model — https://docs.sigstore.dev/about/security/

## Corrections

| Date | Correction | Reason |
|---|---|---|
| — | None | — |

---

**RESONANCE verification chain:**

**Signal → Claim → Source → Evidence → Cause → Timeline → Uncertainty → Verification → Implication → Action**
