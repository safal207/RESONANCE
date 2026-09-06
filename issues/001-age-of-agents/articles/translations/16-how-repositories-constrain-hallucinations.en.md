# Reducing hallucinations: from answers to verifiable outcomes

**Article ID:** 016

**Deck:** What CML, ContractGraph-QA, PythiaLabs and LiminalQA can already check — and the experiment needed to measure fewer AI-agent errors.

**By:** Aleksei Safonov

**Status:** Publication-ready research explainer

**Last verified:** 2026-09-06

**Languages:** EN

**Canonical identity:** article016 / how-repositories-constrain-hallucinations

## The agent said “done.” What happened?

Imagine an agent reporting: “All checks passed; the change is ready to release.” Its link leads to a real report. But that report belongs to the previous commit, some checks never ran, and release approval was never given. The wording is convincing. The operational conclusion is unsupported.

Several distinct problems are involved. An invented test result is an unsupported claim. Applying an old report to new code is an applicability error. Treating verification as permission is an authority error. Checking them separately exposes the broken boundary that a single “reliable agent” score can hide.

Our engineering thesis is that explicit sources, verification rules, current scope and observed outcomes can reduce the unsupported conclusions a system accepts and acts on. This is a proposed design for the system around a model. This article does not measure a change in the model’s hallucination rate.

## Retrieval is the first layer

Lewis et al.’s Retrieval-Augmented Generation combines retrieved documents with parametric memory. On the authors’ evaluated tasks, generation was more factual than the selected baseline. This supports using external sources; it does not establish that every answer from every RAG application is true. [S1]

FActScore decomposes long answers into atomic facts and evaluates the fraction supported by a reliable source. The useful principle for our work is to check each consequential claim separately. Results from an earlier study cannot be transferred to a current model or our repositories. [S2]

A practical extension is to bind each claim to a specific passage, version and observation time. Merely including a link does not show that the document supports that conclusion. A stale source or an incorrect interpretation remains possible.

## Four repositories, four questions

| Component | Present in the inspected revision | Contribution | Remaining boundary |
|---|---|---|---|
| Causal-Memory-Layer | Parent and configurable approval-ancestor audits; two cases replayed | Detects when a claimed decision lacks the required approval-record ancestry | Reads a trace; does not itself block actions or authenticate the record [S3] |
| ContractGraph-QA | Payment-recovery trace evaluation; four seed cases replayed | Detects retry under unresolved ambiguity and broken retry identity | Checks supplied events; does not prove source completeness or an actual receiver-side effect [S4] |
| PythiaLabs | Documented pre-tool ALLOW / BLOCK / ESCALATE gate MVP | Provides an explicit decision pattern for action conditions | Documentation inspected here; PythiaLabs execution was not run. ALLOW does not execute the action [S5] |
| LiminalQA | Typed decision packet including Unknown and ObserveOnly | Exposes test signals and insufficient-data outcomes in a machine-readable form | Types and heuristics do not prove root cause; the Rust component was not run here [S6] |

These roles are complementary. Their existence in separate repositories does not establish a complete, integrated path from answer checking to execution. The composition below is an integration proposal. Existing components and locally executed evidence are identified separately.

## What should accompany a claim?

The first prototype can use a small claim ledger. This is a proposed integration format, not a shared API already implemented by all four projects.

| Field | Meaning |
|---|---|
| claim_id, claim_text | The precise claim being checked |
| evidence_refs | Original passages or artifacts supporting it |
| source_commit, subject_id | The inspected source version and subject |
| observed_at, applicable_until | When evidence was obtained and when or under what condition to recheck it |
| status | SUPPORTED / CONTRADICTED / UNKNOWN: support by the evidence |
| decision_ref | A separate reference to the action-admission decision |
| result_ref | A separate outcome observation if an action was performed |

First, the system obtains evidence and preserves its version. It then decomposes the answer into checkable claims and matches each to supporting evidence. Before an action, it rechecks the subject, time, conditions and authority. Afterward, it records an observed result or leaves the outcome UNKNOWN.

When evidence is missing, an agent can request an artifact, continue safe information gathering or narrow its answer explicitly. For a consequential action, incomplete mandatory conditions should cause a stop or human escalation. That is a rule for the proposed integration: a passive auditor does not enforce it by itself.

A valid JSON structure checks form. A hash helps detect changed bytes. A connected graph checks relationships within recorded data. None independently authenticates the truth of the original message. Receipt validity, correlation of two receipts with one call, effect count and exactly-once guarantees require distinct evidence.

## What was reproduced now?

