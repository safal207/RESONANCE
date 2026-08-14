# Engineering Signal 015 — Durability Frontier / Commit ≠ Ack ≠ Retry Permission

**Status:** VERIFIED — 2026-08-14  
**Lineage:** FCRP → persistence frontier → durable local/test evidence → independent cross-repository replay  
**System case:** `FCRP-SYSTEM-005`  
**Authority:** operational memory / routing guidance only; this signal grants no production persistence, deployment, credential, financial, merge, external-effect, or execution authority

## Signal

SYSTEM-004 ended deliberately at:

```text
ProofPath
→ verified evidence
→ LiminalDB-compatible artifact
→ persistence frontier
```

SYSTEM-005 crossed that frontier for the first time — but only under an explicit **`local_test_only` storage admission**.

The verified path is now:

```text
real ContractGraph-QA evidence
        ↓
canonical ProofPath SCIG
        ↓
native proofpath-scig = VALID
        ↓
SYSTEM-004 AuditEvent projection
        ↓
canonical LiminalDB artifact validator = dry-run PASS
        ↓
SEPARATE local/test storage admission
        ↓
canonical ProofPathDurableLedger
        ↓
WAL append + sync
        ↓
process restart
        ↓
byte-exact replay
        ↓
same semantic retry = ALREADY_PRESENT
changed semantic evidence = IDEMPOTENCY_CONFLICT
        ↓
AfterSyncBeforeAck recovery = one durable effect
        ↓
LTP strict + replay
        ↓
FCRP-SYSTEM-005 = PASS
```

Therefore the current system statement is:

```text
ProofPath
→ verified evidence
→ LiminalDB artifact acceptance
→ separate local/test storage admission
→ durable evidence state
→ restart-replayable proof record
```

The qualifier **local/test** is load-bearing.

## Canonical evidence

Consumer-side durable capability:

```text
repository  safal207/LiminalDB
merge       61b02fc81e0cb5cf1f1ed4658ecff58f683cb728
PR          #121
```

Independent system verification:

```text
repository  safal207/ContractGraph-QA
merge       efe3efe637372815bef55ec3862c49cc69244b88
PR          #59
```

Final exact-head verification subject before merge:

`ab9d80a8faa056574615981dc78a85ec10a4ad2b`

Final independent evidence artifact:

```text
artifact    9215228292
digest      sha256:01146320a1d04aaedb9bc12a76c71935b6b474620b372119a802207d841845e9
```

Pinned identities:

```text
logical_operation_id
crossmint-public-example-001

ProofPath SCIG capability
685d50e256a5125a21f4c4584b326411caaa64ad

LiminalDB artifact import contract
00580ff097dee61b45ad3c8a3c36ae5f548f572d

LiminalDB AuditEvent contract blob
fd733971aaae089df770062bcf7f2c2d6d19ca1d

LiminalDB durable consumer
61b02fc81e0cb5cf1f1ed4658ecff58f683cb728

LTP
fc58072d301a487c09227ea09004dc8e99676370
```

## 1. Artifact acceptance is not storage admission

The canonical artifact consumer remains intentionally non-persistent:

```text
mode = dry_run
write_performed = false
durable_memory_accepted = false
live_ingestion_performed = false
```

SYSTEM-005 did **not** reinterpret this PASS as permission to write.

A separate storage-admission reference was created for the exact test subject and exact durable consumer:

```text
scope = local_test_only
derived_from_evidence = false
```

This gives a sharper authority split:

```text
artifact accepted
        ≠
storage write authorized
        ≠
execution authorized
```

The durable record permits only:

```text
storage_write_authorized = true
persistence_scope = local_test_only
```

while replay-enforcing:

```text
execution_authorized = false
mutation_authorized = false
external_effects_authorized = false
```

## 2. Commit is not acknowledgement

The strongest recovery test is not an ordinary restart.

The canonical LiminalDB consumer deliberately injects:

```text
AfterSyncBeforeAck
```

The causal sequence is:

```text
WAL frame written
→ sync succeeds
→ acknowledgement path fails
→ caller receives error
```

At that moment:

```text
caller-observed failure
        ≠
no durable effect
```

The record may already be committed.

Therefore:

> **An acknowledgement failure after commit is not evidence that the effect did not happen.**

## 3. Ack failure is not retry permission

The safe recovery sequence is:

```text
append returns error after sync
→ current writer becomes poisoned
→ no second append in the same ambiguous state
→ close / reopen
→ full WAL replay
→ committed record recovered
→ same retry reconciles as ALREADY_PRESENT
```

This is the persistence-layer form of **Post-Commit False Failure**:

```text
COMMITTED
but
reported as failure to caller
```

The invariant becomes:

```text
may_have_committed = true
→ do not infer retry permission
→ reconcile durable state first
```

## 4. Idempotency belongs to the logical operation, not the payload

The durable ingestion key is derived from:

```text
namespace
+ logical_operation_id
+ semantic record kind
```

It is intentionally **not** derived from event bytes.

