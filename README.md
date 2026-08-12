# RESONANCE

**Journal of Intelligence, Technology & Human Progress**

> Intelligence is changing the world. RESONANCE exists to understand what is changing, why it matters, what the evidence says, and what people should do next.

RESONANCE is an independent, evidence-first global journal covering AI, science, technology, entrepreneurship, trust, and human progress.

We are not building a news feed. We are building a **verification-aware publication** for readers who want signal, causality, evidence, uncertainty, implications, action — and a reproducible path from claim to proof.

## Editorial model

Every serious RESONANCE story should move through a common reasoning chain:

**Signal → Cause → Evidence → Causality → Uncertainty → Verification → Implications → Action**

This means we separate:

- what happened from what is merely claimed;
- primary evidence from commentary;
- correlation from causality;
- known facts from uncertainty;
- short-term noise from structural change;
- interesting information from actionable consequences.

## Market OS

RESONANCE also treats selected articles as structured market-learning experiments:

```text
PUBLISH
  ↓
TEACH
  ↓
ASK
  ↓
LISTEN
  ↓
DIAGNOSE
  ↓
GIVE VALUE
  ↓
SPECIFY
  ↓
PILOT
  ↓
PROVE
  ↓
PRODUCTIZE
  ↓
PUBLISH AGAIN
```

The goal is not to build products first and then search for demand. A strong article should create a useful conversation in which a real workflow, failure, business impact, missing capability and acceptance condition can become visible.

The North Star is **Verified Product Requests**, not page views.

Market infrastructure:

- [`market/README.md`](market/README.md) — Demand Log and evidence rules;
- [`market/problem-card.schema.json`](market/problem-card.schema.json) — structured Problem Card;
- [`market/market-os.mjs`](market/market-os.mjs) — deterministic Product Signal scoring and clustering;
- [`market/demand-graph.json`](market/demand-graph.json) — public demand-graph state;
- [`protocols/MARKET_DIALOGUE_PROTOCOL.md`](protocols/MARKET_DIALOGUE_PROTOCOL.md) — value-first conversation protocol;
- [`protocols/VERIFIED_WORKFLOW_PILOT.md`](protocols/VERIFIED_WORKFLOW_PILOT.md) — one-workflow pilot;
- [`protocols/ARTICLE_005_SELECTION_RULE.md`](protocols/ARTICLE_005_SELECTION_RULE.md) — evidence gate for the next market-driven article;
- [`protocols/PRODUCTIZATION_PROTOCOL.md`](protocols/PRODUCTIZATION_PROTOCOL.md) — custom → pattern → service → software heuristic;
- [`distribution/`](distribution/) — multilingual social/distribution packs.

Synthetic examples are permitted only for testing the data model and **must never count as market evidence**. The Demand Graph starts at zero real signals.

## Languages

The publication now has first-class entry points for:

- **English** — `site/index.html`;
- **Русский** — `site/index.ru.html`;
- **简体中文** — `site/index.zh.html`.

Article #004 is published in all three languages with `hreflang`, localized structured data, localized Open Graph locale metadata, share tools and a common market-intake path.

## Research protocol

### Transactional Trust Protocol v1.0

RESONANCE now maintains an experimental framework-agnostic protocol for consequential agent actions:

```text
OBSERVE
  ↓
VERIFY
  ↓
AUTHORIZE
  ↓
BIND
  ↓
COMPARE
  ↓
COMMIT
  ↓
RECONCILE
  ↓
PROVE
```

Canonical specification:

[`protocols/transactional-trust-v1.0/README.md`](protocols/transactional-trust-v1.0/README.md)

TTP v1.0 synthesizes the reproducible invariants developed across Verified Reports #003–#010: ambiguous recovery, uncertainty preservation, evidence conflict, authority verification, authority lifecycle, stale trust state, execution-time TOCTOU and atomic state-version transitions.

Verified Report #011 composes those hazards in one deterministic end-to-end benchmark. The unsafe path produced three synthetic committed effects; the TTP path preserved one effect while exercising all eight stages.

## Coverage

RESONANCE focuses on five connected domains:

- **AI** — models, agents, infrastructure, robotics, intelligence systems;
- **Science** — research, discovery, reproducibility, scientific tooling;
- **Startups & Economy** — companies, markets, new business models, capital;
- **Trust & Verification** — safety, security, provenance, evidence, governance;
- **Human** — cognition, flow, learning, creativity, health, meaning and adaptation.

## Science Desk

RESONANCE Science is the evidence-first desk for biology, AI for Science, computational research, reproducibility and scientific decision-making.

Its working chain is:

**Observation → Evidence State → Interpretation → Causal Boundary → Translation Gap → Decision Readiness → Next Discriminating Evidence**

