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
