# Article 016 — claim and source ledger

Verified locally: 2026-09-06. Classification: research explainer about repository capabilities and a proposed integration. Author involvement in the projects is disclosed in all three editions.

## Source identities

| ID | Primary source | Exact scope |
|---|---|---|
| S1 | [Lewis et al., Retrieval-Augmented Generation, 2020](https://arxiv.org/abs/2005.11401) | Authors' reported factuality improvement on their evaluated generation tasks; not a universal RAG guarantee |
| S2 | [Min et al., FActScore, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.741/) | Atomic-fact support measurement; no historical model percentage reused as a current result |
| S3 | [CML approval example](https://github.com/safal207/Causal-Memory-Layer/blob/7a3a98c60a402d394e4d286da956823898454b8a/examples/agent_approval_lineage_audit.py), [audit implementation](https://github.com/safal207/Causal-Memory-Layer/blob/7a3a98c60a402d394e4d286da956823898454b8a/cml/audit.py) | Actual native audit of the two existing synthetic traces; audit is read-only and does not enforce |
| S4 | [CGQA evaluator](https://github.com/safal207/ContractGraph-QA/blob/f861b934d77e64fd35f768e2a33bb4a00963bc19/contractgraph_qa/payment_recovery.py), [benchmark and seed inputs](https://github.com/safal207/ContractGraph-QA/tree/f861b934d77e64fd35f768e2a33bb4a00963bc19/benchmarks/agent-payment-recovery-v0.1) | Four existing native trace evaluations; not provider observation or a production audit |
| S5 | [PythiaLabs limitations](https://github.com/safal207/pythiaLabs/blob/dadc0f18a0c4e5d65fe50a3bab32ee34512975b9/docs/LIMITATIONS.md) | Documented MVP and ALLOW / BLOCK / ESCALATE boundary; execution NOT_RUN |
| S6 | [LiminalQA decision types](https://github.com/safal207/LiminalQAengineer/blob/fb1fc7771e7ba29d4edc30ee38b09b4d9dce3c86/liminalqa-core/src/decision.rs) | Typed Unknown and ObserveOnly exist; no accuracy or runtime performance claim; execution NOT_RUN |
| S7 | [Plan](https://github.com/safal207/RESONANCE/blob/main/evidence/article016/plan.md), [native replay](https://github.com/safal207/RESONANCE/blob/main/evidence/article016/native-replay.json), [runner](https://github.com/safal207/RESONANCE/blob/main/scripts/reproduce-article016.py) | This article's local reproduction; six native classifications and two identical evaluations |

## Material claims

| Claim | Classification | Evidence and limit |
|---|---|---|
| Source retrieval is a useful factuality layer | Supported by primary research, task-bounded | S1; no universal reliability claim |
| Evaluate important claims individually | Methodological recommendation | S2 motivates atomic decomposition; our task metrics are a proposed adaptation, not a FActScore implementation |
| CML detects the selected missing-approval ancestors | Observed fact for the pinned example | S3, S7; correct record ancestry is not authenticated authorization |
| CGQA flags unresolved retry and changed retry key | Observed fact for the pinned seed traces | S4, S7; supplied trace evaluation is not effect-count proof |
| PythiaLabs and LiminalQA expose complementary primitives | Source-level observation | S5, S6; neither component was executed for this article |
| Combining these components may reduce accepted unsupported conclusions | Engineering hypothesis | No integrated pipeline or model experiment is claimed as shipped or run |
| Six expected classifications match and two evaluations are equal | Observed local fact | Native results SHA-256: 7a391291204b358bc1c2323186d981e1d993d1d86ef91d7dcf509a361d6e7ff1 |
| Model hallucination rate is reduced by a stated percentage | UNKNOWN / NOT_MEASURED | No model was called; the 30-task, three-mode, three-repeat pilot is proposed only |
| Receipt validity / correlation / effect count / exactly-once are separate claims | Scope distinction / engineering reasoning | Checks of recorded evidence cannot establish unobserved receiver behavior; S3–S5 explicitly retain limited authority |

## Execution record and reproducibility

- Python 3.12.13; Linux; PyYAML 6.0.3.
- Source pins: CML `7a3a98c60a402d394e4d286da956823898454b8a`; CGQA `f861b934d77e64fd35f768e2a33bb4a00963bc19`.
- Native evaluators, fixtures and policies were not modified. The wrapper preserves native inputs and outputs rather than implementing the checking rules.
- First wrapper attempt stopped on a KeyError because it looked for CGQA `verdict`; source inspection established the actual result field `status`. The wrapper was corrected; expectations and native evaluators were unchanged. That failed wrapper attempt is not a successful replay.
- Successful runner exit: 0; matched_cases: 6; repeat_equal: true.
- Original negative findings are preserved, including APR-009_TRACE_ENDS_UNRESOLVED, rather than omitted from the article table.
- No model API, provider API, tool execution, real payment, storage crash, concurrency or external effect-count test was performed.
- This is local author-side reproduction, not independent external validation, statistical generalization, deployment approval or security certification.
- Hashes establish byte identity against the recorded reference; they do not establish source honesty or a trustworthy clock.
- Full CGQA capability scope and the NO_PROMOTION decision are in the preregistered plan. No new upstream rule or defect claim is promoted.

## Proposed experiment, not an observed result

30 labelled tasks, five strata of six tasks, three repeated runs per mode and three modes (90 runs per mode). The retrieval-only and retrieval-plus-checks modes share frozen evidence. Preserve prompts, model settings, source versions, raw output and grading decisions. Blind grading and randomized mode order reduce avoidable evaluation bias. Task repetitions are not independent task samples.

Report unsupported-claim counts and denominators together with solved-task coverage, unnecessary stops, mock-executor admission violations, latency and cost. A zero accepted-claim denominator is undefined. UNKNOWN is abstention, not a factual-error label. Choose the coverage-loss tolerance and budget before running; this small pilot does not establish statistical power.

## Editorial verification

Primary sources opened and code inspected; source revisions pinned; expected versus observed classification checked; outcome/authority/factuality claims kept separate; same substantive text, numbers, commands, sources, limitations and disclosure carried across RU, EN and zh-CN. Static generation, publication links, feeds, translation structure, SEO and correction-history checks are recorded with the publication change. Structural translation parity is not an independent linguistic review.
