# Governance Resolution Equivocation / Conflicting Finality v1.0

Verified #039 used a distinct governance-resolution authority to recover from recovery-authority equivocation. This benchmark asks whether that governance layer can itself fork finality.

## Law

**AUTHENTIC GOVERNANCE RESOLUTION ≠ UNIQUE FINALITY.**

## Scenario

The inherited recovery fork is preserved as two digests from Verified #039. One governance issuer signs two different epoch-4 resolutions of exactly that same inherited dispute:

- `G4-A`: `set-F`, epoch 4, `W16/W17/W18`, threshold 2.
- `G4-B`: `set-G`, epoch 4, `W19/W20/W21`, threshold 2.

Both are authentic. Both carry locally valid 2-of-3 witness certificates over H9. An isolated verifier can therefore accept either branch.

The safe path compares peer governance views. Same issuer + same governance epoch + same inherited recovery-fork set + different authentic governance digests is equivocation evidence, so every disputed epoch-4 branch is held before consequence and the governance issuer is quarantined.

Recovery advances to epoch 5 under a separate constitutional/root authority. The epoch-5 record must bind both conflicting governance-resolution digests before a fresh quorum can restore liveness.

## Score

Five checks × 2 points = 10.

This is a deterministic research fixture using test-only HMAC identities, PostgreSQL and a Dockerized HTTP effect boundary. It is not production safety certification or a vulnerability claim.