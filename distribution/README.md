# RESONANCE Distribution Engine

Every article should ship with a distribution package, not just a URL.

## Publishing flow

```text
ARTICLE
→ EN / RU / ZH
→ metadata + hreflang
→ platform-specific social copy
→ publish
→ distribute
→ collect meaningful replies
→ Demand Log
```

## Optimization target

Primary:

- meaningful replies;
- real workflows;
- qualified problems;
- product signals;
- pilot requests.

Secondary:

- impressions;
- clicks;
- likes;
- reposts;
- follower growth.

## Channels

### Global

- X
- LinkedIn
- Reddit
- Telegram
- Hacker News when editorially appropriate

### Russian

- Telegram
- VK
- Habr when editorially appropriate

### Chinese

- Weibo
- WeChat-compatible copy
- Zhihu

WeChat and Zhihu do not rely on a universal browser share endpoint in this implementation. RESONANCE therefore provides copy-ready localized text/link payloads instead of pretending direct automated posting exists.

## Per-article package

Each article should provide:

- canonical URL;
- localized URLs;
- article title/description;
- Hot Question;
- short and long social copy;
- network-specific copy where useful;
- share/copy UI on the article page;
- a route back to the market-intake form.

`article-004.social.json` is the first concrete package.
