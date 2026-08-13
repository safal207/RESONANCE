# RESONANCE Privacy-Aware Analytics

RESONANCE measures the article-to-dialogue path without creating a cross-session reader identity.

- **v0.7** defined the five-field browser measurement contract.
- **v0.8** selected and activated a minimal Cloudflare Worker + Workers Analytics Engine collector.
- **v0.9** turns that already-verified stream into deterministic aggregate Market Signal readouts without adding identity semantics or treating attention as demand.

See [`COLLECTOR_DECISION_V0_8.md`](./COLLECTOR_DECISION_V0_8.md) for the collector decision and [`MARKET_SIGNAL_READOUT_V0_9.md`](./MARKET_SIGNAL_READOUT_V0_9.md) for the readout contract.

## Measurement spine

```text
article
  ↓
meaningful_read
  ↓
hot_question_view
  ↓
workflow_intake_open / verified_workflow_open
  ↓
explicit workflow submission
  ↓
Problem Card / Product Signal / pilot evidence
```

The browser events are attention/action signals. A real workflow submission and every downstream Market OS claim remain explicit evidence, not inferred conversions.

## Event definitions

- `meaningful_read`: article remained visible for at least 45 seconds and reached at least 60% scroll depth in the same page load.
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

No client timestamp is sent. Analytics Engine receipt time is authoritative for aggregation.

## Privacy invariants

The browser implementation must not use cookies, localStorage, sessionStorage, IndexedDB, persistent anonymous IDs, fingerprint surfaces, referrer, user-agent, screen dimensions, device characteristics, email/name fields, or free-text form contents.

`navigator.globalPrivacyControl === true` or Do Not Track disables emission. Automated browsers used by Site Health are suppressed. Requests use `credentials: omit` and `referrerPolicy: no-referrer`.

## Collector v0.8 — active and verified

The production collector is a minimal Cloudflare Worker that accepts the five fields above and rejects every unknown field. It writes:

```text
blob1   event
blob2   path
blob3   language
blob4   content_kind
blob5   schema_version
double1 1
```

The Worker source does not read, hash, persist or export IP address, IP-derived geography, User-Agent, referrer, cookies, device/browser characteristics, visitor IDs, session IDs or distinct IDs.

Cloudflare necessarily processes connection metadata as infrastructure provider. The RESONANCE boundary is narrower: our collector code does not inspect or write those values into the measurement dataset.

Production activation is complete: the Worker passed live CORS/schema gates, a synthetic write was read back from Workers Analytics Engine, `RESONANCE_ANALYTICS_ENDPOINT` was configured for Pages, and the public live analytics audit passed in enabled mode.

Transport still remains fail-closed by design: a build without an explicit valid HTTPS `RESONANCE_ANALYTICS_ENDPOINT` exposes no collector endpoint.

## Market Signal Readout v0.9

v0.9 does not change the browser payload. It queries the existing dataset for an explicit closed UTC interval and produces deterministic JSON + Markdown evidence.

Key rules:

- counts use `SUM(_sample_interval * double1)` so Analytics Engine sampling is accounted for;
- evidence windows are explicit `[start, end)` UTC intervals, never a rolling `NOW()-24h` artifact;
- collector activation smoke paths remain in the source dataset but are explicitly classified and excluded from market totals;
- output is grouped only by existing event/path/language/content-kind/schema dimensions;
- aggregate signal ratios are not called user conversion rates because no visitor/session identity exists;
- attention/action analytics never become qualified demand without explicit downstream workflow evidence.

## Evidence boundary

Analytics can establish aggregate attention/action signals for the configured measurement contract. It cannot establish unique readers, sessions, comprehension, causal conversion, qualified demand, product-market fit, revenue or complete delivery.

Demand begins only when explicit workflow evidence enters the Market OS path:

```text
workflow submission
  → diagnostic dialogue
  → Problem Card
  → Product Signal
  → client-specific pilot
  → evidence
```
