# RESONANCE Verified Report #021

# Lease Renewal Race / Delayed Heartbeat

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Lease Renewal Race / Delayed Heartbeat v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource service with persistent SQLite effect ledger  
**Lease model:** deterministic logical time, 60-second benchmark TTL  
**GitHub Actions run:** `31551799739`  
**Evidence artifact:** `resonance-lease-renewal-race-v1.0`  
**Artifact ID:** `9124531164`  
**Artifact digest:** `sha256:7c78f54350d392fae2a508bda16e8cabdf73932a2a2ef59346d9d261fc64068a`

## Result

# **10 / 10 — Delayed-heartbeat lease protocol passes**

Verified #020 showed that a stale worker can survive a takeover and must be fenced at the protected resource. Report #021 moves one step earlier in the ownership lifecycle:

> Can a heartbeat from the old worker arrive after takeover and accidentally resurrect the old ownership epoch itself?

The benchmark demonstrates that it can when renewal blindly overwrites coordinator state, and that compare-and-renew plus resource-side fencing prevents the stale worker from regaining execution authority.

## Timeline

```text
T=1000
Worker A acquires lease
owner=A / fence=1 / version=1 / expires=1060

T=1070
A is expired
Worker B takes over
owner=B / fence=2 / version=2 / expires=1130

T=1075
A's delayed heartbeat finally arrives
```

A current heartbeat is also tested separately and succeeds normally, so the safe protocol does not disable lease renewal.

## Unsafe: delayed heartbeat resurrects the old owner

After B's takeover, B applied one external effect using fencing token `2`.

The unsafe renewal path then treated A's delayed heartbeat as a blind write of A's cached lease snapshot:

```text
before late heartbeat:
owner=B
fence=2
lease_version=2
expires_at=1130

blind late heartbeat from A:
updated_rows=1

result:
owner=A
fence=1
lease_version=2
expires_at=1135
```

The coordinator therefore regressed from the newer ownership epoch back to A's older fence.

With no resource-side fence enforced in this unsafe path, A then executed again:

```text
B / fence 2 → effect #1
A / fence 1 → effect #2

final remote:
effect_count=2
status=conflict
```

# **LATE HEARTBEAT CAN RESURRECT SUPERSEDED OWNERSHIP IF RENEWAL IS A BLIND WRITE**

## Safe A: compare-and-renew

The safe renewal mutation is bound to all of the state that made A the current owner:

```text
resource_id
+ owner=A
+ fence=1
+ lease_version=1
+ lease still active at renewal time
```

After B has taken over, A's delayed heartbeat executes the conditional renewal and affects:

```text
updated_rows = 0
```

The lease remains:

```text
owner=B
fence=2
lease_version=2
expires_at=1130
```

A does not make an external call. Final remote state remains one committed effect.

A zero-row compare-and-renew is therefore a safety success: the heartbeat is stale evidence, not authority to overwrite ownership.

## Safe B: resource-side fencing survives coordinator corruption

The benchmark then deliberately repeats the unsafe blind heartbeat so the coordinator is corrupted again:

```text
coordinator after late heartbeat:
owner=A
fence=1
```

But this time the external resource has already accepted B's fencing token `2` and remembers:

```text
highest_fence=2
```

A's resurrected write presents token `1`:

```text
presented_fence=1
highest_fence=2
→ HTTP 409
→ delivery=fenced_out
→ effect_count=1
```

This proves the distinction between two safety layers:

```text
COMPARE-AND-RENEW
protects coordinator ownership state

RESOURCE-SIDE FENCING
protects the consequential mutation even if coordinator state is wrong
```

## Control: a valid heartbeat still renews

A current Worker A heartbeat at `T=1030`, before expiry, using the exact expected owner/fence/version produced:

```text
updated_rows=1
owner=A
fence=1
lease_version=2
expires_at=1090
```

