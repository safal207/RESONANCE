# RESONANCE Transactional Trust Protocol v1.0

**Status:** Experimental protocol specification  
**Scope:** Consequential agent actions with shared state, external side effects, retries, permissions and evidence  
**Protocol chain:** `OBSERVE → VERIFY → AUTHORIZE → BIND → COMPARE → COMMIT → RECONCILE → PROVE`

## Purpose

Agent correctness is not only a property of the final answer. For consequential actions, correctness depends on whether the full transition from observed state to committed effect remained legal, current, recoverable and provable.

Transactional Trust Protocol (TTP) v1.0 composes the invariants developed in RESONANCE Verified Reports #003–#010 into one end-to-end protocol.

It is intentionally framework-agnostic. A model, agent SDK, database, queue, wallet, payment API or policy engine may provide useful primitives, but TTP describes the application-level trust contract across them.

## The eight stages

### 1. OBSERVE

Capture the state that makes the action legal.

Minimum record:

```text
operation_id
actor
intent
observed_state
observed_state_version
observed_at
```

Rules:

- A read is a snapshot, not permanent permission.
- Timeout does not mean failure.
- Missing evidence does not mean missing effect.
- `UNKNOWN`, `ABSENT`, `COMMITTED` and `CONFLICT` are distinct states.

### 2. VERIFY

Evaluate the evidence supporting the observed state.

Minimum checks:

```text
value
source
integrity
provenance
freshness
```

Rules:

- `STALE ≠ CURRENT`.
- `CONFLICT ≠ ABSENT`.
- Self-asserted authority is not verified authority.

### 3. AUTHORIZE

Verify that the source or actor is trusted for this decision now.

Minimum checks:

```text
authority_identity
authority_binding
activation_time
revocation_time
trust_registry_version
trust_registry_freshness
```

Rules:

- `CLAIMED AUTHORITY ≠ VERIFIED AUTHORITY`.
- `VALID SIGNATURE ≠ CURRENTLY TRUSTED AUTHORITY`.
- Fresh evidence evaluated against stale trust state is not trusted evidence.

### 4. BIND

Bind the decision to the exact state and trust versions that made it legal.

A decision object SHOULD carry at least:

```text
operation_id
observed_state_version
trust_epoch
verified_at
invariants
execution_preconditions
```

Rules:

- `VERIFIED THEN ≠ AUTHORIZED NOW`.
- An unversioned boolean such as `allowed=true` is insufficient for consequential transitions.

### 5. COMPARE

At the mutation boundary, compare the bound preconditions with current state.

```text
expected_state_version == current_state_version
expected_trust_epoch    == current_trust_epoch
required_state          == current_state
required_authority      == active
```

Rules:

- Compare and irreversible transition MUST be atomic, transactional or otherwise enforced by the mutation authority.
- A precondition failure is a successful safety outcome when it prevents a stale write.

### 6. COMMIT

Execute the side effect only if all bound preconditions still hold.

Rules:

- One logical operation SHOULD map to at most one committed effect under the declared adapter contract.
- Idempotency keys, compare-and-swap, transactions, leases, transactional outbox or equivalent mechanisms MAY implement parts of this property.
- If an external effect cannot share the business transaction, the business state and durable delivery intent SHOULD commit together before delivery begins.
- TTP does not prescribe one storage or messaging technology.

### 7. RECONCILE

After ambiguous outcomes, database conflicts or external acknowledgement loss, determine what actually happened before retrying.

```text
UNKNOWN / CONFLICT / DB CONFLICT / EXTERNAL ACK UNKNOWN
   ↓
RECONCILE
   ├─ COMMITTED → COMPLETE
   ├─ ABSENT    → RETRY_ALLOWED, subject to fresh preconditions
   ├─ CONFLICT  → RESOLVE EVIDENCE
   └─ UNKNOWN   → HOLD / RECONCILE AGAIN / ESCALATE
```

Rules:

- `UNKNOWN ─X→ RETRY` without evidence.
- `CONFLICT ─X→ RETRY` without resolution.
- A database-level retry signal is not business-level permission to replay a consequential effect.
- A lost external acknowledgement is not evidence that the external effect is absent.
- Retry must re-enter observation, verification, authorization and execution binding; a prior authorization is not automatically reusable.
- External redelivery SHOULD preserve the same logical effect identity when the external contract supports idempotency.

### 8. PROVE

Preserve evidence sufficient for an independent party to reconstruct the transition.

