# Evidence revision you can inspect

## Executive Summary

**A working replay is now available.** Evidence Time Machine shows a real GitHub
observation, a concrete commit mismatch, and a reproducible synthetic defect in
how a system changes its conclusion. The browser actually recomputes the two
published deterministic policies; it does not display invented model answers.

**The immediate product hypothesis is evidence-aware decision review for agent
and QA workflows.** Before trusting a changed conclusion, inspect which source,
version, information cutoff and dependency justified the change. This is a proposed
use case, not demonstrated customer demand or a production product.

**The research claim remains narrow.** One GitHub observation supports five
bounded queries; 32 adapter development tests passed. The prior 12-case synthetic
audit reproduced 7/12 original versus 12/12 candidate. No R4/R5 superiority,
independent review, or LLM performance result is claimed.

## A green check does not transfer to a different commit

The source is [GitHub check #101291849079](https://github.com/safal207/RESONANCE/actions/runs/33960652936/job/101291849079).
It reports success for PR-head commit `0bf8f4095a8048d9a2ee145d71c10c9214d72a8c`.
The real merge commit is `d3f79f9e192b2df3a745fa123e0d24f2be2444fa`.
The same check observation supports a narrow claim about the former, not the latter.
`UNKNOWN` for the latter does **not** mean the merge failed or lacks its own tests.

GitHub's [check documentation](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks)
distinguishes check status and conclusion, and ties suites to commits. Our adapter
keeps exact identity and the local time at which the result became available.
It does not infer branch protection, required checks, or deployment safety.

| Query over one selected observation | Expected and observed |
|---|---|
| Before the local observation was available | UNKNOWN |
| Specific run, exact source commit, after receipt | SUPPORTED |
| Same run evidence, different real merge commit | UNKNOWN |
| Valid-time query before that run completed | UNKNOWN |
| Another run intentionally omitted from this snapshot | UNKNOWN |

These are five views of **one** observation, not five customers or integrations.
The practical implication is a clear audit boundary: preserve the earlier answer
and its cutoff rather than quietly filling it with later knowledge.

## The reason to revise needs evidence too

The synthetic replay comes from the [previously published audit](https://github.com/safal207/RESONANCE/tree/0bf8f4095a8048d9a2ee145d71c10c9214d72a8c/benchmarks/temporal-evidence-interim-2026-09-05).
A positive report is followed by a conditional withdrawal. That withdrawal relies
on a diagnostic whose applicability has already expired. The original policy
discards the report without validating this reason. The candidate validates the
dependency and preserves support. This is a defect in the author's toy policy,
not an incident in GitHub or an external system.

The browser labels this case synthetic and recomputes both sides. Four variants
of the same defect account for four of the prior audit's mismatches. A fifth
mismatch is a newly explicit rejection of cyclic justification, not a resolved
real-world cycle. No statistical generalization is made from the 12 cases.

## A larger history still requires measured cost

Adding 10,000 artificial distractors to one scenario preserved the candidate
verdict and the support ID. Median complete local query time was
**687.314 ms** across seven repetitions; observed range
**566.205–752.887 ms**. Construction and validation
cost **59.812 ms** and is separate. Full query time
includes filtering, dependency evaluation, and snapshot fingerprinting.

This is a deterministic stress probe, not 10,000 independent proofs, model
latency, a throughput benchmark, or an SLA. It exposes an engineering cost to
optimize rather than manufacturing an impressive speedup ratio.

## The next milestone is independent replay, not a stronger slogan

A useful external reviewer should run the pinned code, report the exact commit,
case, expected and observed output, and challenge the conditional-withdrawal
semantics. A repository-owned CI runner is another execution environment, not an
independent scientific reviewer. A second team's reproduction is not yet obtained.

After policy review, compare R4 and R5 with the same information in flat and graph
representations, isolate memory, freeze whole-process budgets, and use new episodes.
The primary endpoint is critical evidence-use error, not answer length or eloquence.

## Open questions and limitations

Does the chosen withdrawal rule match a real customer's workflow? How does the
system handle policy-version changes, extraction errors, source authentication,
partial collection and new required checks? How much benefit comes from the
protocol versus simply providing better structured information? These remain open.

Temporal graphs are not a new invention: [Zep's documentation](https://help.getzep.com/searching-the-graph)
already distinguishes when a fact applies and when it was learned or invalidated.
The proposed contribution here is a narrow, inspectable QA experiment about the
basis for revising a decision, not a claim to have invented graph memory.

The source observation is a selected projection from an authenticated connector
read, recorded locally at `2026-09-05T10:41:26Z`. Its saved fingerprint is
`e1ab1661ed7e5e00bff730832566b31639d1a5b47a9c2dcc0e3e19a9b6fb86e4`; that is a content integrity check, not a signature.
0 comparative LLM runs; 0 independent reviewers; no customer, revenue, certification
or autonomous-action claim. Research and code were produced with AI assistance.

[Open the working application](../../site/evidence-time-machine.en.html) ·
[Reproduce and inspect outputs](../../benchmarks/evidence-time-machine-v0.1/README.md) ·
[Challenge the policy](https://github.com/safal207/RESONANCE/issues/74)
