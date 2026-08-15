# RESONANCE — Issue 001

# THE AGE OF AGENTS

**How AI is moving from answering questions to acting in the world.**

## Thesis

The defining shift in AI is no longer only better generation.

AI systems are becoming actors: they plan, call tools, write and execute code, operate software, move information, coordinate tasks, interact with financial and physical infrastructure, and recover from failure.

This changes the central question from:

> What can a model say?

To:

> What can an intelligent system do, under what constraints, with what evidence, and who can trust the result?

Issue 001 maps this transition.

## Published features

1. [`The Agentic Turn`](articles/01-the-agentic-turn.md)
2. [`The Missing Trust Layer`](articles/02-the-missing-trust-layer.md)
3. [`When Agents Fail`](articles/03-when-agents-fail.md)
4. [`Who Saw the Outcome? — The Missing Provenance Layer After an AI Agent Acts`](articles/04-who-saw-the-outcome.md) — **published 2026-08-13**
5. [`Fractal Causal Refactoring — как AI-агенту искать не ошибку, а точку расхождения системы с её идеей`](articles/05-fractal-causal-refactoring.md) — **published 2026-08-14**
6. [`The System That Refactored Itself — что FCRP нашёл, когда мы применили его к собственной AI trust infrastructure`](articles/06-the-system-that-refactored-itself.md) — **published 2026-08-14**
7. [`Recover the Boundaries — почему AI-агенту после compaction недостаточно просто «вспомнить задачу»`](articles/07-recover-the-boundaries.md) — **published 2026-08-15**
8. [`Authority Has a History — почему право AI-агента действовать тоже имеет причинное состояние`](articles/08-authority-has-a-history.md) — **published 2026-08-15**

The fourth feature extends the trust question beyond pre-action authorization: a consequential outcome needs its own observer identity, vantage and evidence so decision provenance and outcome provenance remain separately inspectable.

The fifth feature proposes a recursive causal-navigation protocol for autonomous engineering agents: choose the right system scale, recover the level's idea across past/present/future, find the first meaningful divergence, select a high-leverage refactor point, simulate impact, and verify affected parent invariants after the change.

The sixth feature reports what happened after that protocol became executable and was applied to its own trust-infrastructure repositories. The self-tests exposed verification-boundary drift, local-success/parent-invariant failure, clock-semantics drift, canonical-reality drift, temporal contract drift, provenance/compatibility conflation, and parallel semantic authority — turning FCRP from a conceptual debugging model into a broader repository and verification governance experiment.

The seventh feature isolates a stricter continuation failure mode: an agent can reread durable state after compaction and still continue incorrectly if responsibility lanes, ownership, mutation scope, done conditions or latest rulings are reconstructed under the wrong topology. It introduces Responsibility-Lane Continuity and an executable fail-closed conformance gate for detecting lane conflation.

The eighth feature makes authority itself causal: static ownership is the cheapest case, dynamic handoff requires a versioned authority predecessor, and genuine concurrent mutation may require both state CAS and authority CAS. Its core invariant is that correct knowledge does not imply current authority.

## Agent operating line

For engineering agents, this issue now has a canonical operational continuation in the Engineering Signals journal.

**Start here:** [`Engineering Signals — Trust Portability & Verification Routing`](../../signals/README.md)

The intended reading / execution loop is:

```text
Article 05 — FCRP origin
        ↓
Article 06 — self-refactoring lessons
        ↓
Article 07 — recover state + responsibility boundaries
        ↓
Article 08 — prove current causal authority
        ↓
Signal 011 — independent historical trust-base portability
        ↓
Signal 012 — downstream causal-state portability
        ↓
Signal 013 — recursive verification skill mesh
        ↓
Signal 014 — native consumer acceptance / persistence frontier
        ↓
Signal 015 — durability frontier / commit ≠ ack ≠ retry permission
        ↓
Signal 016 — meaning may change / trace must not
        ↓
canonical skill registry + native repository contract
        ↓
smallest falsifiable test
        ↓
result / correction / rejection written back to RESONANCE
```

Operational rules carried by this line:

- read the current journal state before inventing a new test method;
- route to existing canonical skills before creating a new skill;
- `output correct` does not imply `agent path admissible`;
- recovered state does not imply recovered responsibility topology;
- a generated summary is information, not automatic execution authority;
- a post-compaction material action must remain attributable to a valid responsibility lane;
- cross-lane mutation and contradictory lane sources must fail closed;
- correct state knowledge does not imply current mutation authority;
- authority transfer/revocation must supersede stale checkpoints and cached ownership;
- state predecessor and authority predecessor are independent proofs; where both are required, failure of either blocks mutation;
- split active authority for the same resource/epoch must fail closed rather than be resolved by timestamp alone;
- `verifier invocation failed` does not imply `verified subject rejected`;
- `repository head` does not necessarily equal `capability identity`;
- an immutable capability pin does not necessarily require the dependency's default branch head to remain frozen;
- `source commit` does not necessarily bind the executed dependency graph;
- `historically verified` does not imply `currently applicable`;
- provenance may prove semantic state without becoming semantic state identity;
- a native downstream continuation should inherit the actual upstream `logical_operation_id` unless an explicit mapping contract exists;
- consumer compatibility does not imply storage admission;
- storage admission does not imply execution authority;
- `commit` does not imply `acknowledgement`, and acknowledgement failure does not imply safe retry permission;
- idempotency identity belongs to the logical operation rather than payload bytes;
- semantic-tamper tests must mutate semantic content, not merely representation noise;
- implementation evidence may be valid while the causal case describing it is invalid;
- evidence dimensions do not become protocol enum values merely because an implementation exposes them;
- durable source identity must remain distinct from reflection identity;
- a new source type must not silently create a second interpretation authority;
- matching bytes/digests do not replace semantic contract validation;
- `valid_time`, durable `recorded_time`, and downstream `reviewed_time` remain distinct facts;
- `review unavailable` does not mean `review passed`;
- evidence, readiness, memory, durable storage, interpretation and publication do not grant execution authority;
- rejected, not-reproduced, fixed and superseded findings remain in append-only history rather than silently disappearing;
- repository advancement during an experiment requires reconciliation/revalidation rather than suppression of stale-base evidence;
- a green run superseded by valid review corrections must be re-executed before promotion.

