# HRC-001 Executable Evidence — Handoff Reachability & Causal Basis

**Parent article:** [A Diagnostic Nobody Can See Is Not a Signal](./12-a-diagnostic-nobody-can-see-is-not-a-signal.md)  
**Protocol:** HRC-001 — Handoff Reachability & Causal Basis  
**Implementation repository:** `safal207/pythiaLabs`  
**Draft PR:** `#262`  
**Exact head:** `f38d45a67430c393f040702b1c1c360dbf3b9343`  
**Canonical CI run:** `31876678326`  
**Result:** **SUCCESS**  
**Date:** 2026-08-15

---

## Executable distinction

The public coordination discussion produced two different classes of stale transition:

```text
writer did not read the predecessor
```

and:

```text
writer read the predecessor, then the head advanced
```

HRC-001 makes them separately observable:

```text
observed_through_event_id != expected_predecessor_id
→ BLOCKED_UNREAD_PREDECESSOR
```

versus:

```text
observed_through_event_id == expected_predecessor_id
expected_predecessor_id != current_head_event_id
→ BLOCKED_CAS_CONFLICT
```

This is the central falsifiable distinction.

---

## Handoff boundary

The reference also refuses to equate an ownership assignment with a completed handoff.

```text
A proposes handoff to B
        ↓
current surfaced reachability(B)
        ↓
HANDOFF_DELIVERABLE
        ↓
B acknowledges exact handoff event + target epoch + predecessor
        ↓
HANDOFF_COMMIT_ALLOWED
```

Without a reachability signal:

```text
PENDING_REACHABILITY_UNCHECKED
```

With a stale or unavailable recipient:

```text
PENDING_UNREACHABLE
```

With a diagnostic signal from a different surface than the one bound into the sender's protocol path:

```text
BLOCKED_REACHABILITY_NOT_SURFACED
```

Thus the executable model represents:

> A diagnostic that exists internally but is absent from the sender's decision path is not an operational signal.

---

## Conformance evidence

Canonical exact-head run:

```text
workflow: HRC conformance
run:      31876678326
event:    pull_request
head:     f38d45a67430c393f040702b1c1c360dbf3b9343
result:   success
```

GitHub Actions:

https://github.com/safal207/pythiaLabs/actions/runs/31876678326

Draft PR:

https://github.com/safal207/pythiaLabs/pull/262

The suite contains **24 tests** covering:

- current owner transition;
- wrong writer;
- stale ownership epoch;
- unread predecessor;
- true CAS conflict;
- lane mismatch;
- missing reachability;
- wrong participant reachability;
- unsurfaced diagnostic;
- future reachability;
- expired reachability;
- known unavailable recipient;
- deliverable handoff;
- target ownership epoch increment;
- missing recipient ACK;
- wrong recipient ACK;
- wrong handoff occurrence ACK;
- wrong target epoch ACK;
- stale predecessor at acknowledgement;
- exact acknowledged handoff commit;
- state schema validation;
- status/handoff proposal schema validation;
- reachability enum rejection;
- acknowledgement binding schema rejection.

---

## Evidence boundary

This proof demonstrates behavior of the bounded reference contract only.

It does not prove:

- the private upstream logs independently;
- population frequency of either failure class;
- that a declared observation cursor corresponds to a real read unless the runtime provides trusted observation evidence;
- successful transport after a READY signal;
- task completion after acknowledgement;
- distributed transaction atomicity;
- Anthropic/Claude Code adoption.

The #2 non-reproduction in the motivating public report remains a preserved negative observation, not something HRC-001 rewrites into a confirmed production race.

---

## Reader falsification

Poll:

https://github.com/safal207/RESONANCE/issues/60

A trace that shows one of these distinctions is unnecessary, harmful, or incorrectly modeled is stronger evidence than an Agree vote.