Minimum evidence bundle:

```text
operation_id
actor + intent
state observations + versions
trust observations + versions
evidence verification decisions
precondition result
commit or conflict result
outbox / delivery identity when used
external acknowledgement or reconciliation result
final invariant result
```

Rules:

- Tool success alone is not proof of state correctness.
- Correct final state without causal evidence is incomplete verification.
- Safety-relevant conflicts, rejected writes, redelivery and reconciliation belong in the evidence trail.

## Core invariants

```text
I1  TIMEOUT ≠ FAILURE
I2  UNKNOWN ≠ ABSENT
I3  CONFLICT ≠ ABSENT
I4  CLAIMED AUTHORITY ≠ VERIFIED AUTHORITY
I5  VALID SIGNATURE ≠ CURRENT TRUST
I6  FRESH EVIDENCE + STALE TRUST STATE ≠ TRUSTED EVIDENCE
I7  VERIFIED THEN ≠ AUTHORIZED NOW
I8  READ WAS CORRECT ≠ WRITE IS STILL LEGAL
I9  CHECK + WRITE MUST SHARE ONE STATE PRECONDITION
I10 AMBIGUOUS OUTCOME → RECONCILE BEFORE RETRY
I11 PRECONDITION FAILURE MAY BE A SAFETY SUCCESS
I12 PROOF MUST COVER THE TRAJECTORY, NOT ONLY THE FINAL OUTPUT
I13 RETRYABLE TRANSACTION ≠ RETRYABLE BUSINESS ACTION
I14 DATABASE CONFLICT SIGNAL → RECONCILE BUSINESS STATE BEFORE RE-EXECUTION
I15 BUSINESS STATE + DURABLE DELIVERY INTENT MUST COMMIT TOGETHER
I16 DB COMMITTED ≠ EXTERNAL EFFECT ACKNOWLEDGED OR ABSENT
I17 REDELIVERY MUST PRESERVE LOGICAL EFFECT IDENTITY
I18 AMBIGUOUS EXTERNAL ACK → RECONCILE EXTERNAL STATE BEFORE RE-EXECUTION
```

## Reference state machine

```text
INTENT
  ↓
OBSERVED
  ↓
VERIFIED
  ↓
AUTHORIZED
  ↓
BOUND
  ↓
COMPARE
  ├─ mismatch / database conflict → CONFLICT → RECONCILE
  └─ match
       ↓
     COMMIT
       ├─ local acknowledged → external delivery if required
       └─ local ambiguous    → UNKNOWN → RECONCILE

external delivery
   ├─ ACK          → PROVE → COMPLETE
   └─ ACK UNKNOWN  → RECONCILE EXTERNAL STATE
```

## Failure coordinates covered

TTP is designed to connect the RESONANCE structural coordinates rather than replace them:

```text
State
Causality
Phase
Transition
Time
Recovery
Verification
Evidence
```

The protocol adds an execution discipline across those coordinates for consequential transitions.

## Conformance levels

### TTP-Fast

For low-impact reversible actions:

- OBSERVE
- minimal VERIFY
- BIND state version
- COMPARE + COMMIT
- basic PROVE

### TTP-Standard

For consequential business actions:

- all eight stages
- explicit UNKNOWN / CONFLICT
- authority lifecycle
- trust-state freshness
- state + trust version binding
- reconciliation before retry
- durable evidence bundle
- stable logical effect identity across external redelivery when supported

### TTP-Deep

For high-impact or adversarial environments:

- all TTP-Standard requirements
- independent/peer verification
- stronger provenance / attestations
- isolated execution environment
- replayable evidence
- explicit recovery/escalation path

## Adapter rule

A storage or execution adapter conforms to the atomic transition requirement only when the mutation authority itself enforces the state precondition. A prior application-side check is insufficient.

For a versioned relational record, the reference shape is:

```text
OBSERVE state/version N
      ↓
BIND expected_version=N
      ↓
MUTATION AUTHORITY evaluates N atomically
   ├─ match    → transition + effect commit
   └─ mismatch → PRECONDITION_FAILED → reread / reconcile
```

Report #012 validates this shape against a real PostgreSQL service using two independent connections. The successful adapter used a conditional `UPDATE ... WHERE state='absent' AND version=N` and inserted the effect only for the winning transaction.

## Retry classification rule

Storage engines can expose different conflict signals for the same stale business decision. TTP classifies those signals as inputs to recovery, not as direct permission to replay the effect.

