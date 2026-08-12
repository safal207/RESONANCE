# TTP Mid-flight Lease Loss / Commit Authority Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #022.

## Problem

Authority can change while legitimate work is still running.

```text
A owns fence N / version V
       ↓
start authorization succeeds
       ↓
long-running work begins
       ↓
lease expires
       ↓
B takes over → fence N+1 / version V+1
       ↓
A finishes old work
```

The fact that A was authorized at the beginning does not prove that A still owns the right to perform the final consequential mutation.

## New invariants

### I47 — Authorized at start does not imply authorized at commit

A start-time authorization is evidence about one point in the trajectory. It must not be treated as a timeless execution capability.

### I48 — Lease loss while work is in flight invalidates the old commit authority

Once a newer ownership epoch exists, the old worker may finish computation but must not silently reuse the old epoch to commit.

```text
work completed
≠ commit authorized
```

### I49 — Long-running consequential work must bind the final mutation to current authority

Before an irreversible commit, the execution path SHOULD either:

1. revalidate current owner + fencing token + lease version + validity; or
2. present the fencing token to a protected resource that rejects stale epochs.

For high-impact effects, resource-side fencing is the stronger final boundary because coordinator rechecks can themselves become stale before the external mutation.

### I50 — Proof must preserve both the start epoch and the commit epoch

A proof bundle for long-running work SHOULD distinguish:

```text
start authorization
start owner / fence / version / expiry
        ↓
work interval
        ↓
commit-time observed owner / fence / version
        ↓
resource-side fence decision
        ↓
final effect
```

Without both endpoints, a successful final output can hide stale execution authority.

## Canonical recovery path

```text
ACQUIRE A / FENCE N / VERSION V
          ↓
AUTHORIZE START
          ↓
RUN WORK
          ↓
OWNERSHIP MAY CHANGE
          ↓
REVALIDATE COMMIT AUTHORITY
   ├─ stale → STOP / RECONCILE / DISCARD OR TRANSFER RESULT
   └─ current → continue
          ↓
PRESENT FENCING TOKEN TO RESOURCE
          ↓
RESOURCE COMPARES HIGHEST FENCE
   ├─ stale → FENCED_OUT
   └─ current → COMMIT
          ↓
PROVE START + FINISH AUTHORITY TRAJECTORY
```

## Proof fields

A TTP proof bundle for long-running lease-backed execution SHOULD preserve:

- resource identity;
- worker identity;
- start decision time;
- start owner;
- start fencing token;
- start lease version and expiry;
- finish / commit decision time;
- ownership state observed at commit;
- commit-time authorization result;
- fencing token presented to the protected resource;
- highest resource-side fence observed;
- final external effect count/status;
- recovery / handoff / reconciliation result.

## Relationship to previous ownership rules

```text
#020 stale worker fencing:
old worker must not commit after a newer execution epoch exists

#021 delayed heartbeat:
old heartbeat must not resurrect the superseded epoch

#022 mid-flight lease loss:
a worker legitimately authorized at start must re-prove authority at final commit
```

## Interpretation boundary

This rule is synthesized from a deterministic PostgreSQL + local HTTP benchmark. It does not prescribe a universal job scheduler, lease duration, distributed transaction protocol, or one exact handoff strategy for unfinished work.
