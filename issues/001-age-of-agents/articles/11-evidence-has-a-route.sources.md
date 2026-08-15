# Sources & Evidence Map — Article 11: Evidence Has a Route

**Article:** `11-evidence-has-a-route.md`  
**Article ID:** I001-RN-ELR  
**Status:** Published companion  
**Last verified:** 2026-08-15

---

## Evidence policy

Article 11 separates:

1. **public architecture discussion** — claims made in public upstream threads;
2. **verified repository facts** — files, PRs, tests and CI states we can inspect directly;
3. **RESONANCE design inference** — new abstractions proposed by this article;
4. **future falsification targets** — claims that remain hypotheses until implemented and tested;
5. **reader judgment** — poll responses, which are signal rather than proof.

A public implementation report is not automatically upgraded to an independently reproduced fact.

---

## S1 — CrewAI GuardrailProvider discussion

Thread:

https://github.com/crewAIInc/crewAI/issues/4877

Relevant architecture discussed publicly includes provider-agnostic pre-tool authorization, sync/async authorization, durable `DEFER`, freshness binding, policy/version state and execution continuation concerns.

**Evidence class:** public architecture discussion.

---

## S2 — sync-only occurrence-binding response

Comment by `babyblueviper1`:

https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5300582003

The commenter explicitly distinguishes their current synchronous check-then-act architecture from an async deferred-consumption lifecycle, while reporting that multiple independently issued signed events can share the same semantic `decision_ref`.

They also ask whether an `AuthorizationOccurrence.status` should collapse operationally in a sync-only implementation.

**Evidence class:** public architecture description + public implementation report.

**Important qualifier:** the reported production-ledger examples are attributed to the commenter and are not independently reproduced by RESONANCE in this article.

---

## S3 — Article 10: Consent Has a Causal Lifetime

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/10-consent-has-a-causal-lifetime.md

Article 10 separates:

```text
semantic decision identity
!= authorization occurrence
!= execution consumption
```

and introduces the Authorization Consumption Boundary (ACB).

**Evidence class:** prior RESONANCE design model.

---

## S4 — ACB-001 executable reference contract

PR:

https://github.com/safal207/pythiaLabs/pull/260

Exact-head conformance run referenced at publication time:

https://github.com/safal207/pythiaLabs/actions/runs/31865527490

ACB-001 provides a framework-neutral executable contract for authorization occurrence, execution-scope binding and consumption semantics.

**Evidence class:** verified repository / CI evidence.

**Non-claim:** ACB-001 does not prove atomicity with arbitrary external side effects and does not imply adoption by CrewAI, AG2 or another vendor.

---

## S5 — FCRP / causal coordinates lineage

Article 05:

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/05-fractal-causal-refactoring.md

FCRP introduced reasoning over scale, time, causality and intent to locate the first meaningful divergence and select a high-leverage intervention point.

Article 11 extends that style of reasoning from **where to refactor** to **which proof route is appropriate at the current causal point**.

**Evidence class:** internal conceptual lineage.

---

## S6 — Article 11: Evidence Logistics Routing

The following claims are **new RESONANCE design inferences**, not upstream guarantees:

- sync vs async may be treated as a contextual route choice rather than a universal category;
- proof acquisition / verification / authorization can be represented as a routing graph;
- the target can be modeled as a constrained shortest-path problem;
- hard proof obligations should filter the admissible route set before cost optimization;
- route validity should be bound to causal coordinates such as state, time, authority and policy;
- a previously optimal route may become inadmissible after material context change;
- route selection must remain distinct from execution authority.

These are proposals to test, not claims of established consensus.

---

## S7 — Reader poll

Poll:

https://github.com/safal207/RESONANCE/issues/58

Options:

- Agree
- Partially agree
- Disagree

Reader votes are **not** correctness evidence.

They are useful for:

- discovering missing constraints;
- finding counterexamples;
- locating implementation contexts;
- measuring whether the abstraction is understandable or contentious.

A reproducible counterexample can outweigh broad agreement.

---

## Claim map

| Claim | Evidence status |
|---|---|
| CrewAI thread discusses sync/async pre-tool authorization | Verified public thread fact |
| ACB-001 exists as executable reference contract | Verified repository fact |
| ACB-001 exact-head CI run 31865527490 succeeded | Verified CI fact at publication time |
| sync and async should always be dynamically routed | **Not claimed** |
| Evidence Routing is already adopted by CrewAI | **Not claimed** |
| Dijkstra/A* is the normative algorithm | **Not claimed** |
| strongest route is always wasteful | **Not claimed** |
| cheapest route is safe if risk score is low | **Not claimed** |
| hard obligations must remain outside negotiable cost weights | RESONANCE normative design proposal |
| route decisions should have provenance / validity conditions | RESONANCE design proposal |
| poll agreement proves correctness | **Explicitly rejected** |

---

## Proposed falsification suite

Future executable work should test at least:

```text
A. low-risk reversible action -> cheap sync route admissible
B. cached evidence without required freshness -> blocked
C. high-risk action missing mandatory human/independent verification -> route inadmissible
D. authority epoch changes after route selection -> route invalidates
E. one-shot authorization consumed -> retry requires new admissible route or blocks
F. same nominal action under changed risk/context -> route may change
G. cheapest route violates hard obligation -> optimizer must select costlier admissible route or block
H. no admissible route -> fail closed
I. optimizer cannot turn a hard obligation into a soft cost penalty
J. route provenance explains selected and rejected alternatives sufficiently for independent inspection
```

Passing these tests would support the operational model. It would not constitute a formal safety/liveness proof.
