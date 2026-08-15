# Signal 018 — Autonomous Repository Maintenance Mesh

## Classification

**RESONANCE classification:** Proposed Engineering Signal — a maintenance mesh is a candidate operating layer for continuous, evidence-bound repository care.

**Status:** `BOUNDED_P2_4_VERIFIED_DESIGN`

This signal records an architectural direction, not an implemented autonomous service. The user-observed maintenance-loop pattern is an input hypothesis; no external experiment, merge ratio, production deployment, or model capability is independently claimed here.

## Thesis

AI-assisted maintenance becomes materially different from one-shot code generation when the unit of work is a durable routine with feedback:

```text
Observe → Diagnose → Patch → Verify → Outcome → Learn → Refactor Routine → Repeat
```

The system should maintain the codebase and the routines that maintain it. A routine is successful only when its exact target, causal explanation, patch, independent evidence, downstream outcome, and later routine-quality signal remain connected.

The proposed product shape is an **Autonomous Repository Maintenance Protocol**, implemented as a bounded **Maintenance Mesh** rather than one giant agent.

## Mesh members

| Routine | Primary observation | Typical contract / invariant | Default authority |
|---|---|---|---|
| Crash / failure hunter | CI, runtime failures, flaky tests | failure is reproduced or marked unconfirmed | draft PR only |
| Duplication hunter | repeated logic, schemas, adapters | semantic identity is preserved | draft PR only |
| Dead-code hunter | unreachable or unused paths | reachability claim is reversible and evidenced | draft PR only |
| Contract drift detector | API/schema/spec versus implementation | exact contract and implementation subjects are compared | draft PR only |
| Invariant guardian | causal, provenance, verification invariants | negative cases and parent invariants stay fail-closed | draft PR only |
| Dependency freshness agent | dependencies, actions, SDKs, pins | freshness and compatibility are exact-head checked | draft PR only |
| Evidence auditor | PR evidence and reproducibility | no ready verdict without bound replayable evidence | no merge authority |
| Cross-repository consistency agent | ProofPath, CML, LiminalDB, RINSE, LS, CGQA, RESONANCE | shared identities and contracts do not drift | draft PR only |
| Refactoring scout | first meaningful divergence | FCRP separates symptom, causal and refactor locations | draft PR only |
| Routine evaluator | routine outcomes over time | routine quality is measured and its rule is revisable | no code or merge authority |

The list is a topology, not ten independent semantic authorities. The Mesh needs one shared interpretation and evidence contract; routines are adapters and projections over it.

## Combined FCRP case

### Selected scale

- Selected level `L`: the organization-level repository maintenance control plane.
- Parent contract: RESONANCE makes maintenance claims inspectable, bounded and non-authorizing.
- Children: routines, repository adapters, patch branches, PRs, verifiers and outcome records.
- Cross-boundary dependencies: exact repository heads, workflow identities, evidence artifacts, contract subjects and outcome events.

This is the minimum containing system because a weak routine can fail in code, in its evidence, in its PR outcome, or in the rule that keeps generating the same weak PR.

### Idea(`L`)

**Purpose:** continuously reduce repository degradation while preserving causal identity, provenance and authority boundaries.

**Expected outcome:** a routine finds a bounded discrepancy, creates the smallest justified patch, proves the relevant invariant, publishes a traceable PR, and learns from the destination outcome.

**Invariants:** exact target identity; diagnosis distinct from patch intent; patch claims distinct from verification results; evidence, reflection, authorization, execution, persistence and observation remain separate; negative cases are first-class; outcomes are attributed to routine version and patch subject; a routine cannot silently authorize merge, deployment or external effects.

**Forbidden outcomes:** a green routine summary is treated as proof outside its boundary; stale or ambiguous heads are presented as current; evidence becomes authority; merge rate is optimized by hiding rejected or reverted PRs; a routine changes its own guardrails without an independently checked result.

### Past / Present / Future

**Past:** the trust spine was assembled as bounded contracts: exact-head governance, provider-neutral cargo, ancestry, negative-path matrix, evidence-bundle replay, and explicit evidence/authority/reflection separation.

**Present:** ContractGraph-QA PR #61 current verifier subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` has successful exact-head runs for the full chain, P1-3, occurrence portability, independent cross-repository replay, compatibility/migration replay and P2-4 maintenance-routine evaluation. P1-3 proves evidence-to-execution `BLOCK`, reflection-to-execution `BLOCK`, inferred authority `BLOCK`, and authority `HOLD` to execution `HOLD`; zero cases execute. Occurrence-binding evidence preserves semantic decision identity, authorization occurrence identity and consumption fact. P1-7 independently reconstructs those identities across frozen ProofPath, CML, LiminalDB, RINSE and RESONANCE subjects; P1-8 independently rejects unsupported schema revisions, route reorder and authority escalation while preserving source cargo by digest. P2-4 independently evaluates `contract_drift_detector` and `evidence_auditor` with exact outcome attribution and no merge authority.

