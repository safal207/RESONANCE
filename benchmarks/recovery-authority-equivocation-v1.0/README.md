# RESONANCE Recovery Authority Equivocation / Conflicting Resolution Fork v1.0

Verified #038 used an independent recovery authority to resolve a same-epoch membership-authority fork. This benchmark asks whether that recovery authority can itself fork recovery history.

## Law

> **AUTHENTIC RECOVERY RECORD ≠ UNIQUE RECOVERY HISTORY.**

## Scenario

A membership-authority equivocation already exists at epoch 2:

- `M2-A` = set-B / epoch 2;
- `M2-B` = set-C / epoch 2;
- both records are authentic and both digests are preserved as disputed evidence.

The same recovery authority then signs two different epoch-3 resolution records:

- `R3-A` = set-D / recovery epoch 3;
- `R3-B` = set-E / recovery epoch 3;
- both bind the same disputed `M2-A` and `M2-B` digests;
- both authenticate under the same recovery-authority key;
- each has a locally valid 2-of-3 quorum over the same current H9 authority head.

An isolated verifier can therefore accept either branch. A cross-view verifier must treat same recovery issuer + same recovery epoch + same dispute set + different authentic recovery digest as equivocation evidence and hold both branches.

Recovery uses a distinct governance-resolution authority at epoch 4, explicitly binding both conflicting recovery digests before a fresh quorum may authorize consequence.

## Score

Five checks × 2 points = 10/10.

1. Both epoch-3 recovery branches authenticate and validate locally.
2. Isolated verifier accepts one branch and commits one external effect.
3. Cross-view comparison detects recovery-authority equivocation.
4. Safe verifier holds both disputed recovery branches with zero effects.
5. Epoch-4 governance recovery binds both fork digests and restores liveness exactly once.

The HMAC identities are deterministic test fixtures, not production PKI. The benchmark is not a production safety certification or a vulnerability claim.