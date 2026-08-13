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
→ checkpoint freshness / anti-rollback
→ checkpoint authority commit protocol
→ checkpoint content commitment
→ full causal checkpoint state binding
→ live causal execution resumption
→ causally bound architectural execution resumption
→ architectural checkpoint content binding
→ precise trap / privilege recovery
→ delegated + nested trap authority
→ MMU translation / precise page-fault recovery
→ TLB freshness / shootdown authority
→ multi-hart shootdown delivery / acknowledgement quorum
→ shootdown delivery provenance / bounded retry reliability
→ cross-generation message reordering / stale-message quarantine
→ generation-wrap / ABA protection
→ accelerator command / exactly-once DMA recovery authority
→ in-flight DMA completion uncertainty / evidence-gated recovery
→ durable negative completion evidence / UNKNOWN convergence
```

See [`issues/001-age-of-agents/`](issues/001-age-of-agents/) and the web edition at [`site/issue-001.html`](site/issue-001.html).

## Verified research

**Current verified milestone — 2026-08-13:** CaPU v0.28 closes the recovery-convergence gap left intentionally by v0.27. When exact evidence resolves an issued DMA effect as `NOT_COMMITTED`, the bounded model creates a durable negative-completion receipt and consumes the old issue witness. That receipt survives a later crash and dominates a stale checkpoint that still records `UNKNOWN`, reconstructing `NOT_COMMITTED` and allowing replay authority to reopen when no new recovery/restore barrier is active. A new retry consumes the old negative receipt and creates a fresh issue witness, so evidence from a previous non-committed attempt cannot describe a newer unresolved attempt; committed completion receipts continue to dominate stale checkpoints and keep replay closed. Safety passed bounded model checking to depth 18 on a reduced 2-bit identity instance; reachability passed to depth 28 with nine VCD witnesses, while v0.27 deterministic, canonical and bounded-safety regressions remained green. Verified CaPU head: `bc3594b187b4f5901d90db3bd76e1abaa60a80e4`. See [`Verified Report #033`](reports/verified/033-capu-durable-negative-completion/REPORT.md) and its [`machine-readable result`](reports/verified/033-capu-durable-negative-completion/result.json).

Key reproducible reports:

- **#001** OpenAI Agents SDK structural baseline — 95/100;
- **#002** Docker containment — 8/10;
- **#003–#010** recovery, evidence, authority, time and atomic-transition protocols — 10/10 each in their defined synthetic scopes;
- **#011** Transactional Trust Protocol v1.0 End-to-End — 10/10, unsafe compounded path 3 effects vs TTP-safe path 1 effect;
- **#012–#014** PostgreSQL transactional trust, isolation and external-effect boundaries — reproducible scoped results;
- **#015** CaPU v0.10 replay-state recovery across reset — bounded formal PASS with fail-closed restore semantics;
- **#016** CaPU v0.11 checkpoint freshness / anti-rollback — bounded formal PASS with exact-anchor recovery semantics;
- **#017** CaPU v0.12 checkpoint authority commit — bounded formal PASS with persist-then-anchor commit semantics;
- **#018** CaPU v0.13 checkpoint content commitment — bounded formal PASS with canonical replay-state content binding across prepare, persistence, authority commit and anchored recovery;
- **#019** CaPU v0.14 full causal checkpoint state binding — bounded formal PASS binding replay state plus committed causal head, GEN and SEAL across checkpoint construction and recovery;
- **#020** CaPU v0.15 live causal execution resumption — bounded formal PASS restoring replay state plus causal head / GEN / SEAL into live continuation control while recovery remains a fail-closed speculation barrier;
- **#021** CaPU v0.16 causally bound architectural execution resumption — bounded formal PASS coupling PC / four GPRs / status to the recovered causal/replay runtime by one accepted recovery epoch, rejecting split-state recovery and blocking visible effects across recovery/restore;
- **#022** CaPU v0.17 architectural checkpoint content binding — bounded formal PASS binding PC / four GPRs / status plus recovery epoch, causal head / GEN / SEAL and replay spent-state into one exact canonical checkpoint authority, rejecting same-epoch mixed snapshots;
- **#023** CaPU v0.18 precise trap / privilege recovery — bounded formal PASS binding one trap/privilege context to that exact checkpoint authority, rejecting foreign trap bytes, wrong privilege and masked interrupts while preserving exception priority, return-context capture and pre-trap effect containment;
- **#024** CaPU v0.19 delegated + nested trap authority — bounded formal PASS binding delegation policy and a two-frame trap stack to the exact checkpoint authority, rejecting unauthorized delegation, bounded overflow/underflow and foreign parent contexts while preserving exact nested parent capture/return and visible-effect containment;
- **#025** CaPU v0.20 MMU translation / precise page-fault recovery — bounded formal PASS binding a reduced memory view and precise page-fault state to the exact checkpoint authority, rejecting foreign/stale translation state and blocking modeled visible effects across fault/recovery boundaries;
- **#026** CaPU v0.21 TLB freshness / shootdown authority — bounded formal PASS gating cached translations by exact ASID/translation epoch/VPN and permissions, binding modeled TLB/shootdown state, rejecting foreign acknowledgements and destroying stale cached authority across recovery;
- **#027** CaPU v0.22 multi-hart shootdown delivery / acknowledgement quorum — bounded formal PASS binding two-hart acknowledgements to an exact shootdown generation and target, rejecting stale/foreign/duplicate acknowledgements, keeping partial quorum fail-closed, and reopening global translation authority only after exact required-hart coverage;
- **#028** CaPU v0.23 shootdown delivery reliability / bounded retry — bounded formal PASS separating send attempt, observed delivery and acknowledgement authority, rejecting phantom ACKs, recovering lost delivery/ACK through exact retries and keeping retry exhaustion fail-closed;
- **#029** CaPU v0.24 cross-generation message reordering / stale-message quarantine — bounded formal PASS quarantining delayed prior-generation delivery/ACK evidence, preventing it from mutating successor-generation authority, enforcing exact no-wrap successor progression and preserving delivery-before-ACK causality;
- **#030** CaPU v0.25 generation-wrap / ABA protection — bounded formal PASS separating incarnation identity from a wrapping generation counter, quarantining historical same-generation messages with stale incarnations and preventing numeric identifier reuse from recreating authority;
- **#031** CaPU v0.26 accelerator command / DMA recovery authority — bounded formal PASS reconciling stale pre-effect checkpoints against durable DMA-effect receipts, keeping replay authority closed and allowing retirement only after exact reconciliation of an already-committed effect;
- **#032** CaPU v0.27 in-flight DMA completion uncertainty — bounded model-checking PASS preserving `UNKNOWN` across recovery via a durable issue witness, blocking replay/retirement without discriminating evidence, allowing exact negative evidence to reopen replay and exact committed evidence to create a completion receipt that dominates later stale checkpoints;
- **#033** CaPU v0.28 durable negative completion evidence / UNKNOWN convergence — bounded model-checking PASS making exact `NOT_COMMITTED` evidence durable across a later crash, allowing it to dominate stale `UNKNOWN`, while consuming that negative receipt on a new retry so prior-attempt evidence cannot authorize a newer unresolved attempt.

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