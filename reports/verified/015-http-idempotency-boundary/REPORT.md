# RESONANCE Verified Report #015

# HTTP Idempotency Boundary

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** HTTP Idempotency Boundary v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** separate Dockerized HTTP service  
**GitHub Actions run:** `31465000594`  
**Evidence artifact:** `resonance-http-idempotency-boundary-v1.0`  
**Artifact ID:** `9091169764`  
**Artifact digest:** `sha256:afd38661d64ccc3e04f1fa663c0c45a536e564fa872153d03424bc2c0d8b3afd`

## Result

# **10 / 10 — HTTP idempotency boundary protocol passes**

Report #014 crossed the database/external-effect boundary with a synthetic external ledger. Report #015 moves that boundary onto a real HTTP connection and a separate Docker container.

The topology is:

```text
PostgreSQL 17.6
  business state + outbox intent
            ↓
       outbox worker
            ↓ HTTP
separate Docker container
  external effect service
```

The external service owns its effect state in its own process memory. PostgreSQL cannot commit, roll back or inspect that state directly.

## Real ambiguous acknowledgement

The external HTTP service supports one deterministic failure injection:

```text
POST /effects
      ↓
remote effect is recorded
      ↓
server closes the TCP/HTTP connection
before returning a response
      ↓
client observes RemoteDisconnected
      ↓
ACK_UNKNOWN
```

This is the central distinction in the benchmark:

# **HTTP ACK LOST ≠ REMOTE EFFECT ABSENT**

The first safe POST therefore ended with:

```text
client outcome = ACK_UNKNOWN
error          = RemoteDisconnected
```

while a subsequent authoritative HTTP status query already observed:

```text
status       = COMMITTED
effect_count = 1
post_requests = 1
ack_drops     = 1
```

The client did not receive success, but the remote effect existed.

## Unsafe control: retry identity changes

The business transition and outbox intent committed once:

```text
operation = COMMITTED
version   = 101
outbox    = PENDING
```

The worker then sent:

```text
POST #1
Idempotency-Key: http-unsafe:attempt:1
→ remote effect applied
→ HTTP response lost
→ ACK_UNKNOWN
```

Unsafe recovery generated a new request identity:

```text
POST #2
Idempotency-Key: http-unsafe:attempt:2
→ HTTP 200
→ applied
```

Authoritative remote status then reported:

```text
status        = CONFLICT
post_requests = 2
effect_count  = 2
```

The database still contained only one business transition. The duplicate appeared beyond the database boundary because the retry changed logical effect identity.

## Safe redelivery: a real second POST is deduplicated

The safe redelivery case used one stable key:

```text
http-safe-redelivery-op:effect:v1
```

Attempt 1:

```text
POST #1
→ remote effect applied
→ connection closed before response
→ client ACK_UNKNOWN
```

An HTTP status query immediately after the lost acknowledgement observed:

```text
COMMITTED / effect_count=1 / post_requests=1
```

The benchmark then deliberately performed a **real second HTTP POST** with the same idempotency identity:

```text
POST #2
same Idempotency-Key
→ HTTP 200
→ delivery = DEDUPLICATED
```

Final remote state:

```text
post_requests = 2
remote effects = 1
status         = COMMITTED
```

Final outbox state:

```text
delivery_attempts = 2
status            = DELIVERED
```

Therefore:

# **MULTIPLE HTTP DELIVERY ATTEMPTS ≠ MULTIPLE COMMITTED EFFECTS**

when the external contract enforces a stable idempotency identity.

## Safer path: reconcile before making a second POST

The third scenario used the same ACK-loss injection, but changed recovery policy.

After the first POST ended in `RemoteDisconnected`, the worker called:

```text
GET /status/http-safe-reconcile-op
```

Observed:

```text
status        = COMMITTED
effect_count  = 1
post_requests = 1
```

The worker therefore made no second consequential POST:

