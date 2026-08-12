# RESONANCE Privacy-Aware Analytics v0.8

RESONANCE measures the article-to-dialogue path without creating a cross-session reader identity.

v0.8 keeps the browser contract from v0.7 and selects a collector architecture: **a minimal Cloudflare Worker writing only the five allowlisted dimensions to Workers Analytics Engine**. The collector is selected and deployable, but production transport remains disabled until the explicit activation gate passes.

See [`COLLECTOR_DECISION_V0_8.md`](./COLLECTOR_DECISION_V0_8.md) for the provider comparison and decision boundary.

## Measurement spine

```text
article
  ↓
meaningful_read
  ↓
hot_question_view
  ↓
workflow_intake_open
  ↓
GitHub market workflow submission
  ↓
Problem Card / Product Signal / pilot evidence
```

The first three transitions are browser-measurement signals. A real workflow submission and every downstream Market OS claim remain evidence-backed GitHub/Problem Card events, not inferred conversions.

## Event definitions

- `meaningful_read`: article remained visible for at least 45 seconds and the reader reached at least 60% scroll depth in the same page load.
- `hot_question_view`: the market hot-question block reached at least 60% viewport visibility.
- `workflow_intake_open`: a reader activated the GitHub market-workflow intake link.
- `verified_workflow_open`: a reader activated the Verified Workflow pilot link from a market-question surface.

Each event is emitted at most once per page load.

## Allowed browser payload

Only five fields may leave the page:

```json
{
  "schema_version": 1,
  "event": "meaningful_read",
  "path": "/RESONANCE/before-you-let-an-ai-agent-move-money.html",
  "language": "en",
  "content_kind": "article"
}
```

No client timestamp is sent. The selected collector uses Analytics Engine receipt time instead of widening the client payload.

## Privacy invariants

The browser implementation must not use cookies, localStorage, sessionStorage, IndexedDB, persistent anonymous IDs, fingerprint surfaces, referrer, user-agent, screen dimensions, device characteristics, email/name fields, or free-text form contents.

`navigator.globalPrivacyControl === true` or Do Not Track disables emission even when a collector endpoint is configured. Automated browsers used by Site Health are also suppressed.

Requests use `credentials: omit` and `referrerPolicy: no-referrer`.

## Collector selection v0.8

The selected Worker is intentionally smaller than a general analytics product. It accepts the same five fields and rejects every unknown field.

The Worker must not read, hash, persist or export:

- IP address or IP-derived geography;
- User-Agent;
- referrer;
- cookies;
- device/browser characteristics;
- visitor/session/distinct IDs.

Cloudflare still processes network connection metadata as the infrastructure provider. The RESONANCE boundary is narrower: our collector code does not inspect or write those values into the analytics dataset.

Analytics Engine mapping:

```text
blob1   event
blob2   path
blob3   language
blob4   content_kind
blob5   schema_version
double1 1
```

The repository config keeps Worker observability logging disabled, and the collector contract statically checks that prohibited identity/header tokens are absent from the Worker source.

## Default-off transport remains authoritative

Production analytics is **disabled unless `RESONANCE_ANALYTICS_ENDPOINT` is explicitly configured during the publication build**. A collector endpoint is not a hidden secret: browser clients must know where they send events. Provider credentials must stay server-side and must never be embedded in the journal.

v0.8 does not set this variable. Selection is not activation.

Activation requires:

1. collector adversarial tests pass;
2. collector source/privacy verifier passes;
3. pinned Wrangler dry-run passes;
4. Worker is deployed to the intended Cloudflare account;
5. live CORS and strict-schema smoke tests pass;
6. one synthetic event is confirmed in Analytics Engine with no extra dimensions;
7. only then is `RESONANCE_ANALYTICS_ENDPOINT` set;
8. the existing public live analytics audit confirms enabled mode.

## Why not Plausible / Umami for this spine

Both are credible privacy-oriented general analytics systems, but each carries semantics RESONANCE does not need. Plausible uses request IP + User-Agent for a rotating daily unique-visitor identifier. Umami exposes session-oriented analytics and uses the sender IP for location metrics while requiring a valid User-Agent for its send API. The v0.8 collector deliberately omits unique visitors, sessions and geography entirely.

## Evidence boundary

Web analytics can tell us whether readers reached and acted on a market question. It cannot prove the question exposed a real workflow, a real failure, willingness to test, product-market fit, or revenue. Those claims remain downstream Market OS evidence.

Passing the v0.8 collector contract proves repository source/configuration minimization and deployability. It does not prove production deployment, Cloudflare account settings, provider-side legal compliance for a particular jurisdiction, event delivery completeness or real-user behavior.
