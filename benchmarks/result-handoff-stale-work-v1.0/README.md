# Result Handoff / Stale Work Salvage v1.0

This benchmark tests whether useful work produced by a worker that lost execution authority can be salvaged without allowing that stale worker to perform the consequential commit.

## Question

Worker A is legitimately authorized when long-running work starts. A later loses its lease and Worker B becomes current owner with a higher fencing token. A still finishes a useful result artifact.

Can B safely adopt that artifact without treating A's old authority as still current?

## Model

```text
A / fence N starts work
        ↓
lease expires
        ↓
B / fence N+1 takes over
        ↓
A finishes immutable artifact D
        ↓
artifact D is DATA, not commit authority
        ↓
B explicitly adopts D
bind digest + producer epoch + current owner epoch
        ↓
B commits with fence N+1
```

## Unsafe path

A's stale result is auto-published directly using its old execution context. B then legitimately adopts and publishes the same artifact. The external boundary receives the same artifact twice and records two effects.

## Safe path

A stores the artifact as `PRODUCED` with:

- artifact digest;
- producer worker;
- producer fencing token;
- producer lease version;
- production time.

No external effect occurs.

B then adopts the exact digest through a conditional PostgreSQL transition bound to:

- the stored artifact digest;
- producer identity and producer epoch;
- current owner B;
- current fencing token;
- current lease version;
- unexpired current lease.

The artifact becomes `ADOPTED`; B performs the consequential HTTP commit using B's current fencing token. A stale late publish is rejected by resource-side fencing.

## Additional negative test

A modified digest cannot be adopted. The correct digest can still be adopted and committed once.

## Control

A worker that remains current may produce, adopt and commit its own artifact normally.

## Invariants

1. **STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE.**
2. **RESULT HANDOFF MUST BIND ARTIFACT DIGEST + PRODUCER EPOCH + CURRENT ADOPTER EPOCH.**
3. **ADOPTION IS A NEW AUTHORITY TRANSITION, NOT A RETROACTIVE EXTENSION OF PRODUCER AUTHORITY.**
4. **THE CONSEQUENTIAL COMMIT MUST PRESENT THE CURRENT ADOPTER FENCING TOKEN.**

## Components

- PostgreSQL: lease and adoption authority state.
- Dockerized HTTP service: protected consequential resource.
- SQLite inside the HTTP container: durable local effect/fencing evidence.
- Deterministic logical time: benchmark scheduling only.

## Interpretation boundary

This is a deterministic local protocol benchmark. It is not a vulnerability claim, exactly-once guarantee, universal work-stealing algorithm, production scheduler certification or arbitrary agent-safety certification.