Why?

If payload bytes were part of operation identity:

```text
same operation
+ changed payload
→ new key
→ accidental second durable operation
```

Instead SYSTEM-005 proves:

```text
same operation + same semantic artifact
→ ALREADY_PRESENT
→ event_count = 1
```

and:

```text
same operation + changed semantic artifact
→ ERROR_CODE IDEMPOTENCY_CONFLICT
→ no second durable effect
```

The negative control changes an actual semantic field:

```text
event.details.persistence.durable_memory
false → true
```

It does not merely append whitespace or otherwise change irrelevant formatting.

## 5. Retry time does not rewrite first durable transaction time

The durable record carries:

```text
valid_time_ms
transaction_time_ms
```

with:

```text
transaction_time_ms >= valid_time_ms
```

The first value describes when the represented observation is valid.

The second describes when this accepted evidence was first durably recorded.

A later retry may happen at a later wall-clock time, but if it resolves to the same durable operation:

```text
ALREADY_PRESENT
```

then the first `transaction_time_ms` remains unchanged.

No second durable event means no second transaction time.

## 6. Exact restart proof means bytes, not only references

SYSTEM-005 deliberately stores:

- the exact accepted LiminalDB AuditEvent bytes;
- the exact artifact-admission report bytes;
- their SHA-256 identities;
- producer capability identity;
- consumer contract identity;
- temporal coordinates;
- authority-negative fields.

The independent verifier uses two processes:

```text
process A: ingest
→ exit

process B: reopen
→ full WAL replay
→ emit recovered event/admission
→ byte-for-byte compare with originals
```

This is stronger than proving that an in-memory object survived an API call.

## 7. Consumer green is not enough — independently re-exercise it

LiminalDB PR #121 first proved the durable consumer in its own repository.

That did **not** become the final NEO REZONANS system claim by itself.

ContractGraph-QA then independently:

1. rebuilt the real upstream evidence;
2. ran the canonical ProofPath native verifier;
3. rebuilt the SYSTEM-004 AuditEvent;
4. checked out exact canonical LiminalDB durable bytes;
5. re-ran the artifact validator;
6. re-ran the canonical durability and `AfterSyncBeforeAck` tests;
7. performed a fresh ephemeral WAL write;
8. reopened it in another process;
9. tested idempotent retry and semantic conflict;
10. ran native LTP strict/replay;
11. evaluated the FCRP case.

This avoids a weak pattern:

```text
consumer says it works
→ system records consumer self-claim as system proof
```

Instead:

```text
consumer capability canonical
→ independent caller re-exercises exact capability
→ system claim
```

## 8. Native evidence dimensions are not automatically protocol enums

The first independent FCRP run reached the durable state successfully but the final causal evaluator blocked the case.

Initial case model tried to add:

```text
VALID_TIME
TRANSACTION_TIME
```

as top-level FCRP v0.2 time domains.

But the executable protocol currently recognizes only its canonical domain vocabulary.

The correct response was **not** to expand `fcrp_v02.py` merely to obtain the desired PASS.

Instead:

```text
valid_time / transaction_time
= verified native evidence dimensions

but not yet
= canonical FCRP v0.2 time-domain enum values
```

They remain evidence/invariants inside the supported `CAUSAL_SEQUENCE` model until a separate protocol change justifies promotion.

General rule:

> **Evidence that a dimension exists does not automatically authorize changing the verifier's ontology.**

## 9. A green implementation does not validate a bad causal story

The next independent run again crossed the durable path successfully, but FCRP blocked the final case because the case itself ordered:

```text
symptom
before
cause
```

The model originally described:

```text
N1 = system symptom
N2 = authority-boundary cause
```

while claiming a first causal divergence.

The corrected path is:

```text
N1 = authority-boundary first divergence / cause
N2 = over-strong system symptom
N3 = durable consumer refactor point
N4 = restart verification
N5 = idempotency / recovery verification
N6 = path verification
```

with:

```text
cause = N1
FMD = N1
symptom = N2
refactor = N3
```

Nothing in the durable implementation needed changing.

The thing that was wrong was our explanation of it.

Therefore:

> **Implementation evidence may be valid while the causal model describing it is invalid.**

## 10. Immutable capability pin does not mean frozen default branch

The first SYSTEM-005 LTP gate required:

```text
LTP main HEAD == pinned LTP commit
```

Review correctly exposed this as too strong.

An unrelated future LTP commit would invalidate the system gate even if the exact pinned verifier still existed unchanged.

The corrected rule is:

```text
pinned commit exists
AND
pinned commit is an ancestor of observed current main
AND
execute exact pinned commit
```

This preserves both facts:

```text
immutable capability identity
≠
default branch must never advance
```

Exact-head equality should be required only when **head identity itself** is semantically load-bearing.

## 11. Review after green invalidates the old green evidence

SYSTEM-005 reached a complete green once before final review findings arrived.

Those findings exposed:

- an admission-scope literal mismatch inside an identity digest;
- a byte-level rather than semantic tamper control;
- an over-strong LTP default-branch equality assumption.

