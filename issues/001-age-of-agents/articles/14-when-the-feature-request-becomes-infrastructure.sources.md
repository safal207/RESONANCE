# Sources — Article 14: When the Feature Request Becomes Infrastructure

**Article ID:** I001-RN-FRI  
**Article:** [`14-when-the-feature-request-becomes-infrastructure.md`](14-when-the-feature-request-becomes-infrastructure.md)  
**Last verified:** 2026-08-17  
**Scope:** Public evidence for the three Claude Code discussion closures and the native primitives cited in Article 14.

---

## Evidence boundary

Article 14 makes a deliberately bounded claim.

It **does not claim** that Anthropic implemented these capabilities because of the cited community discussions.

The public evidence supports only the following:

1. the discussions existed and described missing or incomplete product surfaces;
2. `bcherny` later pointed to native Claude Code primitives addressing substantial parts of those surfaces;
3. the corresponding issues were closed as `completed` on 2026-08-17;
4. therefore the observable product baseline had moved, regardless of implementation causality.

The article's research conclusion is about the **verification frontier after primitive emergence**, not attribution of product causality.

---

## 1. Persistent memory across compactions — `anthropics/claude-code#34556`

### Final maintainer response

Boris Cherny (`bcherny`) wrote that Claude Code now has built-in auto memory that does much of what the discussion had built externally: a per-project memory directory, a short always-loaded index file, topic files loaded on demand, and notes that survive compaction and new sessions.

He closed the issue because the persistence layer exists and invited specific remaining gaps as separate issues.

- Issue: https://github.com/anthropics/claude-code/issues/34556
- Maintainer comment: https://github.com/anthropics/claude-code/issues/34556#issuecomment-5311260238
- Auto memory docs: https://code.claude.com/docs/en/memory#auto-memory

### What this supports

```text
native persistent project memory exists
        ↓
compaction/session continuity is now a product primitive
```

### What this does not establish

It does not establish:

- source integrity;
- observation binding;
- lineage/supersession correctness;
- current-state applicability;
- use-time freshness;
- action authority derived from memory.

Those remain separate verification questions.

---

## 2. Compact/session lifecycle hooks — `anthropics/claude-code#47023`

### Final maintainer response

Boris Cherny (`bcherny`) wrote that all four lifecycle events discussed in the proposal exist today:

- `PreCompact` — before manual or automatic compaction; receives session identity/transcript context and may block compaction;
- `PostCompact` — after compaction with the generated compact summary;
- `SessionEnd` — on exit with a reason field;
- `SessionStart` — on startup/resume/fork and able to return `additionalContext`.

The issue was then closed as completed.

- Issue: https://github.com/anthropics/claude-code/issues/47023
- Maintainer comment: https://github.com/anthropics/claude-code/issues/47023#issuecomment-5311193029
- Hooks docs: https://code.claude.com/docs/en/hooks
- Claude Code changelog: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

### What this supports

```text
lifecycle boundaries are exposed as native extension seams
```

### What this does not establish

A hook API does not itself prove:

- the collector actually ran;
- the intended state was observed;
- a silent fail-open was detected;
- the callback output remained attributable after restart;
- historical callback output still has current authority.

This is the basis for the Article 14 liveness boundary:

> A lifecycle seam is not a guarantee until the collector using it has an independently testable liveness condition.

---

## 3. Inter-session messaging and coordination — `anthropics/claude-code#24798`

### Final maintainer response

Boris Cherny (`bcherny`) wrote that much of the requested capability had shipped. As of Claude Code `v2.1.224`, sessions can discover other live sessions through `ListAgents`, deliver messages through `SendMessage`, and address a session by `@`-mention. For coordinated work with a shared task list, dependencies and delegation, he pointed to agent teams.

The issue was closed as completed.

- Issue: https://github.com/anthropics/claude-code/issues/24798
- Maintainer comment: https://github.com/anthropics/claude-code/issues/24798#issuecomment-5311328527
- Cross-session messaging docs: https://code.claude.com/docs/en/cross-session-messaging
- Agent teams docs: https://code.claude.com/docs/en/agent-teams
- Claude Code changelog: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

### What this supports

```text
session discovery
        +
message transport
        +
team task/dependency/delegation primitives
```

are now native surfaces rather than purely external workarounds.

### What this does not establish

```text
message delivered != authority transferred
session reachable != responsibility lane valid
task marked done != completion evidence bound
```

Native messaging simplifies transport. It does not by itself define causal authority, exactly-once handoff, predecessor visibility, or evidence-bound dependency admission.

---

## Cross-source observation

The three closures form an observable product-level sequence:

```text
persistent memory
        ↓
lifecycle extension seams
        ↓
cross-session coordination
```

Article 14 treats this as a **baseline shift**, not as evidence of who caused the shift.

The resulting research frontier is:

```text
Can it remember?
        → Is the memory applicable now?

Can the hook run?
        → Can we prove the collector was alive and observed the right state?

Can sessions communicate?
        → Can we prove the handoff carried current authority and causal predecessor state?

Can tasks depend on each other?
        → Can the dependent transition cite the exact completion evidence that admits it?
```

This is the bridge from product capability to verification infrastructure.

---

## Related RESONANCE articles

- [`07-recover-the-boundaries.md`](07-recover-the-boundaries.md) — recovered information vs recovered responsibility topology.
- [`08-authority-has-a-history.md`](08-authority-has-a-history.md) — current knowledge vs current mutation authority.
- [`12-a-diagnostic-nobody-can-see-is-not-a-signal.md`](12-a-diagnostic-nobody-can-see-is-not-a-signal.md) — reachability, causal read basis and diagnostics in the decision path.
- [`13-evidence-must-bind-the-transition.md`](13-evidence-must-bind-the-transition.md) — exact evidence occurrence must bind the consequential transition it authorizes, validates or settles.

---

## Editorial rule carried forward

> **When a missing primitive ships, the trust frontier moves one layer up.**

And the companion operational rule:

> **Yesterday's workaround can become tomorrow's falsification harness.**
