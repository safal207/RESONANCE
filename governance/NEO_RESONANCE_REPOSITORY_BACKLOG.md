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
- Scope decision: no human-review gate is used for this bounded machine transition; this does not create a merge, deployment, production, or security approval claim.
- Next transition: P0-3 provider-neutral interoperability contract.

#### P0-2. Build FCRP-SYSTEM-007 full-chain conformance

- Status: `VERIFIED`
- Target: ContractGraph-QA, using the canonical repositories as external subjects.
- Chain: proposal/intent → ProofPath decision → CML causal record → LiminalDB durable write/reopen → RINSE reflection → independent ContractGraph-QA verification.
- Completion signal: one deterministic `logical_operation_id` travels through every stage; the final bundle is reproducible and proves reflection cannot authorize execution or mutate source truth.
- Negative cases: missing intent, replayed nonce, changed argument digest, stale dependency head, tampered durable record, and attempted reflection escalation.
- Evidence: bounded fixture `PASS` at frozen source subject `6e51cbb176f6d891b758e3026744d1d4c4c5727a`, verified by current PR #61 runtime subject `eac4dae1f9add44050def7579a9ea392bd8199cd`, based on exact main `b54173530c675083426137176cde0aed0b90853a`; workflow run #18 (`31876267048`) completed successfully, with artifact digest `sha256:eed43f9de12ab519c2ac907cc5a93c3283def10790f2b75b99006a8f37e26384`.
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
- Machine evidence: P0-4 workflow run #15 (`31876267037`) passed at current verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`; all five checks (`initial_subject`, `final_subject`, `ancestry`, `workflow_identity`, `artifact_subject`) were `PASS`, with unknown policy `unknown_never_becomes_pass`. Artifact digest: `sha256:3a4f186c689aaf21a41d17c9f4bd3b9c214dc2b748681107c3bf0d52b9597821`.
- Rebound SYSTEM-007 evidence: full-chain run #18 (`31876267048`) passed at current verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd` with 17/17 substantive steps and artifact digest `sha256:eed43f9de12ab519c2ac907cc5a93c3283def10790f2b75b99006a8f37e26384`.
- Scope boundary: the gate establishes evidence identity and ancestry for bounded fixtures; it does not authorize merge, deployment, production persistence, external effects, or security decisions.
- Next transition: P1-1 standard negative-path matrix.

### P1 — safety and repeatability

#### P1-1. Standardize the negative-path matrix

- Status: `VERIFIED`
- Target: ProofPath and ContractGraph-QA system fixtures.
- Include: missing intent/parent/nonce, replay, expiry, scope violation, secret egress, changed arguments, fan-out exhaustion, tampered evidence, and untrusted memory/tool output.
- Completion signal: each case has an expected decision, `side_effect_executed=false` where applicable, and a replayable evidence reference.
- Implementation: ContractGraph-QA `tools/negative_path_matrix.py`, focused tests, the `FCRP P1-1 — Negative-Path Matrix` workflow, and the bounded design note `docs/NEO_REZONANS_P1_1_NEGATIVE_PATH_MATRIX_V0_1.md`.
- Machine evidence: workflow run #14 (`31876267080`) passed at current verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`; 16/16 cases were replay-stable and evidence-complete, with 15 `BLOCK` negative cases, one `ACCEPT` policy-eligible dry-run control, and zero executed cases. Artifact digest: `sha256:f91fc7ca2086672469defb31141dd0ccaa919e58f5cff2c14b87d0b094b27231`.
- ProofPath pin: `4a05ee31d7497979c2505dd55bfef08823302e24`; the matrix is provider-neutral deterministic policy evaluation and does not claim live runtime integration.
- Safety boundary: all authority flags are `false`; no executor, provider, wallet, real secret, network side effect, mutation, merge, deployment, production persistence, or security authorization is involved. `BLOCK` and `HOLD` remain fail-closed.
- Next transition: P1-2 unify evidence-bundle and replay manifests.

#### P1-2. Unify evidence-bundle and replay manifests

