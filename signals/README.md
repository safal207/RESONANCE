# Engineering Signals — Trust Portability & Verification Routing

This index records the engineering signals produced by the NEO REZONANS / Liminal trust and verification program.

It is also the **default journal entrypoint for engineering agents** that need to understand what has already been learned before choosing or creating a testing skill.

> **Journal = operational memory and routing guidance, not execution authority.**

An agent may use this index to recover current assumptions, verified corrections, falsification questions and available verification routes. Publication in RESONANCE does not grant credentials, production mutation, deployment, disclosure, financial, merge or external-action authority.

## Agent reading path

Before inventing a new method, read the current line in this order:

1. [`Article 05 — Fractal Causal Refactoring`](../issues/001-age-of-agents/articles/05-fractal-causal-refactoring.md)
2. [`Article 06 — The System That Refactored Itself`](../issues/001-age-of-agents/articles/06-the-system-that-refactored-itself.md)
3. [`Article 07 — Recover the Boundaries`](../issues/001-age-of-agents/articles/07-recover-the-boundaries.md)
4. [`Article 08 — Authority Has a History`](../issues/001-age-of-agents/articles/08-authority-has-a-history.md)
5. [`Signal 011 — Genesis / Historical Trust-Base Portability`](011-genesis-historical-trust-base-portability.md)
6. [`Signal 012 — Downstream Causal-State Portability`](012-downstream-causal-state-portability.md)
7. [`Signal 013 — Recursive Verification Skill Mesh / Journal-Driven Agent Routing`](013-recursive-verification-skill-mesh.md)
8. [`Signal 014 — Persistence Frontier / Native Consumer Acceptance Is Not Durable State`](014-persistence-frontier-native-consumer-acceptance.md)
9. [`Signal 015 — Durability Frontier / Commit ≠ Ack ≠ Retry Permission`](015-durability-frontier-commit-ack-retry.md)
10. [`Signal 016 — Meaning May Change / Trace Must Not`](016-meaning-may-change-trace-must-not.md)
11. [`Signal 017 — Authority Causality / Current Owner Gate`](017-authority-causality-current-owner-gate.md)
12. [`Signal 018 — Recovery Integrity / Projection ≠ Authority ≠ Continuation`](018-recovery-integrity-projection-authority-continuation.md)

Then inspect the **canonical skill registry and native repository contract** relevant to the target before execution.

Default loop:

```text
READ JOURNAL
   ↓
CLASSIFY DIVERGENCE
   ↓
ROUTE TO EXISTING SKILLS
   ↓
COLLECT + FALSIFY
   ↓
RUN NATIVE CONTRACTS
   ↓
VERIFY THE VERIFIER / PATH
   ↓
AUTHORIZE SEPARATELY
   ↓
PRESERVE CONFIRMED + REJECTED HISTORY
   ↓
WRITE NEW LEARNING BACK TO RESONANCE
   ↺
```

## Trust portability track

```text
physical location independence
        ↓
topology independence
        ↓
verifier-output independence
        ↓
verifier-implementation independence
        ↓
trust-root / signing-authority independence
        ↓
execution-provider / transport independence
        ↓
checkpoint source-producer / control-plane independence
        ↓
upstream rotation-producer / control-plane independence
        ↓
genesis / historical trust-base independence
        ↓
downstream causal-state portability
        ↓
recursive verification / skill routing
        ↓
native evidence handoff / persistence frontier
        ↓
durable local/test evidence / restart replay
        ↓
immutable source trace / bounded reinterpretation
        ↓
recovery integrity / projection-authority-continuation separation
```

## Verified portability milestones

- [`002 — Manifest-backed Witness Recovery`](002-manifest-backed-witness-recovery.md)
- [`003 — Evidence Topology Portability`](003-evidence-topology-portability.md)
- [`004 — Normalized Verification Receipt`](004-normalized-verification-receipt.md)
- [`005 — Independent Verifier Portability`](005-independent-verifier-portability.md)
- [`006 — Trust-Provider Portability`](006-trust-provider-portability.md)
- [`007 — Execution + Evidence-Transport Portability`](007-execution-transport-portability.md) — **VERIFIED 2026-08-13**
- [`009 — Source-Producer + Control-Plane Portability`](009-source-producer-control-plane-portability.md) — **VERIFIED 2026-08-13**
- [`010 — Upstream Rotation-Authority Portability`](010-upstream-rotation-authority-portability.md) — **VERIFIED 2026-08-13**
- [`011 — Genesis / Historical Trust-Base Portability`](011-genesis-historical-trust-base-portability.md) — **VERIFIED 2026-08-14**
- [`012 — Downstream Causal-State Portability`](012-downstream-causal-state-portability.md) — **VERIFIED 2026-08-14**

### Current portability lesson

