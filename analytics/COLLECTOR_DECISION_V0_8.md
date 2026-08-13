# RESONANCE Collector Selection v0.8

Status: **selected, not activated**  
Date: 2026-08-12

## Decision

Use a minimal first-party collector implemented as a **Cloudflare Worker writing only allowlisted event dimensions to Workers Analytics Engine**.

Do not activate Plausible or Umami for the RESONANCE Market OS measurement spine.

Production transport remains disabled until the Worker is deployed, its public endpoint passes the live collector smoke contract, and `RESONANCE_ANALYTICS_ENDPOINT` is deliberately configured for the publication build.

## Why this decision exists

RESONANCE is not trying to reconstruct people, sessions, journeys, attribution identities or demographic profiles. The measurement question is narrower:

```text
article
  → meaningful_read
  → hot_question_view
  → workflow_intake_open
  → explicit Market OS evidence
```

The browser contract already limits emission to five fields:

- `schema_version`
- `event`
- `path`
- `language`
- `content_kind`

The collector should not widen that boundary.

## Options reviewed

### Plausible Cloud

Strengths:

- mature hosted analytics product;
- no cookies or persistent browser identifiers;
- EU-hosted visitor data;
- custom events and APIs.

Mismatch for RESONANCE v0.8:

- Plausible's unique-visitor model intentionally uses the request IP address and User-Agent to derive a rotating daily identifier;
- its Events API treats User-Agent as required for normal unique-visitor behavior and uses the sender/client IP when `X-Forwarded-For` is absent;
- the product is optimized for web-analytics concepts we deliberately do not need for the Market OS evidence boundary.

Verdict: **good general web analytics, broader identity processing than this measurement spine needs.**

### Umami Cloud / self-hosted

Strengths:

- open source;
- hosted free tier is available;
- no cookies and no cross-site tracking;
- flexible custom events and API access.

Mismatch for RESONANCE v0.8:

- `/api/send` requires a valid User-Agent;
- the data model is session-oriented and exposes session IDs plus browser / OS / device / country / city dimensions;
- location metrics are derived from the sender IP even though the IP is not stored;
- this creates a wider behavioral model than the five-field contract requires.

Verdict: **flexible and inexpensive, but still more session/visitor semantics than RESONANCE needs.**

### Minimal Cloudflare Worker + Workers Analytics Engine

Strengths:

- the Worker can enforce the exact five-field payload and reject every extra field;
- no user ID, session ID, cookie, fingerprint, referrer, User-Agent, IP-derived location or client timestamp is written by RESONANCE;
- Workers Analytics Engine is designed for event/time-series analytics and provides server-side receipt time without adding a client timestamp;
- Analytics Engine retention is currently three months, which provides a natural minimization boundary;
- current Free-plan limits are far above expected RESONANCE traffic.

Important boundary:

Cloudflare, as the network/compute provider, necessarily processes connection metadata such as the request IP at its edge. RESONANCE does **not** claim that transport IP ceases to exist at the provider boundary. The Worker code must not read, hash, copy, persist or export `CF-Connecting-IP`, `X-Forwarded-For`, `User-Agent`, referrer or geolocation fields.

Verdict: **selected. It matches the RESONANCE data-minimization model instead of adapting a general analytics product to it.**

## Collector invariants

The production Worker must:

1. accept only `POST` plus a narrow `OPTIONS` CORS preflight;
2. accept only the GitHub Pages origin `https://safal207.github.io`;
3. accept only JSON bodies up to 2 KiB;
4. require exactly the five v0.7 payload fields and reject unknown fields;
5. enforce the four allowlisted event names;
6. enforce language and content-kind allowlists;
7. reject paths outside `/RESONANCE/` or paths containing query/fragment data;
8. never inspect or persist IP, User-Agent, referrer, cookies or device/location headers;
9. write one Analytics Engine data point per accepted event;
10. return no visitor/session identifier;
11. keep Worker observability logging disabled in repository configuration;
12. remain independent from Market OS demand evidence: aggregate event counts are interest signals only.

## Stored data shape

Analytics Engine receives one data point with these dimensions only:

```text
blob1 = event
blob2 = path
blob3 = language
blob4 = content_kind
blob5 = schema_version

double1 = 1
```

The platform's event timestamp is receipt time. No exact client timestamp is sent.

## Cost / capacity boundary

As reviewed on 2026-08-12:

- Workers Free: up to 100,000 requests/day;
- Workers Paid: minimum $5/month, including 10M requests/month before request overage;
- Workers Analytics Engine Free: 100,000 data points/day and 10,000 read queries/day;
- Analytics Engine documentation states billing is not yet active, while publishing future pricing in advance.

These figures are external and can change. They are capacity context, not a permanent protocol guarantee.

## Activation gate

Do **not** set `RESONANCE_ANALYTICS_ENDPOINT` merely because this code exists.

Activation requires all of the following:

- collector unit/adversarial tests PASS;
- Wrangler dry-run PASS against the pinned CLI version;
- Worker deployed to the intended Cloudflare account;
- deployed endpoint returns correct CORS and strict-schema behavior;
- a synthetic event is observed in the Analytics Engine dataset without extra dimensions;
- live site audit confirms the intended endpoint and enabled mode;
- measurement page is updated from `selected / disabled` to `active` only after the live checks pass.

## Evidence boundary

Passing v0.8 proves the selected collector architecture, source-level minimization rules and deployable Worker contract. It does not prove Cloudflare account configuration, provider-side legal compliance for a particular jurisdiction, event delivery completeness, human readership, demand, product-market fit or revenue.
