# RESONANCE Article Template

Use this template for evidence-first features, investigations, explainers, research notes, and market-learning articles.

---

# [Title]

**Article ID:** [###]

**Deck:** One sentence explaining why this matters.

**By:** [Author]

**Status:** Draft / Fact-check / Verified / Published

**Last verified:** YYYY-MM-DD

**Languages:** EN / RU / zh-CN / [other]

**Canonical identity:** [shared article ID / slug]

## Signal

What happened, changed, or became newly visible?

Keep this section factual and concise.

## Why it matters

What could this change for technology, science, markets, institutions, or people?

## Claims

List the material claims the article depends on.

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 |  | Verified fact / inference / disputed / preliminary / prediction / opinion / unknown | High / Medium / Low |  |

## Evidence

### Primary sources

- [Source]

### Secondary sources

- [Source]

### Data / code / artifacts

- [Artifact]

## Causal model

Describe the proposed mechanism rather than merely the sequence of events.

```text
condition → actor/incentive → action → state transition → observed result
```

### Alternative explanations

- Alternative A
- Alternative B

## Timeline

| Date | Event | Evidence |
|---|---|---|
|  |  |  |

## Uncertainty

What is not known?

What evidence would change the conclusion?

What assumptions are being made?

## Verification

Document the checks performed before publication.

- [ ] Material claims traced to sources
- [ ] Dates checked
- [ ] Quotes checked against originals
- [ ] Numbers/calculations reproduced where relevant
- [ ] Causal language reviewed
- [ ] Counter-evidence considered
- [ ] Conflicts of interest disclosed
- [ ] AI-assisted factual output checked against underlying evidence

## Implications

### First-order

What changes immediately?

### Second-order

What could change because of the first-order effects?

### Who wins / who loses

Which actors gain or lose capability, leverage, cost advantage, safety, or optionality?

## What to watch next

Identify observable signals that would confirm or weaken the thesis.

## Action

What can builders, researchers, operators, policymakers, investors, or readers reasonably do with this information?

---

# Optional Market Dialogue Layer

Use this section only when the article is intended to discover a real market problem. Do not force every editorial article into a sales funnel.

## Hot Question

The question must seek a concrete workflow, failure, constraint, missing guarantee, or acceptance condition — not generic opinion.

> **[What unresolved real-world condition should the reader describe?]**

### Workflow prompts

- **Actor / agent:** What does it do?
- **Failure:** What could go wrong?
- **Impact:** What happens if it fails?
- **Current workaround:** How is this handled today?
- **Trust condition:** What would have to be verified or proven before the workflow is acceptable?

### CTA

Prefer problem-first language such as:

**Describe your workflow →**

Avoid a hard sales CTA before the missing capability is explicit.

### Response contract

Every meaningful response should receive:

1. one useful insight;
2. one compact model / trajectory / invariant;
3. one diagnostic question.

Route reviewed responses into a Problem Card and Product Signal Score. Never count synthetic examples as market demand.

---

# Distribution Pack

Before publication, prepare one reusable social metadata file under `distribution/`.

Minimum fields:

- canonical URL;
- localized URLs;
- localized title / description;
- Hot Question when present;
- platform-specific social copy;
- share/copy behavior;
- target channel;
- intended response metric.

Suggested channels:

- **Global:** X, LinkedIn, Reddit, Telegram, Hacker News when appropriate;
- **RU:** Telegram, VK, Habr when appropriate;
- **zh-CN:** Weibo, WeChat-compatible copy, Zhihu.

Optimize primarily for meaningful replies, real workflows and qualified product signals — not only impressions.

# Localization Checklist

For translated/localized editions:

- [ ] Keep one shared article identity / semantic meaning
- [ ] Adapt terminology instead of mechanically translating it
- [ ] Add `hreflang` links for EN / RU / zh-CN and `x-default`
- [ ] Keep a self-canonical per localized URL
- [ ] Localize title / description / `og:locale` / structured-data `inLanguage`
- [ ] Preserve evidence links and uncertainty statements
- [ ] Localize the Hot Question and CTA
- [ ] Localize the social pack

## Corrections

Record material post-publication corrections here.

| Date | Correction | Reason |
|---|---|---|
|  |  |  |

---

**RESONANCE verification chain:**

**Signal → Claim → Source → Evidence → Cause → Timeline → Uncertainty → Verification → Implication → Action**

**RESONANCE market loop (when enabled):**

**Publish → Teach → Ask → Listen → Diagnose → Give Value → Specify → Pilot → Prove → Productize → Publish again**