- Status: `VERIFIED`
- Target: LiminalDB, RINSE, ContractGraph-QA, and LS.
- Completion signal: every load-bearing artifact has path, byte size, SHA-256, source revision, role, and collection timestamps; duplicate or unlisted artifacts fail verification.
- Implementation: ContractGraph-QA `schemas/evidence-bundle-replay-manifest.v0.1.schema.json`, `tools/evidence_bundle_replay_manifest.py`, the canonical four-subject fixture under `fixtures/p1-2/`, focused tests, the `FCRP P1-2 — Evidence-Bundle and Replay Manifest` workflow, and the bounded design note `docs/NEO_REZONANS_P1_2_EVIDENCE_BUNDLE_REPLAY_MANIFEST_V0_1.md`.
- Machine evidence: workflow run #13 (`31876267027`) passed at runtime verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`; the bundle contains four exact component subjects, six artifacts, six replay steps and 1,410 bytes. Replay is `SAME_RESULT`, membership and SHA-256 checks pass, and all authority flags remain `false`. Artifact digest: `sha256:2ed594507b26c92f35bb6e1aad135e6f3f638a7ddf6218dcde492286a8be3544`.
- Pinned bundle subjects: LiminalDB `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728`, RINSE `3be0d2ceb1440641b141cdb80c82ed118e4186dd`, ContractGraph-QA fixture `fcd5e88655eedd3e4e4d3944bb133a8e2c8b0d8e`, LS `fa7e3aba4ff9154856fa7d27c92f702137819ac1`.
- Scope boundary: the verifier proves byte integrity, bundle membership, exact source pins and replay references for a bounded fixture; it does not assert live runtime integration, production safety, merge approval, deployment or security certification.

#### P1-3. Separate evidence, authority, and reflection in every adapter

- Status: `VERIFIED`
- Target: ContractGraph-QA authority/reflection boundary fixture, with the route rule carried into every adapter and example.
- Completion signal: a reflection, schema pass, or valid evidence bundle cannot by itself authorize an action; a negative escalation test proves this.
- Implementation: ContractGraph-QA `schemas/authority-reflection-boundary.v0.1.schema.json`, `tools/authority_reflection_boundary.py`, the canonical three-lane fixture under `fixtures/p1-3/`, focused tests, the `FCRP P1-3 — Evidence, Authority and Reflection Boundary` workflow, and the bounded design note `docs/NEO_REZONANS_P1_3_AUTHORITY_REFLECTION_BOUNDARY_V0_1.md`.
- Machine evidence: workflow run #12 (`31876267042`) passed at runtime verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`, based on exact PR #61 base `b54173530c675083426137176cde0aed0b90853a`; five source subjects, three artifacts, 1,254 bytes, four cases, replay `SAME_RESULT`, three `BLOCK`, one `HOLD`, and zero executed cases. Artifact digest: `sha256:9eaac81d0163435a9e08fc1b6f020b8ca83fd1182a4b30e6f3c58514576b21f0`.
- Boundary result: evidence has `may_authorize=false`; reflection is `REFLECTION_ONLY`, cannot authorize or mutate source; authority is a separate explicit control record and the fixture remains `HOLD`. All side-effect flags are `false`.
- Identity rule: runtime verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd` and frozen ContractGraph-QA fixture source subject `6e51cbb176f6d891b758e3026744d1d4c4c5727a` are recorded separately; a source subject is cargo provenance, not the verifier checkout identity.
- Historical fail-closed check: first workflow attempt #1 (`31873466160`) returned `HOLD` while the verifier/fixture identities were incorrectly conflated; the fix separates them and preserves both identities in evidence.
- Scope boundary: this proves a bounded negative escalation boundary and replayable lane separation; it does not authorize merge, deployment, production persistence, external effects, or security decisions.
- Next transition: P1-4/P1-5/P1-6 occurrence portability.

#### P1-4/P1-5/P1-6. Preserve authorization occurrence across adapters

- Status: `VERIFIED`
- Target: ProofPath → CML → LiminalDB → RINSE → ContractGraph-QA.
- Purpose: preserve one concrete authorization occurrence across every adapter, prevent duplicate or rebound consumption under race/replay, and emit a receipt bound to the exact consumer and action.
- Completion signal: `decision_ref`, `cites_event_id`, action/authority fields, route fingerprint, request ID and consumption receipt remain exact and replayable; exactly one concurrent consumer can consume the occurrence.
- Implementation: ContractGraph-QA `contractgraph_qa/occurrence_portability.py`, `tools/tests/test_occurrence_portability.py`, `tools/occurrence_portability_matrix.py`, and `docs/NEO_REZONANS_P1_4_P1_6_OCCURRENCE_PORTABILITY_V0_1.md`.
- Machine evidence: occurrence portability [run #2](https://github.com/safal207/ContractGraph-QA/actions/runs/31876267011) passed at verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`; artifact `fcrp-p1-4-6-occurrence-portability-31876267011-1`, digest `sha256:7659839c5d29c5c91919b3bbca3b0ba22879f9bde8633f6beec613ad35c3c34c`, artifact size 1,806 bytes.
- Matrix boundary: expired, revoked, not-yet-valid, action mismatch, concurrent compare-and-set race, same-request replay, already-consumed, and request-ID rebound cases remain fail-closed; `side_effects_executed=false` and `production_ledger_mutated=false`.
- Scope boundary: this is a provider-neutral conformance/reference layer; it does not claim a production ledger migration, CrewAI adoption, deployment, external effects, merge approval, or security authorization.
- Next transition: P1-4/P1-5/P1-6 occurrence portability.