Two independently rooted histories may carry distinct genesis, manifest, registry and provider identities while independently validating to the same normalized terminal authorization semantics.

Signal 012 then removes those historical identities from portable downstream checkpoint/witness identity when they are not semantically load-bearing.

```text
History A provenance ─┐
                      ├→ independent verification
History B provenance ─┘
                              ↓
                      semantic trust state
                              ↓
                       CausalStateRef
                              ↓
                  checkpoint → witness
```

Core rule:

> **Provenance must prove a causal state; provenance must not become the causal state's portable identity when multiple independently valid histories can establish the same semantics.**

This does not erase provenance. The raw histories remain separately addressable and independently auditable.

## FCRP / self-refactoring track

Article 06 records the working taxonomy produced by recursive self-tests:

1. **Verification Boundary Drift**
2. **Local Success / Parent Invariant Failure**
3. **Clock-Semantics Drift**
4. **Canonical Reality Drift**
5. **Temporal Contract Drift**
6. **Provenance / Compatibility Conflation**
7. **Parallel Semantic Authority**
8. **Recorded / Verified Provenance Gap**

Signal 013 extends the operational taxonomy with:

9. **Execution-Path Admissibility Drift** — correct-looking output reached through an invalid or unsupported agent path;
10. **Dependency-Resolution Identity Gap** — source revision is pinned but the executed dependency graph is not;
11. **Verification-Method Omission Drift** — a stronger canonical verification lane exists but the agent silently uses a weaker method.

Signal 014 adds:

12. **Persistence-Frontier Collapse** — consumer acceptance, write, durability and authority are compressed into one apparent transition;
13. **Logical-Operation Renaming Drift** — a downstream continuation silently replaces the real upstream logical-operation identity;
14. **Verifier-Invocation / Subject-Verdict Conflation** — a wrapper/tool invocation failure is reported as semantic rejection of the subject;
15. **Integration-Base / Causal-Ancestor Conflation** — one repository SHA is asked to serve both as historical causal anchor and current integration base after `main` advances.

Signal 015 adds:

16. **Commit / Acknowledgement Conflation** — a durable effect commits but a missing acknowledgement is treated as proof of no effect;
17. **Retry-Permission Inference Drift** — an error response is treated as permission to retry without reconciling possible committed state;
18. **Payload-Identity Idempotency Drift** — payload bytes define operation identity, allowing changed evidence to become an accidental second operation;
19. **Storage-Admission / Execution-Authority Conflation** — permission to persist evidence silently becomes permission to execute or mutate the represented subject;
20. **Evidence-Dimension / Protocol-Domain Conflation** — implementation evidence is silently promoted into protocol ontology without verifier support;
21. **Causal-Order Inversion** — a causal case places its claimed cause / First Meaningful Divergence after the symptom;
22. **Semantic-Tamper / Byte-Tamper Conflation** — a negative control changes irrelevant representation bytes while claiming to test semantic mutation;
23. **Pinned-Revision / Frozen-Default-Branch Conflation** — immutable capability pinning is implemented as a requirement that the dependency's default branch never advance.

Signal 016 adds:

24. **Source-Trace / Reflection-Identity Conflation** — derived interpretation identity replaces or obscures durable source identity;
25. **Durability / Truth Conflation** — persistence of evidence is treated as proof that the represented real-world claim is true;
26. **Domain-Adapter / Interpretation-Authority Conflation** — a new source type creates a second interpretation engine instead of projecting into the canonical core;
27. **Digest-Consistency / Semantic-Contract Conflation** — matching source bytes and digest are treated as sufficient despite incompatible authority semantics;
28. **Recorded-Time / Review-Time Conflation** — durable recording time is silently reused as downstream review time;
29. **Review-Unavailable / Review-Passed Conflation** — an unavailable or rate-limited reviewer is reported as approval.

Signal 017 adds:

30. **State-Freshness / Authority-Freshness Conflation** — current data is treated as current write permission;
31. **Checkpoint / Authority Resurrection** — stale recovered ownership silently regains mutation authority after restart or compaction;
32. **Lane-Identity / Active-Owner Conflation** — responsibility-lane membership is treated as proof that a specific actor still owns the lane;
33. **Timestamp / Authority-Predecessor Conflation** — last-write or latest timestamp is used to resolve an authority conflict without a causal handoff;
34. **Split-Authority Acceptance** — two active owners exist for the same resource/epoch and the system continues instead of failing closed;
35. **Authority-CAS / State-CAS Conflation** — one successful predecessor check is treated as sufficient when the action requires both.

Signal 018 adds:

