# Upstream comment draft — anthropics/claude-code#75405

Target: https://github.com/anthropics/claude-code/issues/75405

Status: **not posted**. The connected GitHub integration returned HTTP 403 (`Resource not accessible by integration`) when attempting to comment on the external repository.

---

One way to make this failure class testable is to split **memory persistence** from **current applicability**, then bind verification through the point of consequential use.

I mapped the report to two small negative controls:

```text
FRI-1 — supersession
remember D1
D2 supersedes D1
new session recalls D1

expected: D1 remains inspectable, but cannot silently become current authority
```

```text
FRI-5 — VERIFY -> USE
verify external state/artifact at N
world changes to N+1
attempt consequential use with witness for N

expected: BLOCK / REVALIDATE
```

This seems complementary to @aditya-samalla's machine-checkable `verify:` idea above: a check can prove a claim at one point in time, but the successful check should not become a freely reusable fact after the state it verified has changed.

I also mapped this against the current public Claude Code memory/hooks docs. The documented native surface gives per-project persistence, on-demand topic files, a conditional `modified` timestamp, and a generic `PreToolUse` blocking seam. I could not find a documented memory source identity/digest, supersession relation, current-applicability verdict, or memory-specific verification witness/state binding. I therefore classify FRI-1 and FRI-5 as **NOT_OBSERVABLE**, not FAIL: the public contract is insufficient to decide whether the runtime already enforces these semantics internally.

A generic `PreToolUse` hook looks sufficient to host an external verifier if it also maintains the missing provenance/state bindings.

Reference fixtures + adapter/evidence:
https://github.com/safal207/RESONANCE/tree/main/benchmarks/fri-agent-primitive-verification-v1.0

The invariant I am trying to preserve is simply:

```text
persistence != current applicability
verification at N != authority to act at N+1
```
