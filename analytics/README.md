# RESONANCE Privacy-Aware Analytics v0.7

RESONANCE measures the article-to-dialogue path without creating a cross-session reader identity.

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

## Allowed payload

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

No client timestamp is sent. The collector may timestamp receipt, but its retention and aggregation behavior must be governed separately.

## Privacy invariants

The browser implementation must not use cookies, localStorage, sessionStorage, IndexedDB, persistent anonymous IDs, fingerprint surfaces, referrer, user-agent, screen dimensions, device characteristics, email/name fields, or free-text form contents.

`navigator.globalPrivacyControl === true` or Do Not Track disables emission even when a collector endpoint is configured.

Requests use `credentials: omit` and `referrerPolicy: no-referrer`.

## Default-off transport

Production analytics is **disabled unless `RESONANCE_ANALYTICS_ENDPOINT` is explicitly configured during the publication build**. A collector endpoint is not a hidden secret: browser clients must know where they send events. Provider credentials, if a collector needs them, must stay server-side and must never be embedded in the journal.

Collector activation requires a separate decision covering at minimum:

1. no cross-site profiling or advertising use;
2. no cookies or persistent reader IDs;
3. IP handling/truncation or deletion policy;
4. retention window and aggregation policy;
5. CORS and HTTPS transport;
6. data-processing jurisdiction/provider terms;
7. ability to delete or stop collection without changing article content.

## Evidence boundary

Web analytics can tell us whether readers reached and acted on a market question. It cannot prove the question exposed a real workflow, a real failure, willingness to test, product-market fit, or revenue. Those claims remain downstream Market OS evidence.
