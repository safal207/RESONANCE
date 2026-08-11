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
VISUAL REGRESSION CONTRACT
  ├─ 390×844 phone screenshots
  ├─ 768×1024 tablet screenshots
  ├─ 1440×900 desktop screenshots
  ├─ EN / RU / zh-CN route matrix
  ├─ overflow / clipping / 44×44 primary-target gates
  └─ advisory pixel diff against public main
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

Desktop Lighthouse profiling is intentionally narrower (homepage + primary Article #004) to keep CI useful and fast.

The Visual Regression Contract uses a broader multilingual matrix:

- homepage;
- Article #004 EN / RU / zh-CN;
- Article #005 EN / RU / zh-CN;
- Site Health / Quality;
- each at 390×844, 768×1024 and 1440×900.

That produces 24 candidate screenshots per run plus matching public-main baselines and diff PNGs when a baseline route exists.

The post-deployment Live Experience Audit measures a smaller public subset again to detect deploy/runtime differences.

## UI Geometry Contract

Site health treats rendered geometry as a release property, not only a visual preference.

### Interactive controls

- Primary CTA controls use a **44 px minimum design target** for the interactive width/height hit area.
- The visual contract hard-fails when a visible `<button>` or `.button` control is below 44×44 px.
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

## Visual Regression Contract

Visual Regression v0.3 captures the same important publication surfaces at three fixed reference viewports:

| Profile | Viewport | Purpose |
|---|---:|---|
| Phone | 390 × 844 | Small touch layout, mobile wrapping and CTA geometry |
| Tablet | 768 × 1024 | Mid-width breakpoints and long translated copy |
| Desktop | 1440 × 900 | Wide editorial composition and rail/card geometry |

For each candidate screenshot, CI also captures the same public `main` route and produces a pixel-diff image when both screenshots are comparable.

### Release-blocking visual invariants

The initial hard gate blocks a release when it finds:

- horizontal page overflow greater than 2 px;
- key headings, table cells or controls clipped by their own box;
- watched key elements rendered outside the horizontal viewport;
- visible primary button targets smaller than 44×44 px;
- a candidate route that cannot be rendered successfully.

### Advisory pixel diff

Pixel-diff percentage is **advisory in v0.3**, not a hard release gate. Editorial changes legitimately alter text, line breaks and page height, so a raw screenshot mismatch is not automatically a defect. The candidate, baseline and diff PNGs are retained as evidence for human review.

A later version may add region-aware or component-aware thresholds after enough real regressions exist to calibrate them without generating noisy false positives.

## Initial Lighthouse budgets

| Profile | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mobile | ≥ 80 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 3500 ms | ≤ 300 ms | ≤ 0.10 |
| Desktop | ≥ 90 | ≥ 95 | ≥ 95 | ≥ 95 | ≤ 2500 ms | ≤ 200 ms | ≤ 0.10 |

These are release budgets, not claims about search ranking or field Core Web Vitals. Budgets should be tightened only after stable baselines exist across multiple runs.

## Evidence artifacts

Each pull-request Site Health stack can produce:

- raw Lighthouse JSON reports;
- human-readable Lighthouse HTML reports;
- `lighthouse-summary.json` / `.md`;
- `ui-geometry-summary.json` / `.md`;
- `ui-markup-summary.json` / `.md`;
- candidate screenshot PNGs;
- public-main baseline PNGs;
- visual diff PNGs;
- `visual-summary.json` / `.md`;
- GitHub Actions job summaries;
- compact PR comments for Lighthouse/geometry and visual regression.

The live audit adds `ui-geometry-live-summary.json` / `.md` against the deployed GitHub Pages site.

Artifacts are retained for 90 days in the initial implementation.

## Integrity boundary

A Lighthouse score, geometry check or screenshot diff is controlled evidence for a particular browser profile and run. It does **not** prove:

- Google ranking;
- production field Core Web Vitals;
- identical rendering for every reader/device/network;
- conversion or business impact;
- editorial correctness;
- visual taste or brand quality.

Those require separate evidence.

## Next useful site-quality layers

Prioritized after Lighthouse + geometry + visual regression are stable:

1. **Translation parity contract** — detect when EN/RU/zh-CN siblings drift, become stale or lose structural sections.
2. **Corrections + version history** — expose how articles change and why.
3. **RSS / newsletter feed** — make the journal subscribable outside social platforms.
4. **Privacy-aware analytics** — measure reading and CTA funnels without building invasive identity profiles.
5. **External citation-link health** — periodically detect broken or redirected evidence links without blocking every publication on transient third-party failures.
6. **Field performance evidence** — add privacy-safe real-user Web Vitals only if there is enough traffic to interpret them responsibly.
7. **Public health history** — trend Lighthouse, geometry, visual and publication-contract results across releases rather than presenting only the latest run.

The order matters: deterministic publication integrity and visible UI regressions are more important to an evidence-first journal than maximizing a vanity score.
