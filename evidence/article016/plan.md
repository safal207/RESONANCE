# Article 016 — bounded reproduction plan

Recorded before execution on 2026-09-06.

## CausalSpine

- spineId: article016-native-seed-replay
- exactSubject: repository-owned CML approval-lineage demo and CGQA payment-recovery seed traces only
- subjectHash / source pins: CML `7a3a98c60a402d394e4d286da956823898454b8a`; CGQA `f861b934d77e64fd35f768e2a33bb4a00963bc19`
- scale: editorial reproduction; parent contract: Article 016 source verification
- purpose: determine whether existing checks distinguish the named positive and negative seed traces
- expected outcome: six expected classifications match; native diagnostic output is preserved
- forbidden inference: seed classifications establish an LLM hallucination rate, factual truth, runtime enforcement, source authenticity, production correctness, or exactly-once effects
- dependencies: pinned clean source checkouts, Python, PyYAML for CML
- typed time: synthetic record timestamps / ordered trace sequence; run date is observation metadata
- past/present/future: published examples → local replay → bounded article evidence
- symptom and refactor point: no newly reported defect; no production refactor
- mutation authority: no source changes to CML or CGQA; generated editorial evidence only
- authorizationRef: user request of 2026-09-06 to create a journal article about reducing hallucinations through our repositories
- stop condition: preserve results and report mismatches; do not repair an oracle to match expectations
- remaining debt: real model experiment, external replication, source completeness and live receiver observations

## Cases fixed before execution

| Input | Expected native outcome |
|---|---|
| CML make_invalid_trace | failed audit; policy and human-approval lineage findings |
| CML make_valid_trace | passed audit |
| CGQA pass_committed_stop.json | pass |
| CGQA pass_failed_retry_same_identity.json | pass |
| CGQA fail_retry_before_reconcile.json | fail; APR-001_UNRESOLVED_AMBIGUITY_FINANCIAL_ACTION |
| CGQA fail_changed_idempotency_after_failed_reconcile.json | fail; APR-004_IDEMPOTENCY_CHANGED_ON_RETRY |

The runner calls the existing evaluators, preserves full input and output, hashes source files, and compares two serial evaluations. It does not reimplement the evaluators. No model API, payment provider, external tool action, benchmark training, or live system is involved.

## Transition field

spineRef: article016-native-seed-replay. CGQA state dimensions are the authorized logical operation, concrete attempt, idempotency key, unresolved ambiguity set and recorded reconciliation outcome. Exercised paths are authorize → submit → ambiguous → committed → stop; authorize → submit → ambiguous → failed → retry; and the two existing negative paths (retry before resolution; changed retry key). CML records follow explicit parent and approval ancestors. The runner preserves the native results and full input paths; it does not add per-node state instrumentation.

The dangerous paths are present in supplied negative traces and detected after evaluation. This is observation of invalid traces, not runtime prevention. Real clocks, TTL, numeric value limits, storage, concurrency, crash recovery, provider semantics and external effect counts are outside these seeds.

## Capability scope

| Capability | Planned scope |
|---|---|
| Exact subject / artifact gate; preregistered plan; orientation | RUN: pins, clean checkouts, plan, named inputs |
| Native mapping / adapter review | RUN: direct native evaluator calls; no provider adapter |
| Safety; authorization; replay / idempotency; causal ancestry; negative control | RUN within the six existing seeds |
| Deterministic replay; trace integrity; evidence readiness | RUN: repeat outputs, preserve inputs, source hashes and native output |
| Durable evidence reopen / integrity | RUN: parse result and hash files before Git handoff |
| Verification debt; planning; meaning trajectory; watchpoints | RUN: retain explicit scope and debt; no new watchpoint promoted |
| Liveness / reachability; transition geometry; stateful / property search | NOT_RUN: no exhaustive search or independent operation-order experiment |
| Financial conservation; real temporal lifecycle; crash / recovery | NOT_APPLICABLE to a fixed synthetic trace-classification claim |
| Independent witness; temporal / external replication | NOT_RUN: local author-side replay only |
| Counterexample minimization; root-cause collapse; native regression; forward remediation | NOT_APPLICABLE: no new defect or repair claimed |
| Metamorphic / round-trip verification | NOT_RUN: same-input replay only |

Learning decision: NO_PROMOTION. This reproduces existing examples; it does not change upstream rules or establish a new generalized lesson.
