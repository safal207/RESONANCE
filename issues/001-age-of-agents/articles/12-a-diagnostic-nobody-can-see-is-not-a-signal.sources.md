# Sources & Evidence Map — Article 12

**Article:** [A Diagnostic Nobody Can See Is Not a Signal](./12-a-diagnostic-nobody-can-see-is-not-a-signal.md)  
**Article ID:** `I001-RN-DNS`  
**Date:** 2026-08-15

## Evidence classes

This companion separates public upstream observations, executable implementation evidence, RESONANCE inference, and explicit non-claims.

---

## 1. Public upstream observations

### Claude Code issue #24798

Thread:

https://github.com/anthropics/claude-code/issues/24798

### Ownership-epoch separation acknowledged

`deemwario` stated that the ownership-epoch tier supplied a missing distinction between:

```text
who may write?
```

and:

```text
is this transition based on the expected predecessor?
```

Comment:

https://github.com/anthropics/claude-code/issues/24798#issuecomment-5300586147

**Evidence class:** public participant statement / architectural interpretation.

### Independent log check: asymmetric result

`csitte` reported checking two proposed failure modes against their own logs.

Reported observations included:

- #2 did not reproduce as the proposed concurrency-race class in that environment;
- 372 status-setting messages were inspected;
- 13 transitions had authors that had not seen the preceding transition;
- three were attributed to a typed-timestamp bug;
- of the remaining ten, only one had a seconds-range gap and both writes came from the same session during its own test;
- the other nine were separated by minutes to a day and were characterized as writers not reading the thread to the end;
- #1 did reproduce: one handoff targeted a session that was not running and had no watcher;
- a watcher inventory diagnostic existed, but the documents senders used did not tell them that reachability was checkable.

Comment:

https://github.com/anthropics/claude-code/issues/24798#issuecomment-5301156153

**Evidence class:** public self-report about one participant's logs. RESONANCE has not independently audited the underlying private logs.

### Follow-up on honest non-reproduction

`deemwario` explicitly treated the #2 non-reproduction as useful evidence for narrowing where to investigate rather than as a reason to discard the distinction.

Comment:

https://github.com/anthropics/claude-code/issues/24798#issuecomment-5301327363

**Evidence class:** public participant interpretation.

---

## 2. Executable implementation evidence

### HRC-001 — Handoff Reachability & Causal Basis

Repository:

https://github.com/safal207/pythiaLabs

Draft PR:

https://github.com/safal207/pythiaLabs/pull/262

Exact head:

```text
f38d45a67430c393f040702b1c1c360dbf3b9343
```

Canonical HRC conformance run:

```text
31876678326
```

https://github.com/safal207/pythiaLabs/actions/runs/31876678326

Result:

```text
SUCCESS
```

Reference suite size:

```text
24 tests
```

The executable contract distinguishes, among other states:

```text
BLOCKED_UNREAD_PREDECESSOR
BLOCKED_CAS_CONFLICT
PENDING_REACHABILITY_UNCHECKED
BLOCKED_REACHABILITY_NOT_SURFACED
PENDING_UNREACHABLE
HANDOFF_DELIVERABLE
PENDING_RECIPIENT_ACK
HANDOFF_COMMIT_ALLOWED
```

**Evidence class:** public implementation report + GitHub-hosted executable conformance evidence.

---

## 3. RESONANCE design inferences

The following are design conclusions drawn from the public observations and the executable reference model; they are not claims that Claude Code implements these contracts.

### Inference A

> Ownership does not imply reachability.

### Inference B

> Unread predecessor and CAS conflict are separate failure classes.

### Inference C

> Detectability without discoverability is not operational observability.

### Inference D

> A fact outside the decision path cannot protect the decision.

### Inference E

> A handoff should separate deliverability from commitment when recipient reachability and acknowledgement matter.

---

## 4. Explicit non-claims

Article 12 does **not** claim:

- that `csitte`'s private logs were independently audited by RESONANCE;
- that the reported frequencies generalize to Claude Code users or multi-agent systems broadly;
- that CAS races are absent;
- that CAS races are universal;
- that a watcher process is the only valid reachability primitive;
- that a READY reachability signal guarantees successful delivery;
- that recipient acknowledgement guarantees task completion;
- that a claimed `observed_through_event_id` proves a real read unless backed by a trusted observation mechanism;
- that HRC-001 is adopted by Anthropic or Claude Code;
- that HRC-001 provides distributed transactional atomicity or formal global safety/liveness.

---

## 5. Reader falsification

Live poll:

https://github.com/safal207/RESONANCE/issues/60

A reproducible counterexample or contrary trace is stronger evidence than aggregate agreement.