```text
second_post_made = false
```

and closed the outbox as delivered with one delivery attempt.

This is the network-boundary form of the TTP recovery law:

# **ACK_UNKNOWN → RECONCILE REMOTE STATE BEFORE RE-EXECUTION**

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Real PostgreSQL + separate HTTP service boundary | PASS | 2/2 |
| Unsafe ACK-loss + new identity duplicate reproduced | PASS | 2/2 |
| Stable key deduped a real HTTP redelivery | PASS | 2/2 |
| HTTP status reconciliation avoided a second POST | PASS | 2/2 |
| Final TTP HTTP-boundary invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## Container evidence

The HTTP service health response reported:

```text
service          = resonance-external-http
service_instance = external-http-container
hostname         = 3f9f87866627
pid              = 1
```

HTTP service image:

```text
python:3.12-slim
python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36
```

PostgreSQL image:

```text
postgres:17.6-alpine
sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94
```

The service ran as a separate Docker container and the benchmark reached it through `http://127.0.0.1:18080`.

## TTP network-boundary rule

The adapter path now becomes:

```text
OBSERVE / VERIFY / AUTHORIZE / BIND
              ↓
BUSINESS TRANSACTION
  state transition + outbox intent
              ↓
            COMMIT
              ↓
        OUTBOX WORKER
              ↓
    stable logical effect ID
              ↓
          HTTP POST
        ├─ ACK → DELIVERED
        └─ ACK_UNKNOWN
                ↓
          REMOTE RECONCILE
          ├─ COMMITTED → DELIVERED
          ├─ ABSENT    → fresh POST may proceed
          └─ UNKNOWN   → HOLD / reconcile again
              ↓
            PROVE
```

## New invariants

# **HTTP ACK LOST ≠ REMOTE EFFECT ABSENT**

# **SAME LOGICAL EFFECT → SAME IDEMPOTENCY IDENTITY**

# **REAL HTTP REDELIVERY MAY BE SAFE WHEN REMOTE DEDUPE IS ENFORCED**

# **REMOTE STATUS SHOULD DOMINATE TRANSPORT FAILURE WHEN IT IS AUTHORITATIVE**

# **NETWORK EVIDENCE BELONGS IN THE TRANSACTION TRAJECTORY**

The proof path now includes local database state, outbox state, HTTP request identity, transport outcome, remote status and final remote effect count.

## Interpretation boundary

The network boundary is real, but the external service remains a local benchmark service rather than a production provider.

This report does **not** prove or certify:

- universal exactly-once HTTP semantics;
- production payment-provider idempotency;
- internet-scale network partitions;
- retries across load balancers, proxies or regional failover;
- durable remote state after external-service restart;
- authentication or authorization of the HTTP endpoint;
- broker or webhook delivery guarantees;
- arbitrary agent safety.

The benchmark validates one explicit local TTP HTTP adapter contract.

## Reproducibility

Benchmark specification:

`benchmarks/http-idempotency-boundary-v1.0/README.md`

External HTTP service:

`benchmarks/http-idempotency-boundary-v1.0/external_service.py`

Harness:

`benchmarks/http-idempotency-boundary-v1.0/run_http_boundary.py`

Workflow:

`.github/workflows/benchmark-http-idempotency-boundary.yml`

Machine-readable result:

`reports/verified/015-http-idempotency-boundary/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31465000594`

## Verdict

**A real HTTP acknowledgement was lost after the remote container had already committed an effect. Retrying with a new identity produced two remote effects. Reusing one stable idempotency identity caused a real second POST to be deduplicated, while reconcile-before-retry discovered the committed remote effect and avoided a second POST entirely. Both safe paths preserved one database transition and one remote effect.**

---

**RESONANCE Verified Report #015**  
**Status:** Reproducible real HTTP boundary run  
**Score:** 10/10  
**Unsafe remote effects:** 2  
**Safe remote effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
