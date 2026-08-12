# RESONANCE Verified Report #022

# Mid-flight Lease Loss / Long-Running Action

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Mid-flight Lease Loss / Long-Running Action v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource service with persistent SQLite effect ledger  
**Lease model:** deterministic logical time, 60-second benchmark TTL  
**GitHub Actions run:** `31554618911`  
**Evidence artifact:** `resonance-midflight-lease-loss-v1.0`  
**Artifact ID:** `9125526467`  
**Artifact digest:** `sha256:0dd9aa7c11547a916b75e6c739ba8d009e233de8f5bafbf9e4cb6412cab973c6`

## Result

# **10 / 10 — Mid-flight authority protocol passes**

Verified #020 showed that a stale worker must be fenced after ownership changes. Verified #021 showed that a delayed heartbeat must not resurrect a superseded ownership epoch. Report #022 moves the race into the middle of a legitimate long-running action:

> What if Worker A was authorized when the work started, but loses the lease before the irreversible commit?

The benchmark demonstrates that a valid start authorization can become stale before completion. Reusing the start proof duplicated the external effect; commit-time revalidation or resource-side fencing preserved one effect.

## Timeline

```text
T=1000
Worker A acquires lease
owner=A / fence=1 / version=1 / expires=1060

T=1020
A checks authority
AUTHORIZED=true
A starts long-running work

T=1070
A's lease is expired
Worker B takes over
owner=B / fence=2 / version=2 / expires=1130
B commits external effect #1

T=1080
A finishes the work started earlier
```

The critical distinction is between **permission to start** and **permission to commit**.

## Unsafe: start-time authorization is reused at finish

At `T=1020`, A was genuinely current:

```text
owner=A
fence=1
lease_version=1
expires_at=1060
start_authorized=true
```

No fault is injected into that decision. The work begins legally.

After takeover, B commits with fence `2`. The unsafe path then lets A finish by reusing its old start proof and does not enforce a fence at the external resource:

```text
B / fence 2 → effect #1
A / fence 1 → effect #2

final remote:
effect_count=2
status=conflict
```

# **AUTHORIZED AT START ≠ AUTHORIZED AT COMMIT**

The start decision was correct. The final mutation was no longer legal.

## Safe A: commit-time revalidation

Before A is allowed to touch the consequential external boundary at `T=1080`, the worker revalidates the exact epoch that authorized the start:

```text
resource_id
+ owner=A
+ fence=1
+ lease_version=1
+ lease still valid at commit time
```

The current coordinator state is now:

```text
owner=B
fence=2
lease_version=2
expires_at=1130
```

The result is:

```text
finish_authorized=false
worker_a_write_made=false
final_effect_count=1
```

This is a clean pre-call safety result: the work may have completed computationally, but the old worker no longer owns the right to make the irreversible state transition.

## Safe B: resource-side fencing at final commit

The second safe path deliberately skips the coordinator recheck and lets A attempt the external commit anyway.

The protected HTTP resource has already accepted B's token `2`:

```text
highest_fence=2
```

A presents its original token `1`:

```text
presented_fence=1
highest_fence=2
→ HTTP 409
→ delivery=fenced_out
→ effect_count=1
```

This proves that the final resource boundary must evaluate the current execution epoch, not merely trust that the caller was valid when work began.

## Control: a valid long action can still complete

The benchmark also tests a non-race control. A starts at `T=1020` and finishes at `T=1050`, before its lease expires at `T=1060`.

```text
start_authorized=true
finish_authorized=true
HTTP 200 / applied
effect_count=1
```

The protocol therefore does not reject long-running work as a category. It rejects stale authority at the irreversible boundary.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Start was legitimately authorized and takeover advanced the epoch | PASS | 2/2 |
| Start-time-only authority duplicated the effect after lease loss | PASS | 2/2 |
| Commit-time revalidation blocked stale A before the external call | PASS | 2/2 |
| Resource-side fence rejected A at final commit | PASS | 2/2 |
| Valid completion before expiry still succeeded | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **AUTHORIZED AT START DOES NOT IMPLY AUTHORIZED AT COMMIT**

# **LONG-RUNNING CONSEQUENTIAL WORK MUST REVALIDATE OR PRESENT A CURRENT FENCING EPOCH AT THE COMMIT BOUNDARY**

# **LEASE LOSS WHILE WORK IS IN FLIGHT IS AN AUTHORITY-LIFECYCLE TRANSITION**

# **RESOURCE-SIDE FENCING IS THE FINAL GUARD AGAINST A STALE COMPLETION**

## TTP mid-flight authority rule

```text
ACQUIRE A / FENCE N / VERSION V
          ↓
START AUTHORIZATION
          ↓
LONG-RUNNING WORK
          ↓
LEASE EXPIRES
          ↓
TAKEOVER B / FENCE N+1 / VERSION V+1
          ↓
A FINISHES OLD WORK
          ↓
COMMIT AUTHORITY CHECK
   ├─ old epoch no longer current → STOP / RECONCILE
   └─ still current              → continue
          ↓
EXTERNAL COMMIT PRESENTS FENCE
          ↓
RESOURCE COMPARES HIGHEST FENCE
   ├─ stale → FENCED_OUT
   └─ current → COMMIT
          ↓
PROVE
```

## Relationship to #020–#022

```text
#020 → old worker must not act after a newer execution epoch exists
#021 → late heartbeat must not resurrect the old epoch
#022 → valid start authority must not survive silently past mid-flight lease loss
```

The broader rule becomes:

```text
LONG-RUNNING EXECUTION AUTHORITY =
  valid start decision
+ current ownership at commit
+ monotonic fencing epoch
+ resource-side enforcement
+ recovery evidence
```

## Interpretation boundary

This is a deterministic local benchmark. PostgreSQL is the lease coordinator and a separate local HTTP service is the protected resource boundary. Logical timestamps are injected by the harness; the benchmark does not emulate a real scheduler or arbitrary network delay.

It does **not** claim:

- a vulnerability in PostgreSQL or another external product;
- a universal lease or job-processing algorithm;
- exactly-once execution;
- production safety certification;
- that every long-running task requires the same lease semantics;
- arbitrary agent safety.

The 60-second TTL is a benchmark parameter, not a production recommendation.

## Reproducibility

Benchmark specification:

`benchmarks/midflight-lease-loss-v1.0/README.md`

Harness:

`benchmarks/midflight-lease-loss-v1.0/run_midflight_lease_loss.py`

External HTTP resource:

`benchmarks/midflight-lease-loss-v1.0/external_service.py`

Workflow:

`.github/workflows/benchmark-midflight-lease-loss.yml`

Machine-readable result:

`reports/verified/022-midflight-lease-loss/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31554618911`

## Verdict

**Worker A was genuinely authorized when it started the long-running action. Its lease then expired, Worker B took over with a higher fencing token and committed. Reusing A's old start authorization produced a second external effect. Revalidating authority at commit time stopped A before the call, while resource-side fencing independently rejected A's stale token with HTTP 409.**

---

**RESONANCE Verified Report #022**  
**Status:** Reproducible deterministic mid-flight lease-loss run  
**Score:** 10/10  
**Unsafe effects:** 2  
**Commit-recheck effects:** 1  
**Resource-fenced effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
