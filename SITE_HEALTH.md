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
STATIC UI / MEDIA CONTRACT
  ├─ image alt + intrinsic width/height
  ├─ responsive large-image delivery
  ├─ local image existence + file-size budget
  └─ explicit button types
  ↓
LOCAL EXPERIENCE CONTRACT
  ├─ Lighthouse mobile representative routes
  ├─ Lighthouse desktop key routes
  ├─ rendered UI geometry checks
  └─ versioned performance/accessibility budgets
  ↓
GITHUB PAGES DEPLOYMENT
  ↓
LIVE EXPERIENCE AUDIT
  ├─ Lighthouse against the public deployed site
  └─ rendered UI geometry re-check
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

## UI Geometry Contract

Site health now treats rendered geometry as a release property, not only a visual preference.

### Interactive controls

- Primary CTA controls use a **44 px minimum design target** for the interactive height/hit area.
- Lighthouse `target-size` / `tap-targets` audits are treated as browser-level release guards whenever the pinned Lighthouse profile exposes them.
- Buttons must declare an explicit `type` so their behavior does not change accidentally when markup moves into forms.
- Contrast remains a hard browser-level check because a correctly sized control that cannot be read is still a failed control.

### Images and media

Every image introduced into the journal must:

- declare an `alt` attribute;
- declare positive intrinsic `width` and `height` so the browser can reserve layout space before the asset arrives;
- keep local source files at or below **750 KiB per image** in the initial release budget;
- provide `srcset` when the declared intrinsic width is **960 px or larger**;
- pass Lighthouse image aspect-ratio and responsive-image audits when those audits apply;
- preserve the release CLS budget so image loading does not move surrounding content unexpectedly.

Pages without raster images legitimately report image-specific browser checks as `n/a`.

### Responsive geometry

Current Lighthouse profiles cover representative mobile and desktop rendering. The next visual-regression layer will add stable screenshot viewports for:

- phone: approximately **390 × 844**;
- tablet: approximately **768 × 1024**;
- desktop: approximately **1440 × 900**.

That layer should detect horizontal overflow, clipped controls, unexpected wrapping, oversized/undersized media, and EN/RU/zh-CN layout drift that category scores alone may miss.

## Initial Lighthouse budgets

| Profile | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mobile | ≥ 80 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 3500 ms | ≤ 300 ms | ≤ 0.10 |
| Desktop | ≥ 90 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 2500 ms | ≤ 200 ms | ≤ 0.10 |

These are release budgets, not claims about search ranking or field Core Web Vitals. Budgets should be tightened only after stable baselines exist across multiple runs.

## Evidence artifacts

Each pull-request Site Health run produces:

- raw Lighthouse JSON reports;
- human-readable Lighthouse HTML reports;
- `lighthouse-summary.json` / `.md`;
- `ui-geometry-summary.json` / `.md`;
- `ui-markup-summary.json` / `.md`;
- GitHub Actions job summary;
- one combined PR Site Health comment.

The live audit adds `ui-geometry-live-summary.json` / `.md` against the deployed GitHub Pages site.

Artifacts are retained for 90 days in the initial implementation.

## Integrity boundary

A Lighthouse score or geometry check is a lab measurement for a particular browser profile and run. It does **not** prove:

- Google ranking;
- production field Core Web Vitals;
- identical rendering for every reader/device/network;
- conversion or business impact;
- editorial correctness;
- visual taste or brand quality.

Those require separate evidence.

## Next useful site-quality layers

Prioritized after the Lighthouse + geometry baseline is stable:

1. **Multilingual visual regression** — screenshot key EN/RU/zh-CN pages at stable phone/tablet/desktop viewports and detect meaningful layout drift.
2. **Corrections + version history** — expose how articles change and why.
3. **RSS / newsletter feed** — make the journal subscribable outside social platforms.
4. **Privacy-aware analytics** — measure reading and CTA funnels without building invasive identity profiles.
5. **Translation parity contract** — detect when EN/RU/zh-CN siblings drift or a translated article is stale/missing.
6. **External citation-link health** — periodically detect broken or redirected evidence links without blocking every publication on transient third-party failures.
7. **Field performance evidence** — add privacy-safe real-user Web Vitals only if there is enough traffic to interpret them responsibly.
8. **Public health history** — trend Lighthouse, geometry and publication-contract results across releases rather than presenting only the latest run.

The order matters: deterministic publication integrity and visible UI regressions are more important to an evidence-first journal than maximizing a vanity score.