## Current verified system boundary

The local/test persistence segment is canonical:

```text
ProofPath native verification
        ↓
LiminalDB-compatible AuditEvent artifact
        ↓
canonical LiminalDB dry-run validation
        ↓
separate local/test storage admission
        ↓
canonical durable WAL append + sync
        ↓
process restart / byte-exact replay
        ↓
idempotent retry + semantic-conflict rejection
        ↓
AfterSyncBeforeAck recovery
        ↓
FCRP-SYSTEM-005 PASS
```

SYSTEM-006 has now made the downstream interpretation edge native as well:

```text
LiminalDB durable evidence state
        ↓
exact durable replay
        ↓
canonical RINSE read-only source adapter
        ↓
immutable source trace bound to durable record hash
        ↓
existing canonical reflection_graph v0.2
        ↓
SUPPORTED_WITH_LIMITS / ACCEPT_WITH_LIMITS
        ↓
REFLECTION_ONLY / execution_allowed=false
        ↓
semantic authority-escalation rejection
        ↓
LTP strict inspect + deterministic replay
        ↓
FCRP-SYSTEM-006 PASS
```

Canonical implementation evidence:

```text
LiminalDB durable consumer
61b02fc81e0cb5cf1f1ed4658ecff58f683cb728

ContractGraph-QA independent SYSTEM-005 proof
efe3efe637372815bef55ec3862c49cc69244b88

RINSE durable-source consumer
3be0d2ceb1440641b141cdb80c82ed118e4186dd

ContractGraph-QA independent SYSTEM-006 proof
b54173530c675083426137176cde0aed0b90853a
```

Independent artifacts:

```text
SYSTEM-005
9215228292
sha256:01146320a1d04aaedb9bc12a76c71935b6b474620b372119a802207d841845e9

SYSTEM-006
9215723726
sha256:a5b53c56bbb64d367b1b56ca602a0710de60f58ecc4ba9b7734782caa003c26c
```

The qualifier **local/test** remains load-bearing. Issue 001 must not describe these results as production persistence or execution authority.

The interpretation parent invariant is:

> **Meaning may change. Trace must not.**

The durable record remains the source-trace identity. The RINSE reflection is a derived, deterministic, bounded interpretation — not a replacement source, not truth, and not permission to execute.

## Current open system question

**FCRP-SYSTEM-007 — RINSE Reflection → RESONANCE Operational Memory**

```text
RINSE REFLECTION_ONLY result
        ↓
RESONANCE operational memory
        ↓
append-only journal entry
        ↓
future-agent routing context
```

SYSTEM-007 must preserve the durable source reference, RINSE reflection ID/digest, `SUPPORTED_WITH_LIMITS` / `REFLECTION_ONLY` semantics, uncertainty and missing-evidence boundaries, and append-only correction/supersession history.

The critical rule is:

> **Publication may preserve an interpretation. Publication must not promote it to truth or authority.**

Production persistence authorization remains a separate frontier. SYSTEM-007 does not silently solve it.

The journal is the **operational memory / routing layer**. Skill specifications and native repository contracts remain the execution / verification layer. Authorization remains separate.

## Editorial questions

- What technically distinguishes an agent from a chatbot?
- Which capabilities are real today and which are mostly narrative?
- What infrastructure becomes necessary when AI can act?
- How do identity, permissions, memory, payments, provenance, and recovery change?
- What new failure modes appear?
- How should humans verify actions performed by agents?
- Which markets and companies are likely to emerge around agent identity, security, evaluation, payments, memory, observability, and verification?
- How does human work change when intelligence becomes an operational layer?

## Planned features

### 1. The Agent Economy
A map of the emerging economic stack around autonomous and semi-autonomous AI systems.

### 2. From Chat to Action
The architectural transition from language models to tool-using, stateful systems.

### 3. Trust Is the Missing Layer
Why capability without verification, provenance, permissions, recovery, and evidence is insufficient for high-stakes agents.

### 4. The Infrastructure Race
Compute, accelerators, inference, memory, orchestration, and the systems beneath agentic AI.

### 5. When Agents Fail
A taxonomy of state, permission, coordination, recovery, timing, and verification failures.

### 6. Humans in the Loop — and Beyond It
Where human oversight works, where it fails, and how the human role may shift from operator to governor.

### 7. The New Startup Map
Companies and opportunities emerging across agent identity, security, evaluation, payments, memory, observability, and verification.

### 8. Human + AI Flow
How intelligent systems may change attention, learning, creativity, fatigue, and the design of work.

### 9. Future Map: 2027–2030
A scenario-based view of plausible agent adoption paths, bottlenecks, and discontinuities.

### 10. What Should You Build Now?
A practical synthesis for builders, researchers, operators, and investors.

## Evidence package

Major stories in this issue should preserve, where possible:

```text
claim
├── primary sources
├── evidence
├── timeline
├── causal model
├── uncertainty
├── counter-evidence
├── verification notes
└── implications
```

## Status

**Founding outline — v0.1**

The table of contents is intentionally provisional. Articles may be added, merged, or removed as reporting and evidence develop.

---

**RESONANCE Issue 001 — THE AGE OF AGENTS**