36. **Projection / Authority Conflation** — a derived cache or UI projection becomes a second authority;
37. **Readable / Current Conflation** — parseable state is treated as current state;
38. **Missing / Stale / Corrupt Collapse** — distinct recovery states are all mapped to default initialization;
39. **Recovery / Continuation Conflation** — successful state reconstruction is treated as permission to resume execution;
40. **Evidence-Destructive Repair** — recovery destroys evidence required to diagnose or verify the failure;
41. **Generation-Split Acceptance** — incompatible logical generations are accepted because each store is locally valid;
42. **Recovered-Authority Resurrection** — a recovered session silently regains mutation authority without current-authority proof;
43. **Committed-Effect / Retry Ambiguity** — uncertain pre-crash side effects are replayed without reconciliation.

These names are a working engineering taxonomy, not an external standard. Apply them only when the exact causal shape is supported by evidence.

## Current verification mesh

The journal does not duplicate every skill specification. It routes agents to the current canonical skill registries.

Primary reusable engineering lanes currently include:

```text
causal-deep-audit
├ evidence-capture
├ causal-adjudication
├ exact-head-governance
├ replay-memory
├ product-impact
├ transition-next-action
├ cyber-causal-audit
│  └ websocket-redis-lifecycle
└ specialized lanes when applicable

LTP
└ ltp-agent-trace-auditor
```

Operational invariants:

```text
final output correct
        ≠
agent path admissible
```

```text
verifier invocation failed
        ≠
verified subject rejected
```

```text
commit
        ≠
acknowledgement
        ≠
retry permission
```

```text
source trace
        ≠
reflection
        ≠
truth
        ≠
authority
```

```text
state current
        ≠
authority current
```

```text
projection rebuildable
        ≠
execution continuation safe
```

Where both predecessor proofs are required:

```text
CAS(state)
AND
CAS(authority)
→ mutation admissible
```

A consequential agent run may require deterministic trace/replay verification even when its final object looks correct.

## Persistence and durability frontier

Signal 014 established:

```text
ProofPath native VALID
        ↓
LiminalDB-compatible AuditEvent artifact
        ↓
canonical LiminalDB dry-run PASS
        ↓
LTP strict inspect + replay PASS
        ↓
STOP BEFORE PERSISTENCE
```

SYSTEM-005 crossed the next boundary under an explicit `local_test_only` storage admission:

```text
ProofPath native VALID
        ↓
LiminalDB artifact acceptance
        ↓
separate local/test storage admission
        ↓
canonical ProofPathDurableLedger
        ↓
WAL append + sync
        ↓
process restart
        ↓
byte-exact replay
        ↓
same retry = ALREADY_PRESENT
semantic rewrite = IDEMPOTENCY_CONFLICT
        ↓
AfterSyncBeforeAck recovery = one durable effect
        ↓
LTP strict + replay PASS
        ↓
FCRP-SYSTEM-005 PASS
```

Current durability rule:

```text
proof
≠ truth
≠ consumer compatibility
≠ storage admission
≠ write
≠ acknowledgement
≠ retry permission
≠ execution authority
```

Canonical SYSTEM-005 identities:

```text
LiminalDB durable consumer
61b02fc81e0cb5cf1f1ed4658ecff58f683cb728

ContractGraph-QA independent verification
efe3efe637372815bef55ec3862c49cc69244b88

logical_operation_id
crossmint-public-example-001
```

Final independent SYSTEM-005 artifact:

`9215228292` — `sha256:01146320a1d04aaedb9bc12a76c71935b6b474620b372119a802207d841845e9`

The durable boundary remains **local/test only**. Do not promote it to production persistence authority.

## Interpretation frontier

SYSTEM-006 has now made the next edge native:

```text
LiminalDB durable evidence state
        ↓
exact durable replay
        ↓
canonical RINSE read-only source adapter
        ↓
source_trace.id = liminaldb-proof-durable:<record_hash>
        ↓
existing canonical reflection_graph v0.2
        ↓
SUPPORTED_WITH_LIMITS / ACCEPT_WITH_LIMITS
        ↓
REFLECTION_ONLY / execution_allowed=false
        ↓
semantic escalation negative control
        ↓
LTP strict + replay PASS
        ↓
FCRP-SYSTEM-006 PASS
```

Canonical SYSTEM-006 identities:

```text
RINSE durable-source consumer
3be0d2ceb1440641b141cdb80c82ed118e4186dd

ContractGraph-QA independent verification
b54173530c675083426137176cde0aed0b90853a

SYSTEM-006 exact-head subject
d52787bb67d9bc33047e922adeffa0192d96445b
```

Final independent SYSTEM-006 artifact:

`9215723726` — `sha256:a5b53c56bbb64d367b1b56ca602a0710de60f58ecc4ba9b7734782caa003c26c`

SYSTEM-006 proves that the durable record hash remains the source-trace identity, exact source bytes are not rewritten, the existing RINSE core alone creates reflection identity, semantic authority escalation is rejected even when the source-event digest is recomputed, and the result remains bounded and non-executable.

