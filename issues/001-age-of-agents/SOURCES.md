# Issue 001 — Source Registry

This file is the evidence registry for **THE AGE OF AGENTS**.

Sources are added only when they are actually used, inspected, and linked to a specific article or claim.

## The Agentic Turn

### S-001 — The next evolution of the Agents SDK

- **Type:** primary
- **Publisher / author:** OpenAI
- **Publication date:** 2026-04-15
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C1
- **URL:** https://openai.com/index/the-next-evolution-of-the-agents-sdk/
- **Limitations:** Vendor source; establishes product architecture and capabilities, not independent adoption or outcome data.
- **Notes:** Documents native sandbox execution, file access, commands, code editing and long-horizon tasks.

### S-002 — Speeding up agentic workflows with WebSockets in the Responses API

- **Type:** primary
- **Publisher / author:** OpenAI
- **Publication date:** 2026-04-22
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C1
- **URL:** https://openai.com/index/speeding-up-agentic-workflows-with-websockets/
- **Limitations:** Vendor engineering account; does not establish economy-wide usage.
- **Notes:** Describes repeated next-action → tool execution → tool-result cycles in long-running agentic workflows.

### S-003 — Anthropic Economic Index: Cadences

- **Type:** primary / dataset report
- **Publisher / author:** Anthropic
- **Publication date:** 2026-06-26
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C1
- **URL:** https://www.anthropic.com/research/economic-index-june-2026-report
- **Limitations:** Measures Anthropic ecosystem usage and methodology; not representative of all AI usage.
- **Notes:** Reports increasing long-running agentic tasks and explains why conversational transcripts alone no longer capture all usage patterns.

### S-004 — Trustworthy agents in practice

- **Type:** primary / research
- **Publisher / author:** Anthropic
- **Publication date:** 2026-04-09
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C1, C2
- **URL:** https://www.anthropic.com/research/trustworthy-agents
- **Limitations:** Publisher has commercial interest in agent products; governance framing is partly normative.
- **Notes:** Describes agents that write and execute code, manage files and complete tasks across applications with less direct human oversight.

### S-005 — How we contain Claude across products

- **Type:** primary / engineering
- **Publisher / author:** Anthropic
- **Publication date:** 2026-05-25
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C2
- **URL:** https://www.anthropic.com/engineering/how-we-contain-claude
- **Limitations:** Internal engineering evidence; does not independently quantify external incident rates.
- **Notes:** Explicitly frames growing agent blast radius and containment as production engineering concerns.

### S-006 — How A2A is Building a World of Collaborative Agents

- **Type:** primary / engineering ecosystem
- **Publisher / author:** Google Developers Blog
- **Publication date:** 2026-06-18
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C3
- **URL:** https://developers.googleblog.com/how-a2a-is-building-a-world-of-collaborative-agents/
- **Limitations:** Vendor ecosystem source; adoption examples may be selectively highlighted.
- **Notes:** Describes agent collaboration, delegation and handoff as protocol-level problems addressed by A2A.

### S-007 — Agentic AI Foundation adds 43 new members

- **Type:** primary / institutional announcement
- **Publisher / author:** Linux Foundation
- **Publication date:** 2026-05-18
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C3
- **URL:** https://www.linuxfoundation.org/press/agentic-ai-foundation-adds-43-new-members-as-enterprise-and-government-adoption-of-open-agent-standards-accelerates
- **Limitations:** Membership growth is an ecosystem signal, not proof that standards have converged or achieved production dominance.
- **Notes:** Evidence that open agent standards and tooling are being organized as shared infrastructure concerns.

### S-008 — Coding agents in the social sciences

- **Type:** primary / survey research
- **Publisher / author:** Anthropic
- **Publication date:** 2026-05-27
- **Accessed:** 2026-08-11
- **Used in:** `articles/01-the-agentic-turn.md`
- **Supports:** C5 / counter-evidence
- **URL:** https://www.anthropic.com/research/coding-agents-social-sciences
- **Limitations:** Sample is limited to social scientists and should not be generalized to all occupations.
- **Notes:** Survey of 1,260 social scientists; broad chatbot experimentation but substantially lower coding-agent adoption. Preserved as a constraint on the headline thesis.

## The Missing Trust Layer

### S-009 — OpenAI Agents SDK

- **Type:** primary / technical documentation
- **Publisher / author:** OpenAI
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C1
- **URL:** https://openai.github.io/openai-agents-python/
- **Limitations:** One runtime architecture; does not establish a universal agent design.
- **Notes:** Documents agent loops, handoffs, sandbox agents, guardrails, sessions, human-in-the-loop mechanisms and built-in tracing.

