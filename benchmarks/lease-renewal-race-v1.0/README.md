# RESONANCE Lease Renewal Race / Delayed Heartbeat v1.0

Verified Report #021 extends the stale-worker fencing work from ownership takeover to **lease renewal itself**.

## Question

What happens when Worker A's heartbeat is delayed beyond lease expiry, Worker B takes ownership with a newer fencing token, and then A's old heartbeat arrives?

```text
A acquires lease / fence N
        ↓
heartbeat delayed
        ↓
lease expires
        ↓
B takeover / fence N+1
        ↓
B acts
        ↓
late heartbeat from A arrives
```

The benchmark separates four paths.

### Unsafe — blind renewal

A delayed heartbeat writes its cached lease snapshot over the current coordinator row without comparing owner, fence, lease version, or expiry.

Expected result:

```text
B takeover succeeds
B effect applied
late A heartbeat resurrects owner=A / old fence
A acts again
→ 2 effects
```

### Safe — compare-and-renew

Heartbeat renewal is one conditional mutation bound to:

```text
resource_id
+ owner
+ fencing token
+ lease version
+ lease still active
```

A stale heartbeat after B's takeover must update **zero rows**. Zero rows is a safety result, not permission to overwrite ownership.

### Defense in depth — resource fencing

The benchmark then deliberately corrupts coordinator ownership with the unsafe heartbeat but keeps resource-side fencing enabled. The external resource has already seen B's higher token, so A's older token must be rejected with HTTP 409 / `fenced_out`.

### Control — valid heartbeat

A current, non-expired owner with the exact expected owner/fence/version must still be able to renew normally. This proves the safe rule rejects stale renewal rather than disabling renewal altogether.

## Core invariants

- **Late heartbeat must not resurrect a superseded ownership epoch.**
- **Lease renewal must compare owner + fencing token + lease version + expiry in the renewal mutation.**
- **Zero-row compare-and-renew is stale-owner evidence.**
- **Resource-side fencing remains the final guard if coordinator state is corrupted.**

## Environment

- PostgreSQL 17.6 coordination state
- two logical workers, A and B
- deterministic lease time model
- separate Dockerized HTTP resource service
- persistent SQLite resource ledger
- Python 3.12
- psycopg 3.2.9

## Run locally

```bash
export DATABASE_URL='postgresql://resonance:resonance@127.0.0.1:5432/resonance'
python -m pip install 'psycopg[binary]==3.2.9'
docker pull python:3.12-slim
python benchmarks/lease-renewal-race-v1.0/run_lease_renewal_race.py
```

The harness writes `result.json` and `RESULT.md` under `benchmark-results/lease-renewal-race-v1.0/`.

## Interpretation boundary

This is a deterministic local distributed-systems benchmark. It does not certify a production lease service, consensus implementation, scheduler, queue, cloud lock service, or arbitrary agent system. The logical timestamps and 60-second TTL are benchmark parameters, not production recommendations.
