# Engineering Signal 017 — Proof Logistics / Доказательная логистика

**Status:** proposed engineering principle  
**Proposed:** 14 Aug 2026  
**Scope:** organization, routing and retrieval of bounded causal evidence  
**System:** NEO REZONANS verification chain  
**Not:** a proof of globally optimal routing, a throughput benchmark, a production storage guarantee or an execution authority

## Signal

A causal evidence chain is also a logistics system.

It has a source, a package, a route, handoffs, storage, inspection, delivery and retrieval. The proof is useful only when the right evidence reaches the right verifier with its identity, causal order, integrity, freshness and authority boundary intact.

The working name is **Proof Logistics** or **доказательная логистика**:

~~~
intent
  ↓ source and scope
ProofPath
  ↓ pre-execution decision and replay evidence
CML
  ↓ causal packing and lineage
LiminalDB
  ↓ durable local/test handoff and restart replay
RINSE
  ↓ bounded read-only reflection
ContractGraph-QA
  ↓ independent route and invariant verification
~~~

## Adjacent execution-control boundary: CaPU

CaPU is tracked beside this route at the exact observed head
`safal207/CaPU@babd2945046d2564e1110a76741827560c57fcca`.

Its role is **execution control only**: the `Gate → Incubate → Commit → Execute`
boundary rejects an effect before commit. It is not inserted as a hidden seventh
proof-logistics stage, does not own the canonical causal-record meaning, and does
not turn durable evidence persistence into execution permission.

The ownership split is therefore explicit:

~~~
CML       → canonical causal and authorization-record semantics
CaPU      → execution admissibility / commit-before-effect control
LiminalDB → bounded evidence persistence and restart recovery
RINSE     → read-only reflection
CGQA      → independent verification
~~~

For SYSTEM-007 this is an adjacent negative/positive boundary check only. The
fixture does not perform a CaPU production execution or an external effect. A
future route may consume a CaPU decision, but that would require its own exact
capability pin, authority contract and independent evidence.

The analogy to physical logistics is structural rather than rhetorical:

~~~
resource source       → evidence source
cargo specification   → intent / causal contract
quality gate          → ProofPath decision
packing and manifest  → CML lineage + evidence roles
warehouse / ledger    → LiminalDB durable record
inspection            → RINSE reflection
delivery receipt      → independent QA result
last-mile retrieval   → future verifier / agent route
~~~

A short chain is not automatically a good chain. A fast route that loses the causal parent, silently changes the logical operation, uses stale capability bytes or turns observation into authority is a failed delivery.

## The proposed optimization problem

The objective is not “the fewest hops.” It is the lowest-cost **valid** route.

For a candidate route r:

~~~
RouteCost(r) =
    verification_cost
  + serialization_cost
  + transfer_cost
  + storage_cost
  + retrieval_cost
  + latency_cost
  + duplication_cost
  + staleness_risk
  + handoff_risk
~~~

The route is admissible only when hard constraints hold:

- logical_operation_id is conserved end to end;
- intent, causal parent, argument digest, nonce and policy remain bound;
- every handoff has a known source and destination contract;
- evidence bytes and manifests are digest-bound;
- exact capability and contract identities are recorded where required;
- authority is non-increasing across an evidence route;
- authorization, observation, reflection and QA remain distinct roles;
- the route is replayable from bounded inputs;
- missing, stale, tampered or ambiguous cargo fails closed.

Therefore the relevant algorithm is a **constrained shortest proof path**, not an unconstrained shortest path. The cheapest invalid route must lose to a more expensive valid route.

## Proof cargo and handoff contract

A handoff should declare what it transports. At minimum:

| Field | Meaning |
|---|---|
| logical_operation_id | stable identity of the causal operation |
| source_stage / target_stage | route endpoints |
| evidence_roles | intent, authorization, observation, cause, reflection, verification |
| source_digest | exact bytes being transported |
| manifest_digest | bounded inventory of the package |
| causal_parent_ref | the upstream event or record that gives meaning |
| capability_identity | repository, capability and exact commit where applicable |
| validity_window | the time or protocol window in which the proof applies |
| authority_effect | explicit statement that the handoff grants no hidden authority |
| route_status | PASS, HOLD, BLOCK, NOT_RUN or INCOMPLETE |

This turns “the evidence was passed along” into a falsifiable delivery receipt.

The route should preserve separate cargo lanes:

~~~
authorization
      ≠ observation
      ≠ causal interpretation
      ≠ reflection
      ≠ QA verdict
~~~

