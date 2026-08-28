# Engineering Signal 019 — Lineage Membership / Selective Historical Disclosure

**Status:** VERIFIED — 2026-08-28

## Signal

T-Trace can now prove that one fully disclosed historical reconciliation cycle belongs to a committed lineage root without revealing every later cycle.

The same proof also demonstrates that the root contains the current/final cycle commitment bound by the supplied fixed-shape `LineageAccumulatorRef`.

```text
validated reconciliation cycles
        ↓
canonical cycle commitments
        ↓
Merkle membership root
   ┌────────────┴────────────┐
   ▼                         ▼
selected historical leaf    current/final leaf
+ sibling path              + sibling path
   └────────────┬────────────┘
                ▼
          one verified root
```

## Fractal Causal Refactoring diagnosis

The previous gate bounded active lineage state through a rolling accumulator. It did not provide a bounded proof that an older cycle belongs to the current lineage.

```text
bounded active state
        ≠
bounded historical membership proof
```

The repair adds a companion Merkle commitment over fully revalidated cycle commitments. It does not change the active accumulator.

## Fail-closed incident

The initial design proved the selected historical leaf, but only copied the current cycle commitment into the anchor. A same-size forged tree could therefore omit the real final cycle.

The repaired proof carries a second path:

```text
current_cycle_commitment_sha256
        ↓ current_cycle_sibling_path
membership root
```

Verification now requires:

```text
selected leaf → root
AND
accumulator-bound final leaf → same root
```

A same-size forged-tree regression fails with `current_cycle_membership_path_invalid`.

## Canonical implementation

```text
repository: safal207/T-Trace
PR:         #27
merge:      9362142146b82bf5b6bd76c204367bdf55c1bfb9
```

The profile adds:

- `LineageMembershipAnchor`;
- domain-separated leaf and node hashing;
- `pairwise-duplicate-last-sha256/v0.1` tree semantics;
- exact-position selected-cycle proof;
- exact-position current/final-cycle proof;
- one-cycle selective disclosure;
- fail-closed `LineageMembershipDecision`.

Before anchoring, the builder revalidates the complete retained chain: every reconciliation, accumulator equation, predecessor link, cycle commitment, contract, domain and final tip.

## Canonical five-cycle fixture

```text
completed cycles:               5
current causal epoch:           10
selected cycle:                 2
selected sibling hashes:        3
current-tip sibling hashes:     3
total sibling hashes:           6
raw intervening cycles:         not disclosed
raw provider evidence:          not embedded
```

```text
current lineage root
6b148062ba9520788ce69ce3e06345f5b2d92b7227059ca04fff24af8603e0f7

selected cycle commitment
21c68488d322af81aaf9b6dd45d8cb451dcd8c05fc1529a99136fd87ca77d2b2

membership anchor
1199fa3933e6bb7028218fe69e1e83166a449b6e57ca221754d60bd9589c1834

membership root
1e727666ce283f8c8b0bff67576838f95d9881c6fd77a2a4730ec4e8835102b8
```

The disclosure cost is reported honestly as two independently checked `O(log n)` paths.

## Verification evidence

Exact PR head:

`4254aa3eb217cc3a273146b7f7eaf5dc066d018f`

```text
PR CI                                  33180213088  SUCCESS
PR Governex -00                        33180213020  SUCCESS
PR Governex -01                        33180213026  SUCCESS
PR Security                            33180213017  SUCCESS
CodeRabbit                                          SUCCESS
```

Post-merge `main`:

```text
CI                                     33180614327  SUCCESS
Governex -00                           33180614230  SUCCESS
Governex -01                           33180614347  SUCCESS
Security                               33180614333  SUCCESS
```

Both exact-head and post-merge CI reported `110 passed`. Post-merge CI also re-ran base T-Trace validation, Portable Causality, Repeated Lineage Compaction and Selective Lineage Disclosure successfully.

## Claim boundary

This establishes structural membership of one fully disclosed historical cycle in a supplied root and binds that root to the supplied current accumulator.

It does **not** establish:

- authenticity of an unsigned anchor;
- non-equivocation by the anchor producer;
- append-only consistency between different roots;
- zero-knowledge privacy;
- capture completeness;
- correctness of the reconciliation policy.

Production authority claims must sign or attest the anchor.

## Next falsifiable question

**Membership-Root Consistency / Anti-Equivocation v0.1**

Can a verifier prove that a later root is an append-only extension of an earlier root without replaying every cycle, while detecting incompatible roots for the same lineage frontier?

This likely requires an append-only transparency-tree consistency proof or a Merkle Mountain Range. The current duplicate-last tree must not be promoted to an anti-equivocation claim without that separate proof.