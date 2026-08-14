# Neo Resonance Repository Backlog

Status vocabulary: `PLANNED`, `IN_PROGRESS`, `NEEDS_EVIDENCE`, `VERIFIED`, `BLOCKED`.

This backlog is the implementation queue for the Neo Resonance trust system:

```text
CONTROL       LiminalOSAI
EVIDENCE      ProofPath
MEMORY        Causal-Memory-Layer
DURABILITY    LiminalDB
REFLECTION    RINSE
GOVERNANCE    LS
APPLICATION   ContractGraph-QA
JOURNAL       RESONANCE
```

The queue deliberately integrates existing capabilities before introducing new protocols.

## Current snapshot

The companion file `governance/neo-resonance-system-manifest.v0.1.json` records the observed default-branch heads used for this planning pass.

This is an observed snapshot, not a release approval. Mutable branch names, green badges, commit messages, and workflow definitions alone do not prove a current end-to-end pass.

Already present and not to be recreated:

- ProofPath capability canonicality and promotion contract — FCRP-SELF-005.
- CML Focus-Field reconciliation with canonical trust gates — FCRP-SELF-006.
- LiminalDB durable ProofPath ingestion and reopen semantics.
- RINSE durable ProofPath source adapter and reflection-only boundary.
- ContractGraph-QA FCRP-SYSTEM-005 durable ingestion evidence.
- ContractGraph-QA FCRP-SYSTEM-006 durable LiminalDB → RINSE reflection evidence.
- RESONANCE publication, evidence, market, and site-health contracts.
- LS exact-head PR risk-audit and state-projection recovery work.

## Prioritized delivery backlog

### P0 — trust spine

#### P0-1. Pin the cross-repository system manifest

- Status: `VERIFIED`
- Target: RESONANCE governance layer.
- Purpose: keep repository roles, exact observed heads, dependency edges, and evidence references in one inspectable place.
- Completion signal: manifest validates as JSON; every load-bearing edge names a source revision and a non-claim; refresh detects head movement instead of silently accepting it.
- Implemented guardrail: `governance/validate_neo_resonance_manifest.py` now emits a machine-readable report and explicit `PASS`, `HOLD`, `NOT_RUN`, or `INCOMPLETE` states; `.github/workflows/neo-resonance-p0-1-freshness.yml` runs the required remote check on the exact workflow subject.
- Remote observation at preparation time: all eight manifest heads matched through a read-only GitHub connector snapshot.
- Local direct `api.github.com` execution: `INCOMPLETE` in the current sandbox because the network request timed out; this is not treated as a remote PASS.
- Machine evidence: RESONANCE P0-1 workflow run #4 (`31811652205`) completed successfully at exact subject `c844f22a106a539d789677915e4ef3e88b5f6e46`; the uploaded freshness artifact is retained with SHA-256 `sha256:f50f03a5c0c8c5b8b413cec848280d32397bfa160e0b54b0fe5c6af502255491`.
- Scope decision: human review is `NOT_REQUIRED_FOR_CURRENT_SCOPE` for bounded advisory technical progression; this does not create a human approval claim.
- Next transition: P0-3 provider-neutral interoperability contract.

#### P0-2. Build FCRP-SYSTEM-007 full-chain conformance

- Status: `VERIFIED`
- Target: ContractGraph-QA, using the canonical repositories as external subjects.
- Chain: proposal/intent → ProofPath decision → CML causal record → LiminalDB durable write/reopen → RINSE reflection → independent ContractGraph-QA verification.
- Completion signal: one deterministic `logical_operation_id` travels through every stage; the final bundle is reproducible and proves reflection cannot authorize execution or mutate source truth.
- Negative cases: missing intent, replayed nonce, changed argument digest, stale dependency head, tampered durable record, and attempted reflection escalation.
- Evidence: bounded fixture `PASS` at ContractGraph-QA PR #61 subject `755618d57ace8c657ebd7d14dbfcead86c0fb593`, based on exact main `b54173530c675083426137176cde0aed0b90853a`; workflow run #4 (`31812128865`) completed successfully, with artifact digest `sha256:048475b4cc6c05e55de4025fa46763387bc34165d363ff1c4292ae6e9d935c56`.
- Exact external subjects: ProofPath `4a05ee31d7497979c2505dd55bfef08823302e24`, CML `2a649903693fc61a560ee056834127ada3120206`, LiminalDB `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728`, RINSE `3be0d2ceb1440641b141cdb80c82ed118e4186dd`.
- Adjacent control-plane observation: CaPU `babd2945046d2564e1110a76741827560c57fcca` is recorded separately as execution-control-only; it is not a seventh proof stage or a source of CML semantics.
- Scope boundary: this verifies the deterministic fixture, replay, durability/reopen/retry behavior, and reflection-only negative boundary; it does not authorize merge, deployment, production persistence, external effects, or a security claim.

#### P0-3. Publish one provider-neutral interoperability contract