We did not merge because an earlier artifact was green.

The fixes produced a new head and the entire cross-repository workflow was re-executed.

Therefore only the final artifact is canonical:

```text
9215228292
sha256:01146320a1d04aaedb9bc12a76c71935b6b474620b372119a802207d841845e9
```

The earlier pre-review green evidence is historical, not the final proof.

## Working taxonomy additions

Signal 015 extends the internal FCRP engineering taxonomy with:

16. **Commit / Acknowledgement Conflation** — a durable effect commits but a missing acknowledgement is treated as proof of no effect;
17. **Retry-Permission Inference Drift** — an error response is treated as permission to retry without first reconciling possible committed state;
18. **Payload-Identity Idempotency Drift** — payload bytes define operation identity, allowing changed evidence to become an accidental second operation;
19. **Storage-Admission / Execution-Authority Conflation** — permission to persist evidence silently becomes permission to execute or mutate the represented subject;
20. **Evidence-Dimension / Protocol-Domain Conflation** — an implementation-level evidence dimension is silently promoted into the protocol ontology without verifier support;
21. **Causal-Order Inversion** — a causal case places the claimed cause/FMD after its symptom;
22. **Semantic-Tamper / Byte-Tamper Conflation** — a negative test changes irrelevant representation bytes while claiming to test semantic mutation;
23. **Pinned-Revision / Frozen-Default-Branch Conflation** — immutable capability pinning is implemented as a requirement that the dependency's default branch never advance.

These are working names for recurring engineering shapes, not an external standard.

## Rejected / superseded interpretations preserved

### FORM_ONLY failure ≠ durability defect

Early LiminalDB CI runs stopped at `cargo fmt --check`.

Those runs established only formatting drift. They did not reach the durability tests and therefore could not support a storage verdict.

### CLI error ambiguity ≠ missing idempotency semantics

The first cross-process conflict control observed the expected durable rejection but the harness did not expose a stable machine-readable error class.

The correction was to emit:

```text
ERROR_CODE IDEMPOTENCY_CONFLICT
```

not to change the idempotency semantics.

### Unsupported FCRP time domain ≠ failed durable path

The native path had already passed. The final case failed because our model used unsupported protocol enum values.

### Causal-model failure ≠ implementation failure

The durable path passed while the FCRP case failed because the explanatory graph put the cause after the symptom.

### Pre-review green ≠ final green

A green result produced before valid review corrections is historical evidence, not the canonical final proof.

## Current verified boundary

SYSTEM-005 proves, within pinned revisions and an ephemeral local/test namespace:

1. the real SYSTEM-004 logical operation crosses into durable LiminalDB state unchanged;
2. native ProofPath verification still precedes persistence;
3. artifact acceptance and storage admission remain separate facts;
4. exact accepted event/admission bytes survive restart;
5. producer capability identity and consumer semantic identity remain separate;
6. valid time and first durable transaction time remain replayable;
7. same-semantic retry creates no second durable effect;
8. semantic mutation under the same operation fails with `IDEMPOTENCY_CONFLICT`;
9. `AfterSyncBeforeAck` reconciles to one durable record rather than duplicate state;
10. local/test persistence grants no execution, mutation, or external-effect authority;
11. the trajectory is accepted by native LTP strict/replay;
12. the final FCRP causal case itself is internally coherent.

## What SYSTEM-005 does not prove

Do not extend the result to:

- production persistence authorization;
- service/API ingestion;
- tenant authorization policy;
- distributed replication or quorum durability;
- whole-history rollback resistance against replacement of a mutually consistent local WAL;
- retention / compaction semantics for exact ProofPath payloads;
- unrestricted multi-writer semantics;
- transparency-log anchoring;
- truth of the underlying incident;
- execution authority from durable evidence.

## Next system gate — FCRP-SYSTEM-006

The architectural heartbeat now moves to the next native boundary:

```text
LiminalDB durable evidence state
        ↓
RINSE immutable source trace
        ↓
canonical reflection graph
        ↓
REFLECTION_ONLY interpretation
```

### Falsifiable question

Can canonical RINSE consume the exact durable SYSTEM-005 record as an immutable source trace, derive a reflection through its canonical interpretation semantics, and preserve:

- durable source identity;
- exact trace provenance;
- recorded / valid / reviewed time separation where applicable;
- no rewriting of source history;
- no second semantic authority;
- `REFLECTION_ONLY` / non-executable status;
- zero execution-authority escalation;
- deterministic path / evidence replay?

The critical parent invariant is:

> **Meaning may change. Trace must not.**

Production persistence authorization remains a separate frontier. SYSTEM-006 does not silently solve it.

## Core rule

```text
commit
≠ acknowledgement
≠ retry permission
```

and:

```text
persisted evidence
≠ truth
≠ execution authority
```

---

Signal 015 is operational memory and routing guidance. The canonical repository contracts and their exact execution evidence remain the verification layer; authorization remains separate.