The desk complements live **Science Signals** such as X(2370): a signal verifies a concrete claim; the desk provides the reusable method for asking where evidence stops, what remains unresolved and what additional observation would change confidence.

Science infrastructure:

- [`science/README.md`](science/README.md) — Science Desk manifesto and editorial contract;
- [`reports/science/001-discovery-to-decision.md`](reports/science/001-discovery-to-decision.md) — founding translation-readiness report;
- `site/science.html` — English Science Desk;
- `site/science.ru.html` — Russian Science Desk;
- `site/science.zh.html` — Simplified Chinese Science Desk.

The research-only boundary excludes wet-lab instructions, guide/construct design, clinical advice, biological safety approval and experiment authorization.

## Founding Edition

### Issue 001 — THE AGE OF AGENTS

**How AI is moving from answering questions to acting in the world.**

The first issue explores the transition from passive models to systems that plan, act, use tools, transact, coordinate, recover from failure, and interact with real infrastructure.

The research chain currently connects:

```text
analysis
→ trust framework
→ failure taxonomy
→ benchmark
→ external framework baseline
→ containment
→ recovery
→ uncertainty preservation
→ evidence conflict
→ authority verification
→ authority lifecycle
→ trust-state freshness
→ execution binding
→ atomic transition
→ Transactional Trust Protocol v1.0
→ end-to-end adversarial verification
→ PostgreSQL transactional boundaries
→ causal hardware replay-state recovery
```

See [`issues/001-age-of-agents/`](issues/001-age-of-agents/) and the web edition at [`site/issue-001.html`](site/issue-001.html).

## Verified research

Key reproducible reports:

- **#001** OpenAI Agents SDK structural baseline — 95/100;
- **#002** Docker containment — 8/10;
- **#003–#010** recovery, evidence, authority, time and atomic-transition protocols — 10/10 each in their defined synthetic scopes;
- **#011** Transactional Trust Protocol v1.0 End-to-End — 10/10, unsafe compounded path 3 effects vs TTP-safe path 1 effect;
- **#012–#014** PostgreSQL transactional trust, isolation and external-effect boundaries — reproducible scoped results;
- **#015** CaPU v0.10 replay-state recovery across reset — bounded formal PASS with fail-closed restore semantics.

All scores are scope-specific protocol/benchmark scores. They are **not percentages of safety** and are not external certifications.

Machine-readable evidence and reports live under [`reports/verified/`](reports/verified/).

## Website

`site/` contains the static publication, including:

- `site/index.html` — English magazine homepage;
- `site/index.ru.html` — Russian homepage;
- `site/index.zh.html` — Simplified Chinese homepage;
- `site/science.html`, `site/science.ru.html`, `site/science.zh.html` — localized Science Desk editions;
- `site/before-you-let-an-ai-agent-move-money*.html` — Article #004 in EN/RU/ZH;
- `site/open-problems.html` — public Demand Graph / Open Problems view;
- `site/verified-workflow.html` — service-first verification pilot;
- `site/issue-001.html` — Issue 001 web edition;
- `site/transactional-trust-protocol-v1.html` — TTP v1.0 publication;
- `site/styles.css`, `site/article.css`, `site/market.css` — editorial/market UI;
- `site/app.js`, `site/market.js` — responsive navigation and share helpers;
- `.github/workflows/pages.yml` — GitHub Pages deployment workflow;
- `.github/workflows/seo.yml` — publication contract: Market OS tests + SEO validation.

## Repository structure

```text
RESONANCE/
├── README.md
├── MANIFESTO.md
├── EDITORIAL_PRINCIPLES.md
├── CONTRIBUTING.md
├── content/
├── distribution/
├── market/
├── science/
├── protocols/
│   └── transactional-trust-v1.0/
├── benchmarks/
├── reports/
│   ├── science/
│   └── verified/
├── issues/
│   └── 001-age-of-agents/
├── topics/
├── site/
└── .github/
    ├── ISSUE_TEMPLATE/
    └── workflows/
```

## Publishing philosophy

RESONANCE aims to be:

**Global. Independent. Evidence-first. Curious. Constructive. Human.**

We prefer a precise uncertainty over a confident fiction.

We prefer original evidence over recycled opinion.

We prefer useful synthesis over information volume.

We believe the future deserves journalism and research artifacts that can be inspected, challenged, reproduced, and improved.

## Status

**Founding research edition — active.**

Issue 001 is now both an editorial issue and an executable research program: claims become hypotheses, hypotheses become deterministic tests, tests become evidence bundles, repeated invariants are consolidated into protocols, and selected articles can now feed a separate evidence-bounded market discovery loop.

---

**RESONANCE** — *Find the signal. Verify the path. Understand the future.*
