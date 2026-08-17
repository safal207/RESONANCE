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

## Evidence boundary

A green run proves only that the reference evaluator enforces the declared fixtures. It does **not** prove that a specific agent runtime exposes enough state to enforce these invariants, nor that its native primitives already satisfy them.

That is the next integration step:

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
