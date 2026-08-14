# P0-3 — Provider-Neutral Interoperability Contract v0.1

**Status:** bounded machine-verified contract fixture  
**Primary route:** `intent → ProofPath → CML → LiminalDB → RINSE → ContractGraph-QA`  
**Scope:** canonical field spine, explicit native mappings, local/test serialization and replay  
**Authority:** evidence and reflection only; no merge, deployment, production, external-effect or security authorization

## Purpose

The repositories keep their native schemas. This contract defines the smallest
shared handoff envelope so a verifier can route proof cargo without guessing
which field carries identity, lineage, time, recovery or evidence.

The canonical fixture is
`governance/provider-neutral-interoperability-fixture.v0.1.json`. Its schema is
`governance/provider-neutral-interoperability-contract.v0.1.schema.json`; the
stdlib validator and replay runner are in
`governance/validate_provider_neutral_interoperability.py`.

## Canonical spine

| Canonical field | Required meaning |
|---|---|
| `logical_operation_id` | Stable identity conserved through every stage |
| `execution_id` | One bounded execution context for the route |
| `attempt_id` | One retry/replay attempt identity |
| `parent_cause` | Immediate upstream event; root is explicit `null` |
| `intent` | Declared purpose and expected outcome |
| `resolved_target` | Component, operation and bounded scope actually addressed |
| `expected_invariants` | Invariants the stage must preserve |
| `observed_outcome` | What the stage observed or verified, not an inferred authority |
| `phase` | One of the six primary route phases |
| `valid_time` | Time window in which the evidence claim applies |
| `transaction_time` | Time at which the handoff was recorded |
| `recovery_state` | Explicit retry/reopen/reflection state |
| `verification_refs` | Digest-bound evidence references needed to verify the handoff |

Every event repeats the spine. Repetition is intentional: it makes a handoff
self-describing and lets an independent verifier reject a silent identity or
semantic rename.

## Native mapping rule

Each event carries `native_projection.field_map`. The map names the native path,
declares whether the value is an identity, a derived reference or a structured
projection, and must mark `semantic_status: preserved`. A different spelling
such as CML `parent_cause`, LiminalDB `correlationId`, or CGQA
`logicalOperationId` is therefore visible as a mapping decision; it is not
silently treated as a new meaning.

The fixture binds the native subjects to the exact revisions already used by
FCRP-SYSTEM-007:

| Phase | Native repository | Native boundary |
|---|---|---|
| intent | RESONANCE / SYSTEM-007 envelope | declared operation, nonce and argument digest |
| ProofPath | `safal207/ProofPath` | native SCIG verification receipt |
| CML | `safal207/Causal-Memory-Layer` | `CausalRecord` parent-cause chain |
| LiminalDB | `safal207/LiminalDB` | durable event, valid/transaction time and reopen summary |
| RINSE | `safal207/rinse` | source trace and reflection-only graph |
| ContractGraph-QA | `safal207/ContractGraph-QA` | independent result, negative cases and evidence digests |

## CaPU boundary

CaPU is included in the fixture under `adjacent_control_planes` at exact head
`babd2945046d2564e1110a76741827560c57fcca`. It is explicitly outside the
primary proof route and remains `execution_control_only`; CML remains the
semantic authority. It is not a seventh event and does not receive evidence
authority merely because it can consume a decision boundary.

## Machine lifecycle

The P0-3 runner proves the bounded lifecycle:

1. canonical JSON serialization;
2. byte storage in an isolated local/test directory;
3. reopen and canonical validation;
4. read-only reflection with `REFLECTION_ONLY` authority;
5. independent route/identity reconstruction;
6. negative rejection for identity rename, parent break, unknown phase, missing evidence, authority escalation and semantic rename.

The workflow uploads the result, reflection, stored contract and SHA-256
manifest. A successful lifecycle proves contract conformance for this fixture;
it does not prove live runtime integration or production persistence.

## Stop conditions

The transition is blocked if a field mapping is ambiguous, a native meaning is
silently renamed, a parent link or evidence digest is missing, a timestamp is
invalid, a stored byte differs after reopen, a reflection mutates source state,
or any authority flag becomes true.