On 6 September 2026, we executed the existing CML approval example and four existing CGQA fixtures. Source revisions are pinned; inputs and full outputs are preserved. Expected classifications were recorded before execution. Two consecutive evaluations produced identical results. [S7]

| Scenario | Observed result |
|---|---|
| CML: required approval ancestors absent | FAIL; CML-AUDIT-R5-EXEC_REQUIRES_HUMAN_APPROVAL and CML-AUDIT-R7-ML_ACTION_REQUIRES_POLICY_APPROVAL |
| CML: approval records present | PASS; no findings |
| CGQA: committed, then stop | pass |
| CGQA: failed, then retry with continuous identity | pass |
| CGQA: retry before outcome reconciliation | fail; APR-001_UNRESOLVED_AMBIGUITY_FINANCIAL_ACTION and APR-009_TRACE_ENDS_UNRESOLVED |
| CGQA: retry key changed after failed | fail; APR-004_IDEMPOTENCY_CHANGED_ON_RETRY |

All 6 of 6 preregistered classifications matched: three negative cases were detected and three positive cases passed. This checks the rules’ ability to distinguish selected examples. No LLM was called and no real tool action or payment was executed. “6 of 6” therefore cannot become “hallucinations eliminated” or a production effectiveness percentage.

A particularly important boundary: CML and CGQA in this run detect problems in a supplied trace after it has been constructed. Preventing a future call still requires correctly connecting the result to the executor.

## How to reproduce it

From a RESONANCE checkout containing this article, obtain the two pinned source revisions. The executed environment was Linux, Python 3.12.13 and PyYAML 6.0.3. PyYAML is this example’s only external Python dependency; install it in your virtual environment. Replay itself is local.

```bash
git clone https://github.com/safal207/Causal-Memory-Layer.git ../cml-article016
git -C ../cml-article016 checkout 7a3a98c60a402d394e4d286da956823898454b8a
git clone https://github.com/safal207/ContractGraph-QA.git ../cgqa-article016
git -C ../cgqa-article016 checkout f861b934d77e64fd35f768e2a33bb4a00963bc19
python -m pip install PyYAML==6.0.3
python scripts/reproduce-article016.py --cml ../cml-article016 --cgqa ../cgqa-article016 --output article016-replay.json
```

Expected fields: matched_cases = 6, repeat_equal = true. The canonical results array has SHA-256 7a391291204b358bc1c2323186d981e1d993d1d86ef91d7dcf509a361d6e7ff1. The full file also contains environment versions, Python-source hashes, input events and native diagnostics. This is local author-side reproduction; independent external replication is not claimed.

## Measuring an actual reduction in errors

The next experiment needs real model outputs. We propose a pilot with 30 tasks labelled in advance: six each with sufficient evidence, a missing source, contradictory evidence, stale evidence and an unknown action outcome. This is an initial size for finding problems, not a statistical-power justification.

Compare three modes: the model with a normal prompt; the same model with retrieval; and the same retrieval and retrieved documents plus a claim ledger and explicit checks. Freeze the shared evidence set for the last two modes. Preserve model version, settings, prompts, available tools and budgets; repeat each task three times, giving 90 runs per mode. Randomize mode order and judge answers without their mode labels.

| Metric | Calculation |
|---|---|
| Unsupported claims | Unsupported atomic claims / all atomic claims in accepted answers |
| Task coverage | Fully and correctly solved tasks / all tasks |
| Unnecessary stops | Stopped tasks with sufficient evidence / all tasks with sufficient evidence |
| Admission violations | Proposals missing mandatory conditions admitted to a mock executor / all such proposals |
| Verification cost | Response time and cost per task, including repeated checks |

UNKNOWN counts as abstention, not a factual error. With zero accepted claims, the first fraction is undefined, not zero. A system that refuses everything does not win. Report raw counts, results for each of the five groups and variation across tasks; repetitions of one task are not independent tasks.

The hypothesis weakens if additional checks do not reduce unsupported-claim acceptance compared with identical retrieval, or achieve that reduction through a substantial loss of useful answers. Choose the acceptable coverage loss and budget before running. This experiment has not yet been performed in this article.

## The first useful integration

Start with one scenario: an agent reads CI artifacts for a pinned commit and prepares a report. It must distinguish “check passed,” “check did not run” and “report belongs to another revision.” The output is a claim table with sources and one justified next step. After validating that prototype, add tool admission and outcome observation as separate work.

Our practical target is that every consequential claim has inspectable support, every action has current admission conditions, and every claimed outcome has an observation. Being able to say “we do not know this yet” is a useful product capability.

The author participates in developing the repositories discussed. This is an engineering analysis of our own projects, not independent certification. AI assisted drafting and translation; factual support comes from pinned sources, primary papers and the preserved local run.