#### P1-7. Add independent cross-repo replay

- Status: `VERIFIED`
- Target: ContractGraph-QA as an independent verifier over the Neo Resonance proof subjects.
- Purpose: rebuild the final result from raw inputs and exact repository revisions without importing the producer implementation or trusting its summary.
- Completion signal: exact occurrence, route fingerprint, ConsumptionReceipt, cross-repository subject fingerprint and independent witness are reconstructed; negative tamper cases fail closed.
- Implementation: ContractGraph-QA `tools/independent_cross_repo_replay.py`, `tools/tests/test_independent_cross_repo_replay.py`, pinned fixtures under `benchmarks/global-p1-7/`, workflow `.github/workflows/fcrp-global-p1-7-independent-cross-repo-replay.yml`, and `docs/GLOBAL_P1_7_INDEPENDENT_CROSS_REPO_REPLAY.md`.
- Machine evidence: [workflow run #1](https://github.com/safal207/ContractGraph-QA/actions/runs/31876267085) passed at verifier subject `eac4dae1f9add44050def7579a9ea392bd8199cd`; all 11 steps completed successfully; artifact `fcrp-p1-7-independent-cross-repo-replay-31876267085-1`, 2,492 bytes, digest `sha256:95356f72678454b6f508c13d15657156b993c841a64fd3c6d99cbd738448c7a9`.
- Independent result: `decision_ref=decision-A`, `cites_event_id=evt-42`, route fingerprint `fee0b69553abc156b77ad446c3cda8c7f50bbf0efc2cd3aafa75a279016f7930`, receipt digest `690e4852db587c8aa97673ea3b93c5512ffb052ef15de7153604d3a2ff72d72a`, six exact subject records.
- Frozen external source subjects: ProofPath `4a05ee31d7497979c2505dd55bfef08823302e24`, CML `2a649903693fc61a560ee056834127ada3120206`, LiminalDB `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728`, RINSE `3be0d2ceb1440641b141cdb80c82ed118e4186dd`, and RESONANCE `85c3baea0a551751263ef563a3dd1c75492f57ae`; current verifier subject is `eac4dae1f9add44050def7579a9ea392bd8199cd`.
- Negative cases: route reorder, missing occurrence ID ambiguity, receipt tamper, pinned-revision tamper, and raw-subject worktree tamper all failed closed; `side_effects_executed=false`, `production_ledger_mutated=false`.
- Scope boundary: independent bounded replay only; it does not authorize merge, deployment, production persistence, external effects, security decisions or upstream framework adoption.
- Next transition: P1-8 compatibility and migration policy.

#### P1-8. Create compatibility and migration policy

- Status: `PLANNED`
- Target: ProofPath/LiminalDB/RINSE integration.
- Completion signal: old and new schema versions, rejection behavior, recovery paths and cross-repository compatibility receipts are explicit and tested.
- Dependency: consume P1-7 exact-subject replay as the source identity boundary.

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

#### P2-4. Build the Maintenance Routine Contract and Routine Evaluator

- Status: `PLANNED`
- Target: RESONANCE operating layer over ContractGraph-QA and the cross-repository trust spine.
- Purpose: make repository-maintenance routines durable, evidence-bound, outcome-aware and able to improve their own rules without becoming a second authority.
- Design signal: `signals/018-autonomous-repository-maintenance-mesh.md`.
- FCRP framing: selected level is the repository-maintenance control plane; the likely first meaningful divergence is the missing shared contract joining observation, diagnosis, patch, independent verification, PR outcome and routine version.
- Completion signal: two bounded routines emit closed replayable run records; an independent evaluator reproduces routine-quality results; outcome attribution is exact; no routine output authorizes merge, deployment, production persistence or external effects.
- Initial negative cases: stale target head, missing/unlisted evidence, changed contract subject, duplicate finding, false-green verifier boundary, ambiguous occurrence binding, routine self-authorization, and wrong outcome attribution.
- Scope boundary: this is a planned design track. It does not claim that an autonomous maintenance service, auto-merge policy or production routine exists.

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