- Status: `VERIFIED`
- Target: shared documentation/schema boundary across ProofPath, CML, LiminalDB, RINSE, and ContractGraph-QA.
- Minimum spine: `logical_operation_id`, execution/attempt ID, parent cause, intent, resolved target, expected invariants, observed outcome, phase, valid/transaction time, recovery state, verification/evidence references.
- Completion signal: the same fixture can be serialized, stored, reopened, reflected, and independently verified without semantic renaming.
- Implemented boundary: `governance/provider-neutral-interoperability-contract.v0.1.schema.json`, canonical fixture, explicit native field maps, CaPU adjacent-plane declaration, and dependency-free validator/replay runner.
- Machine evidence: workflow run #2 (`31811652207`) passed at exact RESONANCE subject `c844f22a106a539d789677915e4ef3e88b5f6e46`; artifact `resonance-p0-3-interoperability-31811652207-1` is retained with digest `sha256:d8a6c51ace8f3d5a2c6b99b6f6b7e134235af4b5ec61e52d6056e5149ef0469`. The contract source remains pinned to `4401f7c171311a41afc2d8cce57275118746a8c5`.
- Result: six route events, stored/reopened byte match `true`, independent verification `PASS`, reflection `REFLECTION_ONLY`, and six negative cases `REJECTED`; canonical fixture digest `sha256:3bd90b2e1e7551335c7ed36b8112b44585f63bf18125bc80b672aa3417261a72`.
- Scope boundary: this verifies the provider-neutral contract and bounded replay lifecycle; it does not assert live runtime integration, production persistence, merge approval, deployment or security certification.
- Next transition: P0-4 cross-repository freshness and ancestry gate.

#### P0-4. Add a cross-repository freshness and ancestry gate

- Status: `VERIFIED`
- Target: ContractGraph-QA system workflows plus the manifest.
- Purpose: distinguish an exact current subject from a stale ancestor or a mutable `main` observation.
- Completion signal: initial and final head checks, expected ancestry, workflow identity, and artifact subject are reported as `PASS`, `HOLD`, `NOT_RUN`, or `INCOMPLETE`; no unknown becomes green.
- Implementation: `tools/ancestry_gate.py`, its unit tests, the `FCRP P0-4 — Exact Subject and Ancestry Gate` workflow, and the bounded design note in ContractGraph-QA.
- Machine evidence: P0-4 workflow run #1 (`31812129009`) passed at exact subject `755618d57ace8c657ebd7d14dbfcead86c0fb593`; all five checks (`initial_subject`, `final_subject`, `ancestry`, `workflow_identity`, `artifact_subject`) were `PASS`, with unknown policy `unknown_never_becomes_pass`. Artifact digest: `sha256:528ed18d2e4479279a215233009222e13c79a7019157cfb58ff5ec35836433b2`.
- Rebound SYSTEM-007 evidence: full-chain run #4 (`31812128865`) passed with 17/17 substantive steps and artifact digest `sha256:048475b4cc6c05e55de4025fa46763387bc34165d363ff1c4292ae6e9d935c56`.
- Scope boundary: the gate establishes evidence identity and ancestry for bounded fixtures; it does not authorize merge, deployment, production persistence, external effects, or security decisions.
- Next transition: P1-1 standard negative-path matrix.

### P1 — safety and repeatability

#### P1-1. Standardize the negative-path matrix

- Status: `PLANNED`
- Target: ProofPath and ContractGraph-QA system fixtures.
- Include: missing intent/parent/nonce, replay, expiry, scope violation, secret egress, changed arguments, fan-out exhaustion, tampered evidence, and untrusted memory/tool output.
- Completion signal: each case has an expected decision, `side_effect_executed=false` where applicable, and a replayable evidence reference.

#### P1-2. Unify evidence-bundle and replay manifests

- Status: `PLANNED`
- Target: LiminalDB, RINSE, ContractGraph-QA, and LS.
- Completion signal: every load-bearing artifact has path, byte size, SHA-256, source revision, role, and collection timestamps; duplicate or unlisted artifacts fail verification.

#### P1-3. Separate evidence, authority, and reflection in every adapter

- Status: `NEEDS_EVIDENCE`
- Target: all adapters and examples.
- Completion signal: a reflection, schema pass, or valid evidence bundle cannot by itself authorize an action; a negative escalation test proves this.

#### P1-4. Add independent cross-repo replay

- Status: `PLANNED`
- Target: ContractGraph-QA.
- Completion signal: a second verifier rebuilds the final result from raw inputs and exact revisions without trusting the producer's summary.

#### P1-5. Create compatibility and migration policy

- Status: `PLANNED`
- Target: ProofPath/LiminalDB/RINSE integration.
- Completion signal: old and new schema versions, rejection behavior, and recovery paths are explicit and tested.

### P2 — product and operating leverage

#### P2-1. Measure cost and latency of the trust spine

- Status: `PLANNED`
- Target: system benchmarks.
- Measure: verification time, storage cost, replay cost, failure-detection rate, false positives/negatives, and evidence completeness.
- Non-claim: synthetic fixtures do not prove production security or business impact.

#### P2-2. Make the architecture map executable for contributors

- Status: `PLANNED`
- Target: RESONANCE and repository READMEs.
- Completion signal: a new contributor can identify the canonical repository, current capability, verification command, and next open gap from one route.

#### P2-3. Connect verified capabilities to real market evidence

- Status: `PLANNED`
- Target: RESONANCE Market OS.
- Completion signal: external workflow evidence, repeated problem clusters, pilot candidates, and paid requests remain separate from synthetic examples and internal demos.

## Operating rule

For every item:

1. freeze target and source identity;
2. capture current evidence;
3. state competing explanations and non-claims;
4. make one smallest bounded change;
5. run the negative case;
6. verify the destination state;
7. update the manifest and backlog.

Do not merge, deploy, disclose, or call a capability production-ready from this backlog alone.
