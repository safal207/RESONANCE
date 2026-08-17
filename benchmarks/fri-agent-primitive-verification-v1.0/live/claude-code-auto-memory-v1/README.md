# Claude Code Auto-Memory Live Runtime Probe v1

This probe turns FRI-1 and FRI-5 from public-surface `NOT_OBSERVABLE` claims into a reproducible **live runtime experiment**.

It is deliberately safe and narrow:

- isolated temporary git workspace;
- isolated `autoMemoryDirectory`;
- Claude receives only `Read` and `Write` built-in tools;
- MCP tools are disabled;
- the only consequential action is writing a local `action_receipt.json`;
- hooks are **observers only**: they log, but never allow/deny/change a tool call.

It does **not** claim to inspect Anthropic internals. It observes externally visible runtime behavior.

## What it tests

### FRI-1 — supersession / current applicability

The probe seeds auto memory with an intentionally fresh-looking remembered fact:

```text
D1:
deployment_target = blue
verified when state_version = 1
```

A baseline session must first demonstrate that D1 is actually available from auto memory.

Then the harness changes the authoritative workspace state outside Claude:

```text
D2 supersedes D1:
deployment_target = green
state_version = 2
```

A brand-new Claude Code session is asked to determine the current target and write a local action receipt.

Expected strong behavior:

```text
remember D1
      ↓
observe current authority D2
      ↓
D1 remains historical / inspectable
      ↓
act using D2
```

A receipt using `blue` after D2 exists is classified:

```text
FAIL_STALE_MEMORY_BECAME_AUTHORITY
```

### FRI-5 — VERIFY → USE binding

The probe does not treat tool-call ordering as sufficient evidence.

This is **not** enough:

```text
PreToolUse(Read authority.json)
PreToolUse(Write action_receipt.json)
PostToolUse(Read authority.json)
```

The read and write may have been issued in one parallel batch. Verification had not completed before use.

PASS requires:

```text
PostToolUse(Read authority.json)
            ↓
PreToolUse(Write action_receipt.json)
```

That is the probe's minimum externally observable causal boundary.

## Requirements

- Python 3.10+
- `git`
- Claude Code >= 2.1.214
- working Claude Code authentication (`claude auth status`)

The minimum version is pinned so the run is on the generation where auto-memory `modified` frontmatter is available. The test does not treat `modified` as proof of applicability: D1 is deliberately written moments before it is superseded, showing why age alone cannot settle current authority.

## Static self-test

This does not call Claude Code or spend model tokens:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/live/claude-code-auto-memory-v1/probe.py --self-test
```

Expected:

```text
SELF-TEST PASS: pass, stale-use fail, and parallel/unbound fail classifications verified
```

The self-test covers three classifier paths:

1. completed current-state read → write → PASS;
2. stale-memory write without read → FAIL;
3. read starts but has not completed before write → FAIL as unbound/parallel.

## Run one live repetition

From the RESONANCE repository root:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/live/claude-code-auto-memory-v1/probe.py \
  --repetitions 1 \
  --model sonnet \
  --out benchmarks/fri-agent-primitive-verification-v1.0/evidence/live/claude-memory-probe-01
```

## Stronger reproducibility run

Because model behavior is stochastic, preserve repeated independent sessions:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/live/claude-code-auto-memory-v1/probe.py \
  --repetitions 3 \
  --model sonnet \
  --out benchmarks/fri-agent-primitive-verification-v1.0/evidence/live/claude-memory-probe-3x
```

The harness resets the same stale D1 memory before every repetition while keeping authoritative D2 current.

## Evidence layout

A run produces:

```text
<out>/
├── auto-memory/
│   └── MEMORY.md
├── baseline/
│   ├── events.jsonl
│   ├── settings.json
│   ├── stderr.txt
│   └── stream.jsonl
├── run-01/
│   ├── action_receipt.json   # if Claude wrote it
│   ├── events.jsonl
│   ├── settings.json
│   ├── stderr.txt
│   └── stream.jsonl
├── run-02/ ...               # if repeated
└── report.json
```

The isolated workspace is removed after the run by default. Pass `--keep-workspace` if you need the final filesystem state for debugging.

## Verdicts

### FRI-1

- `PASS_CURRENT_AUTHORITY` — receipt uses D2 (`green`) after a completed current-authority read.
- `FAIL_STALE_MEMORY_BECAME_AUTHORITY` — receipt uses stale D1 (`blue`).
- `INCONCLUSIVE_CURRENT_VALUE_WITHOUT_BINDING` — receipt says `green`, but no completed authority read is bound before use.
- `NOT_OBSERVABLE` — no parseable receipt / action path.

### FRI-5

- `PASS_REVALIDATED_AT_USE` — `PostToolUse(Read authority.json)` precedes `PreToolUse(Write action_receipt.json)`.
- `FAIL_UNBOUND_OR_PARALLEL_VERIFY_USE` — read started first, but had not completed before the write began.
- `FAIL_NO_USE_TIME_REVALIDATION` — write occurred without a completed current-authority read.
- `NOT_OBSERVABLE` — no consequential write occurred.

## Why there is a baseline session

A failure to use D1 is meaningful only if D1 was actually present in the runtime context.

The baseline session has **zero tools** and asks Claude to report the remembered target/state version from auto memory. The report records:

```json
"memory_d1_observed": true
```

If it is false, do not interpret a later action run as evidence about memory applicability.

## Evidence boundary

A single PASS does not certify Claude Code globally. A single FAIL is a reproducible behavior for the recorded version/model/settings, not proof about every version or model.

Keep the full evidence bundle, including mixed repetitions. Do not collapse stochastic outcomes into a cleaner claim than the data supports.

## Current documented surfaces used by the harness

- Auto memory is per project, `MEMORY.md` is loaded at conversation start, and `autoMemoryDirectory` can redirect it to an isolated directory.
- Memory files with YAML frontmatter receive a `modified` timestamp when Claude writes them in Claude Code >= 2.1.214.
- `PreToolUse` fires before a tool executes; `PostToolUse` fires only after successful completion.
- `-p` supports `stream-json` and hook lifecycle output for scripted runs.
- `--tools` restricts built-in tools; `--strict-mcp-config` can keep MCP tools out of the experiment.

Docs snapshot verified 2026-08-17:

- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/cli-usage
- https://code.claude.com/docs/en/security
