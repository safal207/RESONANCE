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
TRANSLATION PARITY CONTRACT
  ├─ managed EN / RU / zh-CN sibling existence
  ├─ reciprocal canonical / hreflang / language-switcher mapping
  ├─ article semantic-outline parity
  ├─ CTA + critical ID + runtime-script parity
  └─ primary / evidence source-link parity
  ↓
CORRECTIONS + VERSION HISTORY CONTRACT
  ├─ public machine-readable corrections ledger
  ├─ unbroken version chains per managed route
  ├─ append-only immutable historical entries
  ├─ published-page change → new version-history event
  └─ reason + claim impact + evidence linkage
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
- Site Health / Quality;
- Corrections / Version History.

Desktop Lighthouse profiling is intentionally narrower (homepage + primary Article #004) to keep CI useful and fast.

The Visual Regression Contract uses a broader multilingual matrix:

- homepage;
- Article #004 EN / RU / zh-CN;
- Article #005 EN / RU / zh-CN;
- Site Health / Quality;
- Corrections / Version History;
- each at 390×844, 768×1024 and 1440×900.

That produces 27 candidate screenshots per run plus matching public-main baselines and diff PNGs when a baseline route exists. A newly introduced route may legitimately have no public-main baseline on its first release; candidate geometry remains release-blocking while the missing baseline is reported rather than invented.

The post-deployment Live Experience Audit measures a smaller public subset again to detect deploy/runtime differences, including the public Corrections history once v0.5 is deployed.

## Translation Parity Contract

Translation Parity v0.4 treats localization drift as a release property rather than a copy-editing afterthought.

The initial **managed translation triplets** are:

- homepage — `index.html` / `index.ru.html` / `index.zh.html`;
- Article #004 — EN / RU / zh-CN;
- Article #005 — EN / RU / zh-CN.

The list is intentionally explicit. RESONANCE can contain a Russian-only or English-only publication without pretending that an unannounced translation is missing. A triplet becomes release-managed only when all three locales are deliberately part of the publication contract.

### Release-blocking translation-parity invariants

For every managed triplet, CI requires:

- all three siblings to exist;
- the expected `html lang` on each sibling;
- correct canonical URLs and reciprocal `hreflang` mappings;
- a visible EN / RU / zh-CN language switcher with only the active locale marked `aria-current="page"`.

For managed article triplets, CI additionally requires:

- the same Issue / Article identity;
- the same major semantic outline: H2/H3 levels plus trajectory, invariant/evidence, market-question, distribution and source blocks in the same order;
- the same critical IDs;
- the same market CTA destinations;
- the same primary/evidence source URLs;
- the same runtime script set.

This is **semantic-structure parity**, not sentence-by-sentence translation comparison. Natural translations may use different wording, sentence counts and paragraph lengths.

### Evidence boundary

A passing Translation Parity Contract proves that the managed localized publication siblings still expose the same structural/evidence surface and action destinations. It does **not** prove linguistic fluency, nuanced semantic equivalence, cultural appropriateness or factual correctness of translated prose. Those require editorial/human or separate language-model review evidence.

## Corrections + Version History Contract

Corrections + Version History v0.5 treats the published state of an article as a time-dependent claim surface rather than timeless text.

The public ledger lives at `site/corrections.json`, with a human-readable view at `/corrections.html`. The initial version-managed publication set is deliberately narrow:

- Article #004 EN / RU / zh-CN;
- Article #005 EN / RU / zh-CN.

Each history entry records:

- a stable event ID and effective date;
- change type: publication, correction, clarification, evidence update, translation repair or structural change;
- whether the change leaves the claim untouched, changes presentation, clarifies it or changes the claim itself;
- affected publication, locale and route;
- version before and version after;
- a plain-language summary and reason;
- inspectable evidence URLs.

### Release-blocking corrections/version invariants

Once v0.5 exists on the base branch, CI requires:

- every registered route to exist and end at the version declared by the registry;
- each route's history to form an unbroken chain from initial publication to current version;
- existing history entries to remain byte-for-byte append-only: they cannot be deleted, reordered or rewritten;
- registered route mappings to remain stable rather than silently moving historical identity to another path;
- a modified managed published page to be covered by a newly appended version-history entry in the same change;
- every entry to carry reason, claim-impact classification and evidence;
- every non-initial-publication event to include RESONANCE GitHub evidence.

The first v0.5 release bootstraps the ledger from known history. Append-only diff enforcement activates automatically on subsequent changes because the base branch will then contain the ledger. PR runs compare against the pull-request base SHA; direct pushes to `main` compare against the push event's previous SHA so the same silent-edit boundary cannot be bypassed by skipping a PR.

The first recorded repair is the Article #005 localization drift found by Translation Parity v0.4: the RU and zh-CN siblings were restored from 17 semantic tokens / 3 source links to the English publication's 23 semantic tokens / 4 source links. That repair changes the localized publication package, not the underlying English claim, so its claim impact is recorded as `presentation`.

### Evidence boundary

A passing Corrections + Version History Contract proves version bookkeeping, append-only historical integrity and evidence linkage for the routes explicitly registered in the ledger. It does **not** prove that a correction is factually sufficient, that an editor chose the perfect wording, or that an unregistered page has complete version history. Those are separate editorial/evidence questions.

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
- `translation-parity-summary.json` / `.md`;
- `corrections-history-summary.json` / `.md`;
- candidate screenshot PNGs;
- public-main baseline PNGs;
- visual diff PNGs;
- `visual-summary.json` / `.md`;
- GitHub Actions job summaries;
- compact PR comments for Lighthouse/geometry, translation parity, corrections/version history and visual regression.

The live audit adds `ui-geometry-live-summary.json` / `.md` against the deployed GitHub Pages site.

Artifacts are retained for 90 days in the initial implementation.

## Integrity boundary

A Lighthouse score, geometry check, translation-parity result, corrections-history result or screenshot diff is controlled evidence for a particular profile and run. It does **not** prove:

- Google ranking;
- production field Core Web Vitals;
- identical rendering for every reader/device/network;
- conversion or business impact;
- editorial correctness;
- nuanced linguistic translation quality;
- factual sufficiency of a correction;
- visual taste or brand quality.

Those require separate evidence.

## Next useful site-quality layers

Prioritized after publication, translation parity, corrections/version history, Lighthouse, geometry and visual regression are stable:

1. **RSS / newsletter feed** — make the journal subscribable outside social platforms.
2. **Privacy-aware analytics** — measure reading and CTA funnels without building invasive identity profiles.
3. **External citation-link health** — periodically detect broken or redirected evidence links without blocking every publication on transient third-party failures.
4. **Field performance evidence** — add privacy-safe real-user Web Vitals only if there is enough traffic to interpret them responsibly.
5. **Public health history** — trend Lighthouse, translation parity, corrections/version history, geometry, visual and publication-contract results across releases rather than presenting only the latest run.

The order matters: deterministic publication integrity, localization drift, historical accountability and visible UI regressions are more important to an evidence-first journal than maximizing a vanity score.
