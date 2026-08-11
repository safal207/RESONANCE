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

- One logical operation SHOULD map to at most one committed effect.
- Idempotency keys, compare-and-swap, transactions, leases or equivalent mechanisms MAY implement this property.
- TTP does not prescribe one storage technology.

### 7. RECONCILE

After ambiguous outcomes, determine what actually happened before retrying.

```text
UNKNOWN
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
- Retry must re-enter verification and execution binding; a prior authorization is not automatically reusable.

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
reconciliation observations
final invariant result
```

Rules:

- Tool success alone is not proof of state correctness.
- Correct final state without causal evidence is incomplete verification.
- Safety-relevant conflicts and rejected writes belong in the evidence trail.

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
  ├─ mismatch → CONFLICT → RECONCILE
  └─ match
       ↓
     COMMIT
       ├─ acknowledged → PROVE → COMPLETE
       └─ ambiguous    → UNKNOWN → RECONCILE
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

### TTP-Deep

For high-impact or adversarial environments:

- all TTP-Standard requirements
- independent/peer verification
- stronger provenance / attestations
- isolated execution environment
- replayable evidence
- explicit recovery/escalation path

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

The next validation step is an end-to-end adversarial benchmark that composes these hazards in one trajectory rather than testing each invariant separately.

## Canonical short form

# **OBSERVE → VERIFY → AUTHORIZE → BIND → COMPARE → COMMIT → RECONCILE → PROVE**
