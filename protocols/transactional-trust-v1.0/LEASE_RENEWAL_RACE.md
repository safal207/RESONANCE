# TTP Lease Renewal Race / Delayed Heartbeat Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #021.

## Problem

Lease renewal is itself an authority transition. A heartbeat that was valid when sent can arrive after the ownership epoch it refers to has already expired and been replaced.

```text
A owns fence N / version V
       ↓
heartbeat delayed
       ↓
A expires
       ↓
B takes over → fence N+1 / version V+1
       ↓
late heartbeat from A arrives
```

If renewal blindly overwrites coordinator state, the late heartbeat can resurrect A and regress execution authority.

## New invariants

### I43 — Late heartbeat must not resurrect a superseded ownership epoch

A heartbeat refers to one specific ownership epoch. Once a newer epoch exists, the old heartbeat is stale evidence.

### I44 — Lease renewal must compare owner + fence + lease version + expiry in the renewal mutation

A safe renewal SHOULD be one mutation whose precondition includes the identity and version of the current lease state.

Canonical form:

```text
RENEW
WHERE resource_id = R
  AND owner = A
  AND fence = N
  AND lease_version = V
  AND expires_at >= decision_time
```

A mismatch must not fall back to a blind overwrite.

### I45 — Zero-row compare-and-renew is stale-owner evidence

When the conditional renewal changes zero rows, the caller no longer has evidence that its cached lease is current.

```text
0 rows renewed
≠ transient success
≠ overwrite permission

0 rows renewed
→ STALE / CONFLICT
→ re-observe ownership
```

### I46 — Resource-side fencing remains required across the consequential mutation

Coordinator correctness and resource correctness are separate boundaries. Even if a stale heartbeat corrupts coordinator state, the protected resource SHOULD reject a fencing token older than the highest already accepted token.

```text
coordinator says A / fence N   # may be wrong
resource has seen N+1
A presents N
→ FENCED_OUT
```

## Canonical recovery path

```text
ACQUIRE A / FENCE N / VERSION V
          ↓
HEARTBEAT IN FLIGHT
          ↓
LEASE EXPIRY
          ↓
TAKEOVER B / FENCE N+1 / VERSION V+1
          ↓
LATE HEARTBEAT A
          ↓
COMPARE owner + fence + version + expiry
   ├─ match    → RENEW
   └─ mismatch → STALE / STOP
                    ↓
              RE-OBSERVE OWNER
                    ↓
              EXTERNAL MUTATION
                    ↓
             RESOURCE FENCE CHECK
               ├─ stale → FENCED_OUT
               └─ current → COMMIT
                    ↓
                  PROVE
```

## Proof fields

A TTP proof bundle for lease-backed execution SHOULD preserve:

- resource identity;
- worker identity;
- acquired fencing token;
- lease version;
- lease expiry used for the decision;
- heartbeat send/decision/arrival ordering when available;
- renewal precondition;
- renewal row/result classification;
- takeover/new-owner state;
- fencing token presented to the protected resource;
- highest resource-side fence observed;
- final external effect count/status;
- recovery/reconciliation result.

## Relationship to previous temporal rules

```text
#019 temporal ABA:
old time value must not resurrect retired temporal permission

#020 stale worker fencing:
old worker must not commit after a newer execution epoch exists

#021 delayed heartbeat:
old worker renewal must not resurrect the superseded epoch itself
```

## Interpretation boundary

This is a protocol rule synthesized from a deterministic PostgreSQL + local HTTP benchmark. It does not prescribe one universal lease implementation and does not replace consensus, database transactions, provider-specific concurrency controls, or resource-specific fencing semantics.