```text
DATABASE SIGNAL
   ├─ conditional mutation matched 0 rows
   ├─ serialization failure / 40001
   └─ other concurrency conflict
          ↓
END / ABORT STALE TRANSACTION
          ↓
RE-OBSERVE AUTHORITATIVE STATE
          ↓
RE-VERIFY + RE-AUTHORIZE + RE-BIND
          ↓
RETRY ONLY IF OPERATION IS STILL ABSENT + LEGAL
```

Report #013 validates this rule across PostgreSQL 17.6 `READ COMMITTED`, `REPEATABLE READ` and `SERIALIZABLE` for one deterministic two-writer race. `READ COMMITTED` returned a zero-row precondition failure; the stronger snapshot levels returned SQLSTATE `40001`. All losing paths reconciled to `COMMITTED / version=101 / effects=1`.

## Cross-boundary delivery rule

A local transaction cannot by itself prove the state of an external side effect. When an effect lives beyond the database transaction boundary, TTP separates durable intent from delivery outcome.

```text
BUSINESS TRANSACTION
  state transition + durable outbox intent
              ↓
            COMMIT
              ↓
        DELIVERY WORKER
              ↓
     stable logical effect ID
              ↓
      EXTERNAL EFFECT
        ├─ ACK → mark delivered
        └─ UNKNOWN
             ↓
      reconcile by effect ID
             ├─ COMMITTED → mark delivered
             ├─ ABSENT    → fresh delivery may proceed
             └─ UNKNOWN   → hold / reconcile again
```

Rules:

- Transactional outbox closes the gap between business-state commit and durable intent to deliver; it does not create universal exactly-once delivery.
- The outbox identity and external idempotency identity SHOULD remain stable across redelivery.
- If the external outcome is ambiguous and an authoritative reconciliation interface exists, reconcile before making another consequential external call.
- A successful external deduplication response can be evidence that redelivery was safely absorbed, but final proof SHOULD still record the logical operation identity and external status.

Report #014 validates this rule with PostgreSQL 17.6 for business/outbox atomicity and a synthetic external effect ledger reached through separate transactions. An unsafe recovery path used a new request identity after ACK loss and produced two external effects. Stable-id redelivery was deduplicated to one effect, and reconcile-before-retry closed the outbox without a second external call.

## Non-goals

TTP v1.0 is not:

- a claim of exactly-once delivery in arbitrary distributed systems;
- a replacement for database transactions or consensus;
- a PKI, IAM or cryptographic standard;
- an OpenAI Agents SDK feature specification;
- an external security certification;
- a proof that arbitrary agents are safe.

## Evidence base

TTP v1.0 is a RESONANCE synthesis derived from the reproducible experiments in Verified Reports #003–#010:

- #003 Recovery Under Ambiguity
- #004 Ambiguous Reconciliation
- #005 Conflicting Evidence
- #006 Evidence Authority Failure
- #007 Revoked Authority / Key Rotation
- #008 Stale Trust Registry
- #009 Revocation Race / TOCTOU
- #010 Distributed Commit Race

Validation then moved from isolated invariants into composed and concrete execution layers:

- **#011 TTP v1.0 End-to-End Adversarial Run** — compounded timeout, stale evidence, revoked authority, stale trust and a competing writer in one trajectory; unsafe path produced three effects, TTP preserved one while covering all eight stages.
- **#012 PostgreSQL Transactional Trust Adapter** — two independent real PostgreSQL connections read the same `ABSENT / version=100` snapshot; unconditional writes produced two effects, while a version-bound conditional mutation produced one winner, one precondition failure and one final effect.
- **#013 PostgreSQL Isolation-Level Matrix** — the same stale-writer race was executed at `READ COMMITTED`, `REPEATABLE READ` and `SERIALIZABLE`; storage signals differed, but fresh reconciliation preserved one effect and prevented a transaction-retry signal from becoming a blind business replay.
- **#014 PostgreSQL Transactional Outbox / External Effect Boundary** — business state and durable delivery intent were committed together; ACK loss with a new request identity reproduced two external effects, while stable-id redelivery and reconcile-before-retry each preserved one external effect.

These reports validate specific protocol properties under their declared scope; they are not general production safety certifications.

## Canonical short form

# **OBSERVE → VERIFY → AUTHORIZE → BIND → COMPARE → COMMIT → RECONCILE → PROVE**
