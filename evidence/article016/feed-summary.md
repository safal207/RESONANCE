# RESONANCE RSS / Subscribe Contract

**Verdict:** PASS
**Mode:** local

| Language | Feed | Items | Newest item | Verdict |
|---|---|---:|---|---|
| en | feed.xml | 30 | Sun, 06 Sep 2026 12:00:00 GMT | PASS |
| ru | feed.ru.xml | 7 | Sun, 06 Sep 2026 12:00:00 GMT | PASS |
| zh-CN | feed.zh.xml | 4 | Sun, 06 Sep 2026 12:00:00 GMT | PASS |

## Invariants

- RSS 2.0 + Atom self-link identity is stable for EN / RU / zh-CN feeds.
- Items are derived from published HTML with explicit publication dates, sorted newest-first and capped at 50.
- `lastBuildDate` equals the newest item date, so identical publication state produces identical feed bytes.
- Utility pages are excluded; item language must match its locale route.
- Local builds require one language-appropriate RSS autodiscovery link on every HTML page.
- Live mode re-fetches public feeds, the Subscribe page and representative recent item URLs.

## Evidence boundary

Passing proves feed structure, deterministic ordering/identity, local route linkage and live reachability for the checked surfaces. It does not prove subscriber delivery by a particular RSS reader, email delivery, readership or engagement.