Packing these lanes together may reduce transfer cost while increasing semantic ambiguity. Proof logistics prefers slightly larger explicit packages over compressed packages that make the receiver guess.

## P0-2 application

FCRP-SYSTEM-007 is the first concrete route for this principle. Its implementation should expose:

1. a deterministic route identity and stage order;
2. a bounded envelope for every handoff;
3. digest continuity from signed intent to final QA;
4. a retrieval index so a verifier can locate the smallest sufficient evidence set;
5. route metrics, not only a final PASS;
6. negative controls for lost, stale, duplicated, tampered or misrouted evidence.

The first route is intentionally fixed:

~~~
intent
 → ProofPath
 → CML
 → LiminalDB
 → RINSE
 → ContractGraph-QA
~~~

Later work may compare alternate routes, but route comparison must preserve the same semantic proof claim and the same hard constraints. A route that reaches a green label with less evidence is not more efficient; it is proving a different proposition.

## P0-3 application — provider-neutral cargo spine

The first reusable cargo contract is now recorded in
`governance/provider-neutral-interoperability-contract.v0.1.schema.json` and
exercised by a canonical fixture. Every stage repeats the same spine:

~~~
logical_operation_id + execution_id + attempt_id
parent_cause + intent + resolved_target
expected_invariants + observed_outcome + phase
valid_time + transaction_time + recovery_state
verification_refs + non-authority boundary
~~~

Native names remain visible through an explicit field map. ProofPath, CML,
LiminalDB, RINSE and ContractGraph-QA can therefore keep their own schemas while
the verifier receives a stable routing envelope. The P0-3 lifecycle checks
serialization, local/test storage, reopen, reflection and independent route
reconstruction; identity rename, broken parent, missing evidence, semantic rename
and authority escalation are delivery failures, not alternate successes.

The CaPU field map is deliberately outside the event list. This keeps execution
admissibility adjacent to the proof route without making it a second semantic
authority or a hidden seventh delivery hop.

## P0-4 application — delivery receipt and ancestry

The P0-4 gate adds a delivery receipt to the proof cargo. A verifier can now
check, in one bounded artifact, that the subject observed at collection start,
the subject observed at collection end, the expected ancestor, the workflow
identity and the artifact subject all refer to the same route. The result is
`PASS` only when each check is explicit; `HOLD`, `NOT_RUN` and `INCOMPLETE`
remain non-green states.

This is the logistics invariant that prevents a well-packed but stale package
from being delivered as current evidence. It reduces retrieval ambiguity without
collapsing authorization, observation, reflection or QA into one authority lane.

## P1-1 application — rejection receipts and route efficiency

The negative-path matrix treats rejection evidence as first-class cargo. Each
case carries its expected decision, observed decision, reason, input digest,
replayable evidence reference and decision digest. A verifier can therefore
route directly to the smallest sufficient receipt instead of scanning the full
chain, while still checking that the receipt belongs to the exact ContractGraph-QA
subject and pinned ProofPath head.

The matrix contains 16 deterministic policy evaluations: 15 `BLOCK` negative
cases and one `ACCEPT` policy-eligible control. All 16 replay identically, all
16 have complete evidence, and zero cases execute. This is a delivery property,
not an authorization property: authority flags remain false, and no provider,
executor, wallet, real secret or external effect is involved. `BLOCK` and
`HOLD` are fail-closed cargo states, so a missing or ambiguous receipt cannot be
mistaken for a successful delivery.

## P1-2 application — closed cargo manifest and replay route

P1-2 turns the logistics metaphor into a bounded delivery receipt. The canonical
bundle is `neo-resonance-p1-2-bundle-001`, collected by a read-only fixture at
`2026-08-14T15:00:00Z`. Its verifier subject is
`ContractGraph-QA@6e51cbb176f6d891b758e3026744d1d4c4c5727a`; the frozen
ContractGraph-QA source records inside the bundle remain explicitly pinned to
`fcd5e88655eedd3e4e4d3944bb133a8e2c8b0d8e`. That distinction prevents a current
verifier checkout from being confused with the source revision whose bytes were
actually packed.

The cargo inventory is closed and directly addressable:

