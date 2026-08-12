# RESONANCE Revocation Propagation / Stale Proof Registry Split-Brain Benchmark v1.0

This benchmark tests whether a verifier may authorize a consequential artifact using a stale regional view of compatibility-proof authority after the authoritative registry has revoked that proof rule.

## Core law

**VALIDATION AGAINST A STALE AUTHORITY VIEW ≠ CURRENT AUTHORIZATION.**

## Topology

```text
                 authoritative origin
                 R1 / generation 8 / REVOKED
                         │
              ┌──────────┴──────────┐
              │                     │
       region-A replica      region-B replica
       gen 8 / REVOKED       gen 7 / ACTIVE
              │                     │
           REJECT                 ACCEPT ❌
```

The artifact and compatibility predicate remain semantically valid. The failure is purely authority-view staleness.

## Expected checks

1. With origin and replica synchronized at `generation 7 / ACTIVE`, the proof is accepted and commits one effect.
2. After origin revokes R1 at generation 8 but region B remains at generation 7, the same proof receives split-brain verdicts: updated region A rejects while stale region B accepts and commits.
3. A verifier that requires the replica to meet the authoritative generation watermark rejects region B with `stale_authority_view` and zero effects.
4. After revocation propagates to region B, it converges on `REVOKED / generation 8` and rejects the old proof.
5. A fresh successor proof under active R2 at generation 9 succeeds after propagation and commits one effect.

The benchmark uses PostgreSQL 17.6 for authoritative and regional registry state plus a Dockerized HTTP effect boundary. It is a deterministic protocol benchmark, not production safety certification or a vulnerability claim against PostgreSQL or another external product.