**Future:** routine → exact target → minimal patch → independent verifier → PR outcome → routine-quality record → bounded routine refactor.

The current evidence is a bounded repository result; the future service is not implemented.

### Causal diff and First Meaningful Divergence

The likely system-level divergence is not one agent writing bad code. It is the absence of a common outcome-bound contract for maintenance routines. Without it, each hunter can emit a local success signal while losing causal scope, exact provenance, negative evidence or downstream outcome.

- Symptom location: fragmented maintenance PRs, inconsistent evidence and unclear routine quality.
- Causal location: no shared Maintenance Routine Contract joining observation, patch, verification, outcome and routine version.
- Refactor location: a provider-neutral routine-run and outcome manifest plus a Routine Evaluator, before multiplying specialized hunters.

**FMD confidence:** `strongly_supported_as_design_gap`, not a production root-cause finding. The discriminating probe is whether two different routines can emit the same machine-readable run record and whether an independent evaluator can reconstruct why their PRs were accepted, rejected, reverted or superseded.

## Proof logistics for a routine run

Each routine should deliver a bounded cargo package:

| Cargo | Required identity |
|---|---|
| routine identity | name, version, rule/config digest, capability lifecycle |
| target | repository, PR/branch, exact checked subject, base subject |
| observation | finding ID, scope, input digest, timestamp and clock type |
| causal case | Idea/Past/Present/Future, FMD, alternatives and confidence |
| patch | changed paths, patch digest and intended invariant |
| verification | local checks, independent checks, negative cases and replay result |
| outcome | PR state, CI, review, merge, revert or incident result |
| authority | `may_authorize`, `may_execute`, `may_mutate`, `side_effect_executed` |
| next step | smallest justified transition and stop condition |

A routine run is incomplete when load-bearing cargo is missing. `PASS` means only that the declared bounded routine contract passed; it does not mean the repository is globally healthy.

## Outcome feedback

The Routine Evaluator must retain outcomes such as accepted/merged, rejected/closed, changes requested, CI failure, stale before review, superseded, reverted, follow-up defect or incident.

Track routine precision, evidence completeness, independent-verification pass rate, rework, time-to-useful-result, false-positive rate, regression rate, stale-head rate and outcome-attribution quality. Merge rate alone is not a quality metric: a routine that avoids difficult findings can look successful while reducing system health.

## Graduated authority

1. `HUMAN_REQUIRED` — authorization/security, payment, destructive persistence and broad refactors.
2. `HUMAN_SPOT_CHECK` — low-risk, reversible changes with independent evidence and stable outcomes.
3. `AUTO_MERGE_AFTER_INDEPENDENT_VERIFICATION` — only for explicitly classified change classes with exact-head, contract, replay, negative-case and rollback evidence.

The last class is a future policy boundary, not current authorization. No human-review gate is part of the current bounded machine transition; merge, deployment, production persistence, external effects and security authorization remain separate gates.

## First bounded build

Implemented as a bounded P2-4 build: `Maintenance Routine Contract v0.1` with machine-readable routine-run manifests, exact target/source identities, evidence and outcome references, routine version and rule digest, independent verification, negative cases, outcome attribution, no hidden authority escalation, and a replayable Routine Evaluator fixture. ContractGraph-QA [workflow run #1](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737058) passed at exact subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` with receipt digest `sha256:50e4c0ebdf7428142e9951adbae983673ff76c76e8fce97f78cd8ee5087c254e` and witness digest `72df07094cce9975a9ffb631a65fe70561c30c3fa8b884b7f1a5afc07bf69b0c`.

Initial negative cases: stale target head; missing or unlisted evidence; changed contract subject; duplicate or contradictory finding; false-green verifier boundary; ambiguous occurrence binding; routine self-authorizes its own patch; outcome attributed to the wrong routine or patch subject.

Completion signal met: two bounded routines emit closed replayable run records, an independent evaluator reproduces the routine-quality result, outcome attribution is exact, and no routine output authorizes merge or external effects by itself.

## Safety boundary and non-claims

This signal does not claim that the Mesh is implemented, that any routine is autonomous in production, that a routine can merge/deploy/persist externally, that the user-provided maintenance experiment generalizes, or that FCRP v0.1 is a universal empirically validated standard.

The Maintenance Mesh is a proposed operating layer over the existing trust spine. Its first job is to make maintenance evidence easy to route, falsify, replay and improve while keeping code changes and authority decisions distinct.

## References

- RESONANCE Article 05, immutable FCRP v0.1 source: `389939d68350f5c0565fb814c6d599505ed8048b`.
- RESONANCE Article 06, immutable Self-Refactoring profile: `5b0e406410f8f1e42d18a969581b6af29032d360`.
- ContractGraph-QA current verifier subject: `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` (P2-4 exact-head evaluator receipt `sha256:50e4c0ebdf7428142e9951adbae983673ff76c76e8fce97f78cd8ee5087c254e`).