| Path | Role / component | Bytes | SHA-256 | Source revision |
|---|---|---:|---|---|
| `durable-record.json` | durable / LiminalDB | 201 | `e03db8b8fcc91f03be47b6e544a6287e1107842e9b0a3585e9de561dcb767852` | `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728` |
| `intent.json` | intent / ContractGraph-QA fixture | 267 | `c41ba09a3a64daaa1e43b1a81a5e67631da5a060444de85b7d509b765aa958ce` | `fcd5e88655eedd3e4e4d3944bb133a8e2c8b0d8e` |
| `reflection-trace.json` | reflection / RINSE | 227 | `370eb517be8c0263dd79cb452684f10ee8d08f22f544a6bcd1a37a6a4d5f1a42` | `3be0d2ceb1440641b141cdb80c82ed118e4186dd` |
| `recovery-receipt.json` | recovery / LS | 261 | `cd47f28e1b6da26df8b11e2fab679fefa4eafa3f0887f6fff4827465a2003aff` | `fa7e3aba4ff9154856fa7d27c92f702137819ac1` |
| `replay-trace.json` | replay / ContractGraph-QA fixture | 211 | `ed5d631ec09bb9e1a1b0a79698a38f7b1f13838770c61f8ad2f8809c107a929c` | `fcd5e88655eedd3e4e4d3944bb133a8e2c8b0d8e` |
| `verification-result.json` | verification / ContractGraph-QA fixture | 243 | `a4911ea841e2db477026f6e85282e3eb044086be529845b9cb36eeebf3e5187c` | `fcd5e88655eedd3e4e4d3944bb133a8e2c8b0d8e` |

The six cargo items total 1,410 bytes. Each item carries the same bounded
collection and valid/transaction time, while its component revision preserves
the provenance needed for a receiver to reject stale or misrouted cargo. The
manifest itself is digest-bound as
`sha256:7d122d8cb2bfdb29ddc36cda55e1c319a4c1d0c2f56f2af7fa62e681f3d5c7bd`.

The replay route is a six-step indexed handoff:

~~~
intent → durable record → reopen/reflection → recovery receipt
      → replay trace → independent verification
~~~

Every input and output is an explicit artifact ID, every sequence number is
contiguous, and every step declares `side_effect_executed=false`. The verifier
replayed the route to `SAME_RESULT`. Missing, unlisted, duplicated, duplicate-
digest, path-traversal, size-mismatch, SHA-mismatch, source-drift, unknown
reference, non-contiguous, or side-effect-marked cargo is rejected rather than
silently repaired. This is retrieval-efficient because a downstream verifier
can jump from the manifest to the smallest sufficient file set without scanning
the repository, while still checking closure and integrity.

The bundle remains evidence cargo, not an authority token: execution,
external-effects and mutation flags are all `false`; reflection cannot authorize
execution; and a valid manifest cannot authorize merge, deployment, production
persistence or security decisions.

## P1-3 application — separate lanes and efficient escalation routing

P1-3 makes the proof-logistics lane split executable. The receiver no longer has
to infer whether a delivered record is proof cargo, a reflection, or an authority
instruction. Each lane is indexed and checked independently:

| Lane | Cargo meaning | Can authorize? | Can mutate source? | Delivery status |
|---|---|---:|---:|---|
| evidence | recomputable proof material and integrity receipts | `false` | `false` | `PASS` cargo only |
| reflection | bounded interpretation of durable bytes | `false` | `false` | `REFLECTION_ONLY` |
| authority | explicit control record, separate from proof and reflection | only by a separate control | only by a separate control | fixture is `HOLD` |

