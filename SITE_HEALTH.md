# RESONANCE Site Health

RESONANCE treats publication quality as evidence that should be reproducible, attributable to a specific run, and separated from claims that the measurement does not support.

## Contract stack

```text
SOURCE
  ↓
PUBLICATION CONTRACT
  ├─ Market OS deterministic tests
  ├─ SEO / canonical / structured-data checks
  └─ internal link integrity
  ↓
LOCAL EXPERIENCE CONTRACT
  ├─ Lighthouse mobile representative routes
  ├─ Lighthouse desktop key routes
  └─ versioned performance/accessibility budgets
  ↓
GITHUB PAGES DEPLOYMENT
  ↓
LIVE EXPERIENCE AUDIT
  └─ Lighthouse against the public deployed site
  ↓
IMMUTABLE WORKFLOW ARTIFACTS
```

## Representative routes

The pull-request Experience Contract measures:

- homepage;
- Article #004 English;
- Article #004 Russian;
- Article #004 Simplified Chinese;
- Open Problems;
- Verified Workflow;
- Site Health / Quality.

Desktop profiling is intentionally narrower (homepage + primary Article #004) to keep CI useful and fast.

The post-deployment Live Experience Audit measures a smaller public subset again to detect deploy/runtime differences.

## Initial Lighthouse budgets

| Profile | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mobile | ≥ 80 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 3500 ms | ≤ 300 ms | ≤ 0.10 |
| Desktop | ≥ 90 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 2500 ms | ≤ 200 ms | ≤ 0.10 |

These are release budgets, not claims about search ranking or field Core Web Vitals. Budgets should be tightened only after stable baselines exist across multiple runs.

## Evidence artifacts

Each Lighthouse run produces:

- raw JSON reports;
- human-readable HTML reports;
- `lighthouse-summary.json`;
- `lighthouse-summary.md`;
- GitHub Actions job summary;
- PR Site Health comment for pull-request audits.

Artifacts are retained for 90 days in the initial implementation.

## Integrity boundary

A Lighthouse score is a lab measurement for a particular browser profile and run. It does **not** prove:

- Google ranking;
- production field Core Web Vitals;
- identical performance for every reader/device/network;
- conversion or business impact;
- editorial correctness.

Those require separate evidence.

## Next useful site-quality layers

Prioritized after the Lighthouse baseline is stable:

1. **Corrections + version history** — expose how articles change and why.
2. **RSS / newsletter feed** — make the journal subscribable outside social platforms.
3. **Privacy-aware analytics** — measure reading and CTA funnels without building invasive identity profiles.
4. **Translation parity contract** — detect when EN/RU/zh-CN siblings drift or a translated article is stale/missing.
5. **Visual regression** — screenshot key pages at stable viewport profiles and review meaningful UI drift.
6. **Field performance evidence** — add privacy-safe real-user Web Vitals only if there is enough traffic to interpret them responsibly.
7. **Public health history** — trend Lighthouse and publication-contract results across releases rather than presenting only the latest run.

The order matters: deterministic publication integrity and correction history are more important to an evidence-first journal than maximizing a vanity score.
