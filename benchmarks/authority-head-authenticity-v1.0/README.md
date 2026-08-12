# RESONANCE Authority Head Authenticity Benchmark v1.0

This benchmark tests whether a verifier can safely use an authority-generation watermark when the watermark itself may be forged in transit.

## Core law

**FRESHNESS CLAIM ≠ AUTHENTIC FRESHNESS EVIDENCE.**

Report #030 established that a regional authority replica must prove currentness against a monotonic authoritative generation or hold. Report #031 asks what makes that generation claim trustworthy.

## Scenario

- compatibility rule `R1` is active at generation 7
- `region-B` is synchronized at generation 7
- a scoped compatibility proof for `model-v1 → model-v2` is valid and both models return `30`
- origin revokes `R1` and advances to generation 8
- `region-B` remains stale at `R1 / ACTIVE / generation 7`
- origin emits an authenticated head statement for generation 8
- an attacker / broken intermediary mutates the head payload to generation 7 but cannot recompute the MAC

Unsafe verifier:

```text
regional generation = 7
claimed head = 7
→ looks fresh
→ ACCEPT
```

Safe verifier:

```text
verify head MAC + authority domain + key id
→ forged payload fails authentication
→ HOLD
```

With the authentic generation-8 head, the same stale regional replica is rejected as `stale_authority_view`. After propagation, R1 is rejected as revoked. A fresh successor R2 proof at generation 9 succeeds with an authentic generation-9 head.

## Authentication model

The benchmark uses deterministic HMAC-SHA256 with a fixed test key to model head authenticity and binding. This is a protocol fixture, **not** a production PKI design or external security certification.

The signed head payload binds:

- authority namespace
- generation
- current rule id
- current rule digest
- rule status
- successor id

## Out of scope

Replay of an **old but authentic** signed head is deliberately not solved here. #031 isolates forged freshness evidence. Authentic-head rollback / replay requires an additional monotonicity or witness mechanism and is a distinct verification surface.

This benchmark is not a vulnerability claim against PostgreSQL, HMAC, GitHub Actions, or any external product.
