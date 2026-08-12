# Constitutional Root Authority Replay / Root Currentness v1.0

Verified #040 showed that an authenticated governance-finality issuer can equivocate and that recovery can advance through a separate constitutional/root authority. This benchmark asks the next question: **what if an old but authentic root record is replayed after a newer root epoch is already known?**

## Law under test

> **ROOT AUTHORITY ≠ TIMELESS AUTHORITY.**

A root signature proves origin and integrity of one root record. It does not prove that the record is still the latest live root authority.

## Scenario

```text
historical root C3
root epoch = 3
set-R = {W25,W26,W27}
threshold = 2
authentic ✅
        ↓
current root C5
root epoch = 5
set-H = {W22,W23,W24}
threshold = 2
authentic ✅
        ↓
verifier persists root high-watermark = 5 / digest(C5)
        ↓
attacker/cache replays authentic C3
```

Unsafe verifier behavior:

```text
C3 authentic ✅
old-set QC valid ✅
H9 authentic ✅
→ historical root treated as current
→ one external effect ❌
```

Safe verifier behavior:

```text
presented root epoch = 3
trusted root high-watermark = 5
3 < 5
→ root_authority_rollback_detected
→ 0 effects ✅
```

Fresh `C5` remains live and succeeds exactly once.

## Scorecard

1. Historical C3 and current C5 both authenticate and their local quorums validate — 2 points.
2. Observing C5 establishes a durable monotonic root high-watermark at epoch 5 — 2 points.
3. An unsafe verifier accepts replayed C3 and commits one external effect — 2 points.
4. A root-currentness verifier rejects C3 below the high-watermark with zero effects — 2 points.
5. Fresh C5 passes the same currentness gate and restores liveness exactly once — 2 points.

## Boundary

The benchmark uses deterministic HMAC-SHA256 identities and PostgreSQL as the verifier's local durable checkpoint store. It does **not** claim that the checkpoint storage itself is rollback-resistant; storage rollback was isolated separately in Verified #033. It does not implement production PKI, hardware roots, BFT finality, legal/constitutional governance or external transparency infrastructure.

Run through `.github/workflows/benchmark-constitutional-root-replay.yml`.