# RESONANCE minimal analytics collector

This directory contains the **selected but not yet activated** v0.8 collector for the RESONANCE privacy-aware measurement spine.

Architecture:

```text
GitHub Pages analytics.js
  ↓ HTTPS POST / CORS
Cloudflare Worker
  ↓ strict five-field validation
Workers Analytics Engine
  ↓ aggregate SQL only
Site Health / Market OS measurement
```

The collector is intentionally not a general visitor analytics system.

## Accepted browser payload

Exactly these fields are accepted:

```json
{
  "schema_version": 1,
  "event": "meaningful_read",
  "path": "/RESONANCE/before-you-let-an-ai-agent-move-money.html",
  "language": "en",
  "content_kind": "article"
}
```

Unknown fields are rejected rather than ignored.

## Stored Analytics Engine mapping

```text
blob1   event
blob2   path
blob3   language
blob4   content_kind
blob5   schema_version
double1 1
```

Workers Analytics Engine adds receipt `timestamp` at the platform layer. RESONANCE does not send a client timestamp.

No RESONANCE code reads or stores IP, User-Agent, referrer, cookies, device/location metadata, visitor IDs or session IDs.

## Local / CI validation

```bash
node --test collector/tests/*.test.mjs
node scripts/verify-collector.mjs
npx --yes wrangler@4.115.0 deploy --dry-run --config collector/wrangler.jsonc --outdir collector-dist
```

CI pins Wrangler `4.115.0` so deployment syntax does not drift underneath the contract.

## Deployment — intentionally manual until the gate is satisfied

Deployment requires Cloudflare authentication and is deliberately not run by the repository workflow yet.

After authenticating Wrangler to the intended account:

```bash
npx --yes wrangler@4.115.0 deploy --config collector/wrangler.jsonc
```

The first write creates the Analytics Engine dataset named `resonance_market_events_v1`.

Do not set the journal's `RESONANCE_ANALYTICS_ENDPOINT` repository variable until the deployed Worker passes the live smoke checks below.

## Required post-deploy smoke checks

1. `OPTIONS` from `https://safal207.github.io` receives the narrow POST CORS contract.
2. `POST` from any other Origin is rejected.
3. a valid five-field synthetic event returns `204`.
4. the same event plus `email`, `user_agent`, `referrer`, `client_timestamp` or any other sixth field is rejected.
5. a path outside `/RESONANCE/` is rejected.
6. Analytics Engine contains exactly the five mapped blobs plus count value.
7. no visitor/session identifier is returned to the caller.
8. only after those checks pass, configure `RESONANCE_ANALYTICS_ENDPOINT=https://<deployed-worker-host>/` and let the existing publication/live analytics contracts verify enabled mode.

## Example aggregate query

Use the Cloudflare Analytics Engine SQL API with an API token kept outside the public site:

```sql
SELECT
  blob1 AS event,
  blob2 AS path,
  blob3 AS language,
  blob4 AS content_kind,
  SUM(_sample_interval * double1) AS event_count
FROM resonance_market_events_v1
WHERE timestamp > NOW() - INTERVAL '1' DAY
GROUP BY event, path, language, content_kind
ORDER BY event_count DESC
```

This query produces aggregate event counts. It does not reconstruct a reader or a session.

## Retention and cost boundary

At the v0.8 decision date, Workers Analytics Engine documents three-month retention. Cloudflare's current Free limits are sufficient for early RESONANCE traffic, but pricing and limits are external facts and must be re-checked before any scale decision.

## Evidence boundary

A deployed collector can prove that aggregate browser events reached the configured dataset. It still cannot prove comprehension, a real workflow, willingness to test, product-market fit or revenue. Those claims stay downstream in explicit Market OS evidence.
