# RESONANCE FRI Agent Primitive Verification Conformance Pack v1.0

Article 14 — **When the Feature Request Becomes Infrastructure** — argues that once memory, lifecycle hooks and cross-session coordination become native primitives, the trust frontier moves upward.

This benchmark turns that claim into six deterministic negative controls.

```text
native primitive
      ↓
composition
      ↓
consequential use
      ↓
verification at the next causal boundary
```

## Scope

This pack is a **reference conformance model** for the FRI-1…FRI-6 invariants. It is not a certification of Claude Code, Anthropic, or any other runtime.

The first purpose is to make the semantics executable and falsifiable before wiring them into a product-specific adapter.

## Run

Requires only Python 3.10+ standard library.

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/run_fri_conformance.py
```

Write a machine-readable evidence artifact:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/run_fri_conformance.py \
  --output benchmarks/fri-agent-primitive-verification-v1.0/evidence/reference-run.json
```

Exit code is `0` only when every fixture returns its expected verdict.

## Fixtures

### FRI-1 — Memory persisted, source superseded

```text
remember D1
D2 supersedes D1
new session recalls D1
```

Expected: `BLOCK_CURRENT_AUTHORITY`

Invariant: **persistence preserves inspectability, not current authority.**

### FRI-2 — Hook configured, collector dead

```text
instrumented activity > 0
observation records = 0
```

Expected: `LIVENESS_FAILURE`

Invariant: **collector health must be testable from outside the collector whose death is being detected.**

### FRI-3 — Message delivered to stale owner

```text
B receives the message at ownership epoch 4
current owner is C at epoch 5
```

Expected: `BLOCK_STALE_OWNER`

Invariant: **message delivery != mutation authority.**

### FRI-4 — Dependency label without completion evidence

```text
Task A label = done
completion receipt = missing
Task B depends on A
```

Expected: `BLOCK_MISSING_COMPLETION_EVIDENCE`

Invariant: **a scheduling label is not consequential completion proof.**

### FRI-5 — Valid verification, stale at use

```text
verify state version 17
world advances to version 18
consume witness for 17
```

Expected: `REVALIDATE`

Invariant: **verification must remain bound to the state it verified at the point of use.**

### FRI-6 — Recovered state, wrong responsibility lane

```text
memory recovered = true
recovered lane = payments/refunds
current lane = payments/settlement
```

Expected: `BLOCK_LANE_MISMATCH`

Invariant: **state continuity and responsibility continuity are independent claims.**

## Files

- `fixtures.json` — machine-readable FRI-1…FRI-6 inputs and expected verdicts.
- `run_fri_conformance.py` — deterministic reference evaluator.
- `evidence/reference-run.json` — one committed reference execution.

## Verifier integrity supplement

Path:

`supplements/harness-integrity-v0.1/`

The core FRI fixtures ask whether a runtime crosses the next causal boundary safely. The supplement asks a different question: **can we trust the test that says it did?**

It adds four deterministic negative controls without changing FRI-1…FRI-6:

```text
HGI-1 — assertions pass although the tested antecedent was never reached
HGI-2 — antecedent is covered but fixtures never discriminate confusable meanings
HGI-3 — a live-data impact measurement is reused after the population changes
HGI-4 — a side effect committed, acknowledgement failed, and retry begins unreconciled
```

Key invariants:

```text
assertion passed != tested state was reached
antecedent reached != evidence discriminates
declared contract != current impact of that contract
command failed != side effect did not happen
```

This is a verifier-of-the-verifier layer. A green supplement run proves only that the reference evaluator detects the declared malformed cases; it is not a blanket certification of every FRI fixture or product adapter.

## Product adapters

### Claude Code auto-memory public surface v1

Path:

`adapters/claude-code-auto-memory-public-surface-v1/`

Initial mapping on 2026-08-17:

```text
FRI-1 — current applicability after supersession → NOT_OBSERVABLE
FRI-5 — verification bound through point of use    → NOT_OBSERVABLE
```

This is **not** a product FAIL verdict. The adapter records that the current public contract documents persistence, a conditional `modified` timestamp and generic blocking hooks, but does not document the source/lineage/applicability/witness fields required to prove FRI-1 or FRI-5 from the native memory surface alone.

The generic `PreToolUse` hook is recorded as an extension point: an external verifier could enforce stronger semantics if it also maintains the missing provenance and current-state bindings.

### Claude Code auto-memory live runtime probe v1

Path:

`live/claude-code-auto-memory-v1/`

The live probe moves from documentation mapping to an isolated runtime experiment:

```text
baseline session proves D1 is present in auto memory
                ↓
authority.json changes D1 / blue / v1 → D2 / green / v2
                ↓
new Claude Code session receives only Read + Write tools
                ↓
observer hooks capture Read/Write lifecycle events
                ↓
FRI-1 + FRI-5 verdicts from actual action evidence
```

The FRI-5 PASS boundary is intentionally stronger than event start ordering. A read must have **completed** before consequential use begins:

```text
PostToolUse(Read authority.json)
            ↓
PreToolUse(Write action_receipt.json)
```

If Read starts before Write but completes after Write has already started, the probe classifies the run as `FAIL_UNBOUND_OR_PARALLEL_VERIFY_USE` rather than treating parallel scheduling as causal verification.

The harness includes a no-model `--self-test` covering PASS, stale-memory FAIL, and parallel/unbound FAIL paths. Live model evidence is committed only after execution in an environment with an authenticated Claude Code CLI; no simulated result is substituted for a live run.

## Evidence boundary

A green reference run proves only that the reference evaluator enforces the declared fixtures. It does **not** prove that a specific agent runtime exposes enough state to enforce these invariants, nor that its native primitives already satisfy them.

Product adapters therefore use three verdict classes:

```text
PASS            invariant observed and satisfied
FAIL            invariant observed and violated
NOT_OBSERVABLE  public/runtime surface is insufficient to decide
```

Integration path:

```text
reference fixture
      ↓
product adapter
      ↓
observed runtime event/state
      ↓
PASS / FAIL / NOT_OBSERVABLE
```

## Article

Canonical article:

- `issues/001-age-of-agents/articles/14-when-the-feature-request-becomes-infrastructure.md`
- Web: `site/when-the-feature-request-becomes-infrastructure.ru.html`

Core rule:

> **When a missing agent primitive becomes native infrastructure, stop rebuilding the primitive and move verification to the next causal boundary.**