The current worker then applied one fenced external effect normally.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Takeover advances fence and a current heartbeat can renew | PASS | 2/2 |
| Blind late heartbeat resurrects superseded owner | PASS | 2/2 |
| Resurrected worker duplicates effect without resource fence | PASS | 2/2 |
| Compare-and-renew rejects late heartbeat and preserves B | PASS | 2/2 |
| Resource fence blocks stale A even after coordinator corruption | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **LATE HEARTBEAT MUST NOT RESURRECT A SUPERSEDED OWNERSHIP EPOCH**

# **LEASE RENEWAL MUST COMPARE OWNER + FENCE + LEASE VERSION + EXPIRY IN THE RENEWAL MUTATION**

# **ZERO-ROW COMPARE-AND-RENEW IS STALE-OWNER EVIDENCE, NOT OVERWRITE PERMISSION**

# **RESOURCE-SIDE FENCING REMAINS THE FINAL GUARD IF RENEWAL CORRUPTS COORDINATOR STATE**

## TTP Lease Renewal rule

```text
ACQUIRE
  ↓
OWNER A / FENCE N / LEASE VERSION V
  ↓
HEARTBEAT IN FLIGHT
  ↓
LEASE EXPIRES
  ↓
TAKEOVER
OWNER B / FENCE N+1 / VERSION V+1
  ↓
LATE HEARTBEAT A ARRIVES
  ↓
COMPARE owner + fence + version + expiry
  ├─ mismatch → STALE / 0 rows → STOP
  └─ match    → RENEW
  ↓
MUTATION STILL PRESENTS FENCING TOKEN
  ↓
RESOURCE COMPARES HIGHEST FENCE
  ├─ stale → FENCED_OUT
  └─ current → COMMIT
  ↓
PROVE
```

## Relationship to #019–#021

```text
#019 → old temporal state must not be resurrected by clock rollback
#020 → old execution owner must not act after a newer fencing epoch exists
#021 → old owner heartbeat must not resurrect the superseded ownership epoch itself
```

The broader rule becomes:

```text
DISTRIBUTED EXECUTION AUTHORITY =
  current ownership state
+ monotonic fencing epoch
+ compare-and-renew semantics
+ resource-side fence
+ recovery evidence
```

## Interpretation boundary

This is a deterministic local benchmark. PostgreSQL is the coordination authority and a separate local HTTP service is the protected resource boundary. Logical timestamps are injected by the harness; this does not test a production scheduler, Kubernetes lease implementation, etcd lease implementation, cloud lock service, network partition detector, or consensus protocol.

The benchmark does **not** claim:

- a vulnerability in PostgreSQL or any external product;
- a universal lease algorithm;
- arbitrary distributed mutual exclusion;
- exactly-once execution;
- production readiness or external security certification;
- arbitrary agent safety.

The 60-second TTL is a benchmark parameter, not a production recommendation.

## Reproducibility

Benchmark specification:

`benchmarks/lease-renewal-race-v1.0/README.md`

Harness:

`benchmarks/lease-renewal-race-v1.0/run_lease_renewal_race.py`

External HTTP resource:

`benchmarks/lease-renewal-race-v1.0/external_service.py`

Workflow:

`.github/workflows/benchmark-lease-renewal-race.yml`

Machine-readable result:

`reports/verified/021-lease-renewal-race/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31551799739`

## Verdict

**A delayed heartbeat from Worker A arrived after its lease expired and Worker B had already taken over with a higher fencing token. Blind renewal overwrote the newer coordinator epoch, resurrected A, and produced a second external effect. Compare-and-renew returned zero rows and preserved B as owner, while resource-side fencing rejected stale A with HTTP 409 even when the coordinator was deliberately corrupted.**

---

**RESONANCE Verified Report #021**  
**Status:** Reproducible deterministic lease-renewal run  
**Score:** 10/10  
**Unsafe effects:** 2  
**CAS-renew effects:** 1  
**Resource-fenced effects after coordinator corruption:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
