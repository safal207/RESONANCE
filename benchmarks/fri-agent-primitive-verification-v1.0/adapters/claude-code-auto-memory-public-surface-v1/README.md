# Claude Code Auto-Memory Public-Surface Adapter v1

This adapter maps the FRI reference semantics from RESONANCE Article 14 onto the **publicly documented** Claude Code auto-memory surface.

It currently evaluates two scenarios:

- **FRI-1 — Memory persisted, source superseded**
- **FRI-5 — Valid verification, stale at use**

## Result on 2026-08-17

```text
FRI-1 → NOT_OBSERVABLE
FRI-5 → NOT_OBSERVABLE
```

This is deliberately **not** a FAIL verdict.

`NOT_OBSERVABLE` means the public contract does not expose enough machine-readable state to prove the invariant from the documented native surface alone.

## What is documented

Claude Code auto memory provides:

- per-project memory storage;
- persistence across sessions;
- an always-loaded `MEMORY.md` index;
- topic files read on demand;
- a `modified` timestamp for memory files with YAML frontmatter when Claude writes them;
- generic hooks, including `PreToolUse`, that can block consequential tool calls.

## What FRI-1 still needs

To distinguish historical persistence from current applicability, the adapter looks for:

```text
memory_ref
source_locator / source_identity
supersedes relation or lineage
current applicability / authority verdict
```

The public auto-memory contract documents persistence and a modification-time hint, but not the other three fields.

A file-level `modified` timestamp is useful, but it cannot prove that a claim inside the file remains true, has not been superseded, or is currently authorized to drive an action.

## What FRI-5 still needs

For VERIFY → USE, the adapter looks for:

```text
verification_witness
verified state/version/digest
use-time revalidation result
```

Claude Code documents a generic `PreToolUse` blocking seam, which is enough to host an **external** verifier. The documented auto-memory surface does not itself expose a memory-specific witness or state binding that the hook can consume without additional instrumentation.

So the current shape is:

```text
native auto memory
      ↓
persistent recalled prose + modified hint
      ↓
[missing machine-readable applicability / witness]
      ↓
generic PreToolUse extension point
```

## Why this is not a duplicate stale-memory claim

Open Claude Code issues already report stale-memory symptoms, including:

- `anthropics/claude-code#85075` — old `MEMORY.md` silently loading into sessions;
- `anthropics/claude-code#75405` — a readiness claim made from stale memory without verifying artifacts.

The second thread also contains field evidence that age is a weak proxy: memories can be recently written and already false, while old memories can remain true.

FRI adds two narrower contracts:

```text
persistence != current applicability
verification at N != authority to act at N+1
```

## Run

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/adapters/claude-code-auto-memory-public-surface-v1/run_adapter.py
```

To write evidence:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/adapters/claude-code-auto-memory-public-surface-v1/run_adapter.py \
  --output benchmarks/fri-agent-primitive-verification-v1.0/adapters/claude-code-auto-memory-public-surface-v1/evidence/public-surface.json
```

## Evidence boundary

This adapter evaluates **public contract observability**, not live Claude Code runtime conformance.

A live adapter must execute against an installed Claude Code runtime and record actual memory writes, recalls, source changes and action-admission decisions before it can return `PASS` or `FAIL` for product behavior.

Core rule:

> **NOT_OBSERVABLE is a request for a stronger measurement surface, not an accusation of a runtime violation.**
