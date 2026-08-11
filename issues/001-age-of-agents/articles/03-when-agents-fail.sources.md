# Evidence Registry — When Agents Fail

Article: `03-when-agents-fail.md`

Accessed: **2026-08-11**

## WF-S01 — Designing AI agents to resist prompt injection

- **Type:** primary / security engineering
- **Publisher:** OpenAI
- **Published:** 2026-03-11
- **URL:** https://openai.com/index/designing-agents-to-resist-prompt-injection/
- **Supports:** C1
- **Use:** Establishes prompt injection as an evolving social-engineering problem for agents that process external content and take actions.
- **Limitation:** Vendor account of its own threat model and defenses.

## WF-S02 — Running Codex safely at OpenAI

- **Type:** primary / production security engineering
- **Publisher:** OpenAI
- **Published:** 2026-05-08
- **URL:** https://openai.com/index/running-codex-safely/
- **Supports:** C3, C4
- **Use:** Documents sandbox boundaries, approvals, network policy, and agent-native telemetry including prompts, tool results and policy decisions.
- **Limitation:** Describes OpenAI's environment; not a universal architecture.

## WF-S03 — Understanding prompt injections

- **Type:** primary / safety guidance
- **Publisher:** OpenAI
- **URL:** https://openai.com/safety/prompt-injections/
- **Supports:** C1
- **Use:** Defines prompt injection and gives action/data-exposure examples plus defense-in-depth guidance.
- **Limitation:** Product-oriented safety explanation rather than independent incident dataset.

## WF-S04 — How we contain Claude across products

- **Type:** primary / engineering report
- **Publisher:** Anthropic
- **Published:** 2026-05-25
- **URL:** https://www.anthropic.com/engineering/how-we-contain-claude
- **Supports:** C2, C3
- **Use:** Documents approval fatigue, containment strategy, blast-radius framing, model-defense limits, and a controlled internal red-team prompt/exfiltration case.
- **Limitation:** Internal evidence from one vendor; reported telemetry and red-team results are not independently reproduced here.

## WF-S05 — Insights into AI Agent Security from a Large-Scale Red-Teaming Competition

- **Type:** primary / government research summary
- **Publisher:** NIST CAISI
- **Published:** 2026-03-23
- **URL:** https://www.nist.gov/blogs/caisi-research-blog/insights-ai-agent-security-large-scale-red-teaming-competition
- **Supports:** C1
- **Use:** Establishes agent hijacking / indirect prompt injection as an empirically tested security concern in a large-scale competition.
- **Limitation:** Summary page; detailed benchmark methodology lives in the associated research paper.

## WF-S06 — Summary Analysis of Responses to the RFI Regarding Security Considerations for AI Agents

- **Type:** primary / government report
- **Publisher:** NIST
- **Published:** 2026-05-18
- **URL:** https://www.nist.gov/publications/summary-analysis-responses-request-information-regarding-security-considerations-ai
- **Supports:** C1, C6 context
- **Use:** Reports broad agreement among RFI respondents that agent security requires adaptation of existing security practices and identifies threats including adversarial data and harmful autonomous actions.
- **Limitation:** Synthesizes stakeholder responses; consensus evidence is not equivalent to direct experimental proof.

## WF-S07 — GHSA-v7px-3835-7gjx / CVE-2026-40111

- **Type:** primary vendor advisory / vulnerability record
- **Publisher:** GitHub / PraisonAI project
- **Published:** 2026-04
- **URL:** https://github.com/MervinPraison/PraisonAI/security/advisories/GHSA-v7px-3835-7gjx
- **Supports:** C5
- **Use:** Documents OS command injection in PraisonAIAgents memory hooks and a lifecycle configuration path capable of recurring execution after agent-controlled file writes; fixed in 1.5.128.
- **Limitation:** One implementation vulnerability; it should not be generalized to all agent frameworks.

## WF-S08 — OWASP GenAI Security Project

- **Type:** open security framework / practitioner standard
- **Publisher:** OWASP GenAI Security Project
- **URL:** https://genai.owasp.org/
- **Supports:** taxonomy context / counter-boundary
- **Use:** Provides security threat taxonomies for agentic applications. Used to distinguish security threat categories from the RESONANCE structural QA coordinates.
- **Limitation:** Community framework; RESONANCE's eight-axis taxonomy is separate and should not be represented as an OWASP standard.

## Counter-evidence / constraints

- Many dimensions in the RESONANCE taxonomy are not unique to AI; they overlap with mature distributed-systems, workflow, security, and QA practices.
- Strong containment can reduce agent utility, so appropriate controls depend on impact and reversibility.
- The 16 benchmark cases are synthetic specifications, not claims that each scenario has occurred in production.
- The RESONANCE Agent Failure Benchmark is an early v0.1 proposal and has not yet been externally validated or calibrated across multiple runtimes.