Parent invariant:

> **Meaning may change. Trace must not.**

## Finding lifecycle

Do not silently delete findings after a better test changes the conclusion.

Preserve an append-only history such as:

```text
DISCOVERY_SIGNAL
→ NEEDS_EVIDENCE
→ DEFECT_CANDIDATE
→ CONFIRMED
```

or:

```text
DEFECT_CANDIDATE
→ DISCRIMINATING_TEST
→ REJECTED_FALSE_POSITIVE
```

or:

```text
CONFIRMED
→ FIXED
→ RETESTED
→ REGRESSION_WATCH
```

or:

```text
PRIOR_INTERPRETATION
→ SUPERSEDED_BY_STRONGER_EVIDENCE
```

The losing hypothesis remains in the evidence ledger with the reason it lost. It must not continue to influence the current verdict silently.

Concrete preserved examples:

- SYSTEM-004's first red LTP lane did **not** establish an inadmissible path; the wrapper invocation failed before the trace was parsed.
- SYSTEM-005's early `cargo fmt --check` reds were **form-only** and did not reach durability tests.
- SYSTEM-005's first conflict-control issue was unstable error classification, not absence of the idempotency rule.
- SYSTEM-005's first independent FCRP red came from unsupported `VALID_TIME` / `TRANSACTION_TIME` protocol enum values; the native durable path had already passed.
- SYSTEM-005's next FCRP red came from a bad causal narrative that placed cause after symptom; the implementation path had again passed.
- a pre-review SYSTEM-005 FULL GREEN was superseded after valid review findings hardened the admission literal, semantic tamper test and LTP revision check; only the post-review artifact is canonical.
- SYSTEM-006 did not claim an external review passed when CodeRabbit was rate-limited; promotion used exact-head execution plus a bounded manual diff review and unchanged canonical base.

## External research signals

These entries record externally observable engineering feedback and architecture convergence. They are evidence of public technical interaction, **not** verification milestones, endorsements, partnerships or implementation certification.

- [`007 — External Research Impact via Semantic Mutation`](007-external-research-impact-semantic-mutation.md)
- [`008 — Independent Outcome-Provenance Convergence`](008-independent-outcome-provenance-convergence.md) — **OBSERVED 2026-08-13**
- [`018 — Recovery Integrity / Projection ≠ Authority ≠ Continuation`](018-recovery-integrity-projection-authority-continuation.md) — **PUBLIC FIXTURE + EXECUTABLE GENERATION MATRIX 2026-08-15**

Current external-research finding:

> **`source_class` answers how an outcome was established; it does not by itself answer who observed it or from what vantage.**

Decision provenance and outcome provenance remain separately inspectable.

## Current open system gate

**FCRP-SYSTEM-007 — RINSE Reflection → RESONANCE Operational Memory**

Falsifiable question:

> Can RESONANCE ingest the exact bounded SYSTEM-006 reflection as append-only operational memory while preserving its durable source record reference, RINSE reflection identity/digest, `REFLECTION_ONLY` authority, missing-evidence boundaries, uncertainty, correction/supersession history, and deterministic evidence/path replay — without promoting publication to truth or journal routing to execution authority?

Minimum independent lanes should include:

- exact canonical SYSTEM-006 evidence identity;
- durable source record reference preservation;
- RINSE reflection ID/digest preservation;
- `SUPPORTED_WITH_LIMITS` / `ACCEPT_WITH_LIMITS` / `REFLECTION_ONLY` preservation;
- missing-evidence and uncertainty preservation;
- append-only correction / supersession behavior;
- publication-versus-truth negative controls;
- journal-routing-versus-execution-authority negative controls;
- no mutation of durable source history or RINSE reflection history;
- deterministic journal/evidence serialization;
- LTP path admissibility;
- FCRP upward verification.

Current architectural target:

```text
RINSE REFLECTION_ONLY result
        ↓
RESONANCE operational memory
        ↓
append-only journal entry
        ↓
future-agent routing context
```

Critical rule:

> **Publication may preserve an interpretation. Publication must not promote it to truth or authority.**

## Skill creation rule

Do **not** create a new skill merely because a new problem appears.

First test whether an existing canonical skill already expresses the required invariant.

Create a new skill only when the missing method is recurring, clearly scoped, evidence-bounded, distinguishable from existing lanes, fail-closed, authority-explicit and backed by at least one negative regression.

Every new skill should link back to the journal signal that justified its creation.

This is how the system prevents **skill sprawl from becoming another form of Canonical Reality Drift**.

---

This index is descriptive and operationally useful, but not ambient authority. A milestone is marked **VERIFIED** only after its stated execution, recomputation and fail-closed evidence requirements are satisfied.
