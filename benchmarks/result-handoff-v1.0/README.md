# RESONANCE Result Handoff / Stale Work Salvage v1.0

This benchmark tests whether useful work produced by a worker that lost lease authority can be salvaged without allowing the stale producer to publish the consequential effect itself.

## Core question

Worker A is valid at start under fence `N`, then loses the lease to Worker B / fence `N+1` while computing. A still produces an immutable result artifact.

Can B safely adopt that artifact without inheriting A's stale execution authority?

## Model

```text
A / fence N
  ↓
AUTHORIZED START
  ↓
COMPUTE
  ↓
LEASE LOSS
  ↓
B / fence N+1
  ↓
A finishes immutable artifact digest D
```

The benchmark separates:

```text
artifact production
≠ artifact adoption
≠ consequential commit
```

## Unsafe path

A's stale READY artifact auto-publishes with the producer's old fence. B later adopts and publishes the same digest as the current owner. Without fencing on that unsafe boundary, one logical result creates two external effects.

## Safe path

1. A may write a READY immutable artifact after losing ownership.
2. No external effect is created by artifact production.
3. B adopts with a CAS-style transaction that binds:
   - exact artifact digest;
   - artifact state READY;
   - current owner B;
   - current fence/version;
   - current lease validity.
4. B publishes using B's current fencing token.
5. A's stale publish attempt using the producer fence is rejected by the external resource.

A mismatched digest is not adopted.

## Invariants

- **STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE.**
- **RESULT ADOPTION MUST BIND THE EXACT ARTIFACT DIGEST AND PRODUCER EPOCH TO THE CURRENT OWNER EPOCH.**
- **READY ARTIFACT IS DATA, NOT COMMIT AUTHORITY.**
- **THE CONSEQUENTIAL COMMIT MUST PRESENT THE ADOPTER'S CURRENT FENCING TOKEN, NOT THE PRODUCER'S STALE TOKEN.**

## Run

```bash
python benchmarks/result-handoff-v1.0/run_result_handoff.py
```

The GitHub Actions workflow runs PostgreSQL 17.6 and a separate Dockerized HTTP resource with persistent SQLite effect state.

This is a deterministic local protocol benchmark, not a universal job handoff algorithm, external product vulnerability claim, exactly-once guarantee or production safety certification.
