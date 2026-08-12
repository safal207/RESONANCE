# RESONANCE Membership Authority Equivocation / Same-Epoch Fork v1.0

This benchmark isolates a same-epoch fork in witness-membership authority.

Two membership records are issued by the same authenticated membership authority for the same membership namespace and the same `set_epoch=2`, with the same predecessor membership digest, but with different member sets and therefore different membership digests:

```text
M2-A: set-B / epoch 2 / {W4,W5,W6}
M2-B: set-C / epoch 2 / {W7,W8,W9}
```

Both records authenticate. The failure is not signature forgery or replay. The authority has created two incompatible histories at the same logical membership epoch.

The benchmark proves:

1. both same-epoch branches authenticate and each has a locally valid 2-of-3 quorum;
2. an isolated verifier shown only fork branch M2-B can authorize and commit one external effect;
3. cross-view comparison detects `membership_authority_equivocation_detected` from same namespace + same issuer + same epoch + same predecessor + different membership digest;
4. disputed branch certificates are held before consequence once equivocation evidence exists;
5. recovery uses a higher epoch membership issued by a separate recovery authority and explicitly binds both conflicting branch digests before a fresh quorum can authorize one effect.

Main law:

> **SAME AUTHORITY + SAME EPOCH + TWO AUTHENTIC MEMBERSHIPS = EQUIVOCATION EVIDENCE.**

Interpretation boundary: deterministic HMAC identities model authenticity only. This benchmark is not production PKI, BFT membership governance or a safety certification.
