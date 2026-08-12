# RESONANCE Compatibility Proof Revocation Benchmark v1.0

This benchmark tests whether a previously valid model-compatibility proof can still authorize reuse after its rule authority is revoked or its authority epoch advances.

## Core law

**PROOF VALID THEN ≠ PROOF AUTHORIZED NOW.**

The benchmark deliberately keeps the reused artifact semantically correct. The failure is not a wrong numeric result; it is use of a proof whose authorization has expired.

## Scenario

- `model-v1`: `y = min(limit, 2 * price)`
- `model-v2`: `y = min(limit, 2 * price + tax_rate)`
- scoped compatibility predicate: `tax_rate >= 0 AND 2*price >= limit`
- current state: `price=20, limit=30, tax_rate=8`, so both models return `30`
- compatibility rule `R1` is active at authority epoch 1 and issues proof `P1`
- before adoption, `R1` is revoked and successor rule `R2` becomes active at epoch 2

## Expected checks

1. While `R1` is active, `P1` authorizes reuse and commits one correct effect.
2. After revocation, an unsafe verifier that checks only proof contents still accepts `P1` and commits an unauthorized effect.
3. A live-registry verifier rejects the exact same `P1` with zero effects.
4. A fresh proof under active successor `R2` can re-authorize the same historical artifact and commit once.
5. If an active rule's authority epoch advances after proof issuance, the older proof is rejected even though the rule remains active.

This is a deterministic protocol benchmark, not production safety certification or a vulnerability claim against PostgreSQL or any external product.