The current P1-3 fixture is bound to ContractGraph-QA PR #61 base
`b54173530c675083426137176cde0aed0b90853a`, runtime verifier subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329`, and frozen source subjects:
ProofPath `4a05ee31d7497979c2505dd55bfef08823302e24`, LiminalDB `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728`, RINSE `3be0d2ceb1440641b141cdb80c82ed118e4186dd`, LS `fa7e3aba4ff9154856fa7d27c92f702137819ac1`, and the
ContractGraph-QA fixture `6e51cbb176f6d891b758e3026744d1d4c4c5727a`. The runtime verifier subject is the
checkout that performs the inspection; the frozen fixture subject is the source
revision whose cargo is being inspected. They are separate logistics identities,
not interchangeable labels.

The delivery receipt contains three artifacts totaling 1,254 bytes and four
replayable cases. The route is deliberately small enough for direct retrieval:

~~~
evidence PASS        → execution request → BLOCK / EVIDENCE_NOT_AUTHORITY
reflection PASS       → execution request → BLOCK / REFLECTION_NOT_AUTHORITY
inferred authority   → execution request → BLOCK / EXPLICIT_AUTHORITY_RECORD_REQUIRED
authority HOLD       → execution request → HOLD / AUTHORITY_REVALIDATION_REQUIRED
~~~

All four cases replay to `SAME_RESULT`; three are `BLOCK`, one is `HOLD`, and zero
cases execute. Every side-effect flag is `false`. A verifier can route directly
to the lane, source subject, artifact digest and decision receipt it needs,
without scanning unrelated repository history. The closed manifest still makes
membership, byte size, SHA-256, source revision, causal reference and route
status checkable.

The first workflow attempt (#1, `31873466160`) returned `HOLD` because it exposed
an identity-routing bug: the verifier subject was incorrectly compared to the
frozen fixture source subject. That fail-closed result was retained, the rule was
corrected, and the current exact-head workflow [run #14](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737024)
passes. This is a logistics lesson: a valid delivery receipt must identify both
carrier/verifier and cargo/source; conflating them creates a false routing failure,
while omitting either one makes the proof impossible to locate or audit.

Occurrence binding adds a second logistics constraint at source subject
`558cf8126de88d5bc57de6b36de9f183bc46d27e`: semantic decision identity,
authorization occurrence identity and consumption fact are separate cargo labels.
A side-effecting execution may consume an authorization only when exactly one
concrete occurrence is resolved. Ambiguous, missing, unauthorized or already
consumed occurrences route to `OCCURRENCE_AMBIGUOUS`, `OCCURRENCE_NOT_FOUND`,
`NOT_AUTHORIZED` or `ALREADY_CONSUMED` and fail closed. This keeps a valid
decision from being delivered to the wrong occurrence, and does not claim
CrewAI adoption, production deployment or ledger migration.

P1-3 therefore optimizes retrieval without collapsing authority boundaries. It
reduces lookup cost by explicit lane and subject indexes, while preserving the
hard constraint that evidence, reflection and QA cannot silently become execution
authority. The route is bounded, replayable and side-effect-free; it does not
claim live execution, merge, deployment, production persistence or security
authorization.
## Current occurrence-portability receipt

The bounded P1-4/P1-5/P1-6 portability matrix is bound to verifier subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` and [workflow run #3](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737013). Its artifact digest is `sha256:9cf005d73a07f4f356581337c27c378747b199ada278bd9122f8f3db71559200`. The receipt keeps decision, concrete occurrence and consumption fact as separate routable identities; race, replay and request-ID rebound cases fail closed. This is bounded evidence cargo, not execution authority.

## P1-7 independent replay cargo

P1-7 adds a second verifier vantage. [Workflow run #2](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737094) passed at ContractGraph-QA subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` while freezing RESONANCE source subject `85c3baea0a551751263ef563a3dd1c75492f57ae`. The verifier reconstructed the exact occurrence `decision-A / evt-42`, route fingerprint `fee0b69553abc156b77ad446c3cda8c7f50bbf0efc2cd3aafa75a279016f7930`, and ConsumptionReceipt digest `690e4852db587c8aa97673ea3b93c5512ffb052ef15de7153604d3a2ff72d72a`. The cargo contained six subject records and artifact digest `sha256:cb4d3eec62eee29787dd6608faa9dde804270c6afe450aa4a2560d90bb665528`.

The independent route rejected reorder, ambiguity, receipt tamper, pinned-revision tamper and raw-subject tamper. This is the logistics gain: the receiver can locate the minimum sufficient proof and independently recompute it, while stale later journal commits remain separate source identities.

## P1-8 compatibility and migration cargo

P1-8 turns compatibility into a routable proof package. [Workflow run #1](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737060) passed at verifier subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329` with 11 completed steps and artifact `fcrp-p1-8-compatibility-migration-31879737060-1`, digest `sha256:dc6ca4d597b0fee05528e20bf6f9a72d6d2e6a2e67931eab8c2c8d2d5ddaf28e`.

The delivery policy is `EXACT_CURRENT_REVISION_ONLY`: the current ProofPath authorization schema, LiminalDB protocol and RINSE receipt are accepted only at their exact observed identities. Candidate ProofPath v0.2, LiminalDB 1.1.0 and RINSE receipt v0.2 are rejected with explicit unsupported-revision outcomes; route reorder and authority escalation are rejected as misrouted or unsafe cargo.

The recovery receipt preserves the original source payload digest `5abf15b7fb2533a8d668be4faf4a47128344cc29a4ef1616c1f4131d6f261c82` across every rejected candidate. The compatibility receipt contains nine exact subject records, subject fingerprint `a5e28dfdfcb0937de31e90f49a44686fa7c031bbcc556b0c3c7b55491332f333`, receipt digest `sha256:aebbb831ac4e0b4c5554094a8750f76d4f581dda8a297b42e16f37f5d51e1d57`, and all mutation, execution, external-effect and production-ledger flags are `false`.

This improves proof logistics by making incompatibility searchable as a typed delivery failure rather than a vague missing artifact: `UNSUPPORTED_SCHEMA_REVISION`, `ROUTE_ORDER_DRIFT`, `AUTHORITY_ESCALATION`, `EXACT_REVISION_TAMPER` or `RAW_SUBJECT_TAMPER`. The receiver can route to the exact source digest and recovery path without scanning unrelated history. The result is conformance cargo only; it does not claim automatic migration, merge, deployment, production persistence or security authorization.

## P2-4 maintenance-routine cargo

The Maintenance Routine Contract is now bounded and independently evaluated at ContractGraph-QA subject `7fd3e744037832b74b2ee4c4c71cc8fce18fc329`. [Workflow run #1](https://github.com/safal207/ContractGraph-QA/actions/runs/31879737058) produced artifact `fcrp-p2-4-maintenance-routine-31879737058-1`, 2397 bytes, digest `sha256:d63a58cca47d7fcc329963b8c1438af9316927d0b6f9bd56982799bbcec9c0b3`. The evaluator returned `PASS` under `QUALITY_ONLY_NO_MERGE_AUTHORITY`: two routine runs, 2/2 evidence-complete, 2/2 independently verified, 2/2 replay-stable and 2/2 outcome-attributed. Receipt digest `sha256:50e4c0ebdf7428142e9951adbae983673ff76c76e8fce97f78cd8ee5087c254e`; witness digest `72df07094cce9975a9ffb631a65fe70561c30c3fa8b884b7f1a5afc07bf69b0c`.

The two cargo items are `contract_drift_detector` for ProofPath `4a05ee31d7497979c2505dd55bfef08823302e24` and `evidence_auditor` for frozen RESONANCE source `85c3baea0a551751263ef563a3dd1c75492f57ae`. Both outcomes remain `DRAFT_OPEN` / `NOT_MERGED`, and all authority flags, side-effect flags and production-ledger mutation flags are `false`. Negative boundaries for stale target, missing evidence, changed subject, contradictory finding, false-green verification, ambiguous occurrence, self-authorization and wrong outcome attribution fail closed.

This is the next logistics layer: not only can a verifier find the proof cargo, it can identify which routine observed it, which patch it proposed, what independent verification passed and what downstream outcome was actually attributed. Routine quality is not repository health or merge authority.
## Logistics metrics

The following metrics are proposed for later measurement, not yet benchmark results:

- **proof lead time** — source creation to independently usable verification;
- **handoff loss** — required evidence roles or lineage links missing at a boundary;
- **proof density** — verified claim coverage per byte or per stored artifact;
- **retrieval cost** — bytes, lookups and verification steps needed for the smallest sufficient proof;
- **verification fan-out** — number of downstream consumers that need to re-read or re-derive the same source;
- **route duplication** — repeated copies or repeated derivations of identical evidence;
- **staleness exposure** — time or repository-history distance beyond the declared validity window;
- **route congestion** — queued or rate-limited verification work;
- **delivery failure class** — MISSING, STALE, TAMPERED, MISROUTED, DUPLICATED, AUTHORITY_ESCALATED or INCOMPATIBLE.

The first optimization target should be retrieval cost and handoff loss. Optimizing raw latency before those two dimensions is likely to reward an evidence shortcut.

## Falsification questions

The principle becomes useful only if it can be disproved by tests:

- Does a verifier need to scan the entire repository when a manifest can route it to a bounded package?
- Does a changed argument digest reach the final verifier as if it were the original operation?
- Does a stale dependency head look like a successful delivery?
- Can a retry create a second proof cargo item with a different payload?
- Can a reflection package be delivered to an execution consumer?
- Can a valid source digest conceal an incompatible semantic contract?
- Can two physical topologies deliver the same proof without changing its semantic identity?
- Can an independent verifier reconstruct the route from the recorded handoffs alone?

These are routing and delivery questions, not merely serialization questions.

## Safety boundary

This signal does not claim that logistics terminology creates authority, that a manifest proves truth, that a lower byte count means stronger evidence, or that one route is universally optimal.

The journal remains routing guidance, not execution authority. A route optimizer may select where evidence should be read or verified; it may not authorize the represented real-world action. Publication may preserve a reflection; it must not promote reflection to truth, credentials or mutation permission.

## Classification

**RESONANCE classification:** Proposed Engineering Signal — proof logistics is a candidate design principle for making causal evidence chains efficient to locate, transport, store, inspect and retrieve while preserving semantic and authority invariants. FCRP-SYSTEM-007 is the first falsifiable implementation target.