### S-010 — OpenAI Agents SDK Guardrails

- **Type:** primary / technical documentation
- **Publisher / author:** OpenAI
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C1 / counter-evidence
- **URL:** https://openai.github.io/openai-agents-python/guardrails/
- **Limitations:** Guardrail coverage differs by tool and execution path.
- **Notes:** Preserved specifically because the documentation describes scope boundaries; guardrails are useful controls but not a universal trust guarantee.

### S-011 — Agent2Agent (A2A) Protocol Specification

- **Type:** primary / protocol specification
- **Publisher / author:** A2A Project
- **Version:** current repository specification; latest released version shown as 1.0.0 at verification time
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C2
- **URL:** https://github.com/a2aproject/A2A/blob/main/docs/specification.md
- **Limitations:** Interoperability protocol; does not attempt to solve all governance, invariant or recovery concerns.
- **Notes:** Defines tasks as stateful units with lifecycle states, timestamps, history and artifacts.

### S-012 — OpenTelemetry Context Propagation

- **Type:** primary / technical documentation
- **Publisher / author:** OpenTelemetry
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C3
- **URL:** https://opentelemetry.io/docs/concepts/context-propagation/
- **Limitations:** Observability standard, not an authorization or domain-correctness system.
- **Notes:** Documents propagation of trace context and causal information across distributed process and network boundaries.

### S-013 — Temporal Documentation

- **Type:** primary / technical documentation
- **Publisher / author:** Temporal
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C4
- **URL:** https://docs.temporal.io/
- **Limitations:** Product documentation; durable execution does not itself establish domain correctness or agent authorization.
- **Notes:** Documents resumption of application progress after crashes, network failures and infrastructure outages.

### S-014 — Sigstore / Cosign Verification

- **Type:** primary / technical documentation
- **Publisher / author:** Sigstore
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C5
- **URL:** https://docs.sigstore.dev/cosign/verifying/verify/
- **Limitations:** Artifact integrity and identity evidence do not prove the correctness of the workflow that created the artifact.
- **Notes:** Documents verification of signatures and attestations, including identity, artifact digest and transparency-log evidence.

### S-015 — Sigstore Security Model

- **Type:** primary / security documentation
- **Publisher / author:** Sigstore
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C5 / limitations
- **URL:** https://docs.sigstore.dev/about/security/
- **Limitations:** Specific to Sigstore's trust model.
- **Notes:** Explicitly documents guarantees and non-guarantees, supporting the article's principle that verification claims must expose their assumptions.

### S-016 — OpenTelemetry Tracing API

- **Type:** primary / specification
- **Publisher / author:** OpenTelemetry
- **Accessed:** 2026-08-11
- **Used in:** `articles/02-the-missing-trust-layer.md`
- **Supports:** C3
- **URL:** https://opentelemetry.io/docs/specs/otel/trace/api/
- **Limitations:** Defines telemetry semantics, not policy or business invariants.
- **Notes:** Spans include parent/context relationships, timestamps, events, links and status; useful precedent for explicit causal structure and time.

## Article 13 — Evidence Must Bind the Transition

Article 13 uses a dedicated evidence ledger because its primary material is a live public architecture discussion whose implementation reports, proposals, synthesis and non-claims must remain separately classified.

- **Article:** [`articles/13-evidence-must-bind-the-transition.md`](articles/13-evidence-must-bind-the-transition.md)
- **Dedicated evidence ledger:** [`articles/13-evidence-must-bind-the-transition.sources.md`](articles/13-evidence-must-bind-the-transition.sources.md)
- **Web edition:** https://safal207.github.io/RESONANCE/evidence-must-bind-the-transition.ru.html
- **Primary public threads:** `crewAIInc/crewAI#4877`, `langchain-ai/langgraph#5672`
- **Core distinction:** public implementation reports and public design proposals are evidence inputs; `Evidence-Bound Transition`, `Terminality Binding`, and `EBT-I1..I7` are RESONANCE synthesis and are not claimed as vendor-native guarantees.

The dedicated ledger preserves exact comment links, source classification, claim mapping, explicit non-claims and the proposed EBT falsification suite.

## Evidence rules

- Prefer primary evidence where possible.
- Do not add a source simply because it agrees with the thesis.
- Record material limitations and conflicts.
- Preserve contradictory evidence.
- Distinguish event date from publication date.
- If a source changes after publication, record the version or access date used.

## Counter-evidence

Important stories should actively preserve evidence that weakens or contradicts the working thesis.

A trustworthy evidence package is not a collection of supporting links. It is a record of what was examined and why the conclusion survived.
