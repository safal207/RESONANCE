# Graph–Field Prospective Routing A/B — Result 2026-08-15

Status: **PAIRED_OBSERVED / one real pair / calibration confidence INSUFFICIENT**

Experiment: `gfd-routing-ab-2026-08-15-001`

This result is separate from the pre-outcome freeze contract. It records what was observed after the candidate set, routing policies and utility rubric had already been committed and machine-verified.

## 1. Freeze evidence

Pre-experiment GFD revision:

```text
5aef5b4703da07ca508f59b978056a87e8ac959b
```

Machine-verified freeze head:

```text
4ad0d9e1f988136d573538005045291bd9b746bb
```

Graph–Field Dynamics workflow run:

```text
31884900733 — SUCCESS
```

Freeze receipt digest:

```text
sha256:07b089e583e6b24c9d6e4544cc1e1537808b4a4e8b85da370f087970c2d5d7dc
```

Frozen selections:

```text
GFD_ORIENTATION_V0_1 → cml-memory-proposal-pressure
field_score = 0.728913

FIFO_READY_NODE → liminaldb-codeql-dependency
ready_since = 2026-07-31T14:45:26Z
```

The freeze contained no outcomes, utilities, winner, advantage or calibration proposal.

## 2. Treatment observation — GFD / CML memory proposal pressure

Observed evidence:

- the CML learning loop is documented as one reviewable memory proposal per eligible merged pull request;
- automatic proposals carry `merge_authority=false`, `execution_authority=false`, `status=proposed`, and require human review;
- idempotency is defined for the same source PR / merge identity;
- seven open proposal PRs were present in the frozen queue: #271, #273, #275, #277, #279, #282 and #284;
- sampled proposals #271, #273 and #284 use the same generated review envelope while preserving different source-specific content.

Finding:

> Review pressure is a queue-level problem, not merely the oldest proposal. The next safe transition is a read-only queue audit/grouping/revalidation pass before spending separate review effort on individual packs.

Non-claims:

- the seven memory packs are not claimed to be semantically duplicate;
- current-main drift does not by itself invalidate historical decision memory;
- no memory proposal was accepted, closed, merged or mutated.

Frozen-rubric raw counters:

```text
actionable_finding = true
affected_work_items = 7
blocked_or_stale_actions_avoided = 0
stale_evidence_drift_found = false
downstream_reviews_or_actions_redirected = 7
```

Normalized dimensions:

```text
useful_finding = 1.0
information_gain = 1.0
blocked_work_avoidance = 0.0
stale_evidence_catch = 0.0
downstream_rework_avoidance = 1.0
```

Observed utility:

```text
U_GFD = 0.75
```

## 3. Baseline observation — FIFO / LiminalDB CodeQL dependency

Observed evidence:

- LiminalDB PR #111 proposes changing `github/codeql-action@v4` to `@v4.37.3`;
- current LiminalDB main at `61b02fc81e0cb5cf1f1ed4658ecff58f683cb728` still uses `github/codeql-action@v4`, so the maintenance intent remains relevant;
- PR #111 was based on `b8cf0528187c6d3fac3b28dbb9e90f1a2fb740e7`;
- current main is seven commits ahead of that base;
- the dependency PR head `f1a5d352cca01c09723063d8eb4db9b1804e0222` and current main have diverged: seven commits on current main versus the one dependency side commit.

Finding:

> The old dependency intent is still relevant, but the old branch is not a current-head proof. The next safe transition is recreate/rebase plus exact-head validation rather than treating the historical PR head as directly merge-ready.

Non-claims:

- no speculative root cause is assigned to GitHub's `mergeable=false` state;
- the CodeQL update is not claimed unnecessary;
- no PR was rebased, recreated or merged by the experiment.

Frozen-rubric raw counters:

```text
actionable_finding = true
affected_work_items = 1
blocked_or_stale_actions_avoided = 1
stale_evidence_drift_found = true
downstream_reviews_or_actions_redirected = 1
```

Normalized dimensions:

```text
useful_finding = 1.0
information_gain = 0.5
blocked_work_avoidance = 0.5
stale_evidence_catch = 1.0
downstream_rework_avoidance = 0.5
```

Observed utility:

```text
U_FIFO = 0.70
```

## 4. First prospective advantage

```text
Adv = U_GFD - U_FIFO
    = 0.75 - 0.70
    = +0.05
```

Result label:

```text
winner = TREATMENT
paired_observation_count = 1
calibration_confidence = INSUFFICIENT
weight_update_allowed = false
```

This is a small positive routing signal. It is not validation that GFD is better than FIFO in general.

## 5. Exact-head result verification

Result head:

```text
8655ee608e51e3d2f91ccdd597da04ae1a0baf87
```

Graph–Field Dynamics workflow:

```text
31885058821 — SUCCESS
```

The run completed 40 focused tests and separately verified:

- the historical P2-1 unpaired boundary;
- the prospective pre-outcome freeze;
- treatment and FIFO selection identities;
- mechanical utility normalization;
- the first real paired outcome;
- a real calibration batch;
- proposal-only calibration authority.

## 6. First real calibration proposal

The existing calibration interface consumed the real paired observation with learning rate `0.05`.

Observed mean advantage:

```text
0.05
```

Proposal:

| Component | Current | Proposed | Delta |
|---|---:|---:|---:|
| divergence | 0.250000000 | 0.249957812 | -0.000042188 |
| uncertainty | 0.200000000 | 0.199991250 | -0.000008750 |
| blast_radius | 0.200000000 | 0.200066250 | +0.000066250 |
| freshness_gap | 0.150000000 | 0.149918438 | -0.000081562 |
| open_pressure | 0.100000000 | 0.100058125 | +0.000058125 |
| opportunity | 0.100000000 | 0.100008125 | +0.000008125 |

The proposal explicitly remains:

```text
mode = ADVISORY_ONLY
authority_granted = false
apply_recommended = false
confidence = INSUFFICIENT
observation_count = 1
```

**No canonical GFD weight has been changed.**

## 7. Interpretation

The useful result is not that GFD "won" by five points.

The useful result is that the system now has a falsifiable closed loop:

```text
pre-outcome graph
→ competing routing policies
→ frozen selections
→ independent real observations
→ mechanically scored utilities
→ explicit advantage
→ bounded calibration proposal
→ NO automatic mutation
```

The first pair suggests that systemic orientation can expose a broader review-efficiency problem than age-only FIFO, while FIFO remains valuable for catching exact stale-head maintenance work.

Both signals are useful and neither policy should be collapsed into the other.

## 8. Next evidence threshold

Calibration v0.2 requires:

```text
1–4 paired observations  → INSUFFICIENT
5–19                     → NASCENT
20+                      → EVALUATE_ON_HOLDOUT
```

Therefore at least four additional prospective paired observations are required before the system may even call the calibration evidence `NASCENT`.

Even then, proposed weights remain non-authorizing and must be evaluated on held-out transitions before any configuration change.
