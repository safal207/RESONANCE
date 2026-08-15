# Engineering Signal 017 — Authority Causality / Current Owner Gate

**Status:** VERIFIED — 2026-08-15  
**Lineage:** Article 07 Responsibility-Lane Continuity → Article 08 Authority Has a History → ACI-001  
**Executable contract:** `safal207/pythiaLabs` PR #259, merged as `17df87775c0d5407c07e86f278455d912ed51305`  
**Authority:** operational memory / routing guidance only; this signal grants no production mutation, deployment, financial, credential, merge, or external-action authority

## Signal

A multi-agent system can know the current state and still be forbidden to mutate it.

The missing proof is not knowledge. It is current causal authority.

> **Authority itself has causal state.**

For any consequential mutation whose ownership may change dynamically, the system should be able to establish both:

```text
current state predecessor
AND
current authority predecessor
```

The compact admission rule is:

```text
CAS(state) ∧ CAS(authority)
→ mutation admissible
```

Failure of either proof blocks mutation.

## Why this signal exists

Public discussion in `anthropics/claude-code#24798` exposed a useful boundary. `deemwario` described `ownership-per-key`: make it structurally impossible for two loops to hold write authority over the same key.

That is the cheapest valid case when the key space can be partitioned statically.

The boundary appears when ownership depends on runtime state, work-stealing, failover, delegation, recovery, or revocation. Then authority itself needs a predecessor and a versioned handoff.

This produces a coordination ladder:

```text
static ownership
      ↓
CAS ownership transfer
      ↓
causal-CAS shared state
```

Use the cheapest mode that actually matches the contention model.

## Canonical executable evidence

ACI-001 is canonical in `pythiaLabs/main` after PR #259.

```text
repository  safal207/pythiaLabs
PR          #259
merge       17df87775c0d5407c07e86f278455d912ed51305
```

GitHub Actions proof on the PR head:

```text
ACI conformance  SUCCESS — 16/16
VCE conformance  SUCCESS
Security         SUCCESS
CI               SUCCESS
```

ACI run:

`31863547583`

The executable contract includes:

- per-resource `authority_epoch`;
- tamper-evident authority-state digest;
- explicit `assign`, `transfer`, `delegate`, `revoke`, `expire` transitions;
- exact predecessor digest and epoch checks;
- mutation request bound to owner, scope, authority digest and epoch;
- independent state-predecessor checks;
- split-authority detection;
- stale-writer rejection after ownership handoff.

## Current-owner gate

Before a consequential mutation, an agent should not ask only:

> Is my local state current?

It must also ask:

> Am I still the current authorized owner for this resource and scope?

Minimum gate:

```text
presented owner
presented authority_epoch
presented authority_digest
requested scope
        ↓
resolve canonical current AuthorityState
        ↓
owner matches?
epoch matches?
digest matches?
scope permits effect?
status active?
        ↓
YES → authority side eligible
NO  → BLOCKED
```

Only then should the state-predecessor check decide whether the proposed transition is still based on current state.

## Stale writer rule

Canonical negative shape:

```text
A owns X @ epoch 17
        ↓
A reads current state
        ↓
X transferred to B @ epoch 18
        ↓
A finishes a semantically correct computation
        ↓
A attempts mutation with epoch 17
        ↓
BLOCKED
```

This yields the operational invariant:

> **Correct knowledge does not imply current authority.**

A stale owner must not regain authority merely because it has fresh data, a correct patch, a durable checkpoint, or a resumed session.

## Revocation dominates memory

Recovery artifacts are evidence of prior state, not automatic restoration of write authority.

```text
checkpoint: A owns X @ 17
current authority source: B owns X @ 18
```

Result:

```text
current authority wins
A remains blocked
```

This is especially important after:

- context compaction;
- process restart;
- delayed retry;
- agent failover;
- work-stealing;
- delegation expiry;
- incident-response leader rotation.

The recovery rule is:

> **A durable memory of authority is not authority unless it still matches the current causal authority state.**

## Responsibility lane ≠ active authority instance

Article 07 / RLC answers:

```text
Which responsibility lane owns this class of action?
```

ACI answers:

```text
Which actor or instance currently holds that lane's mutation authority, and by what causal predecessor?
```

These are separate proofs.

A stable lane may survive while its active holder changes:

```text
verification lane
  verifier A @ 8
       ↓ handoff
  verifier B @ 9
```

Therefore a resumed `verifier A` cannot rely on lane membership alone.

## Split-authority rule

For one resource and one authority epoch, competing active owners are not resolved by timestamp or last-write-wins.

```text
X @ epoch 22 → owner A ACTIVE
X @ epoch 22 → owner B ACTIVE
```

must become:

```text
CONFLICT
→ fail closed
→ reconcile authority history
```

not:

```text
latest timestamp wins
```

Timestamp order is not a substitute for a valid authority predecessor.

## Working taxonomy additions

Signal 017 adds these internal working names:

30. **State-Freshness / Authority-Freshness Conflation** — current data is treated as current write permission;
31. **Checkpoint / Authority Resurrection** — stale recovered ownership silently regains mutation authority after restart or compaction;
32. **Lane-Identity / Active-Owner Conflation** — responsibility-lane membership is treated as proof that a specific actor still owns the lane;
33. **Timestamp / Authority-Predecessor Conflation** — last-write or latest timestamp is used to resolve an authority conflict without a causal handoff;
34. **Split-Authority Acceptance** — two active owners exist for the same resource/epoch and the system continues instead of failing closed;
35. **Authority-CAS / State-CAS Conflation** — one successful predecessor check is treated as sufficient when the action requires both.

These names are working engineering taxonomy, not an external standard.

## Agent routing rule

When a task includes dynamic ownership, delegation, work-stealing, failover, revocation, leases, delayed retries, or resumed agents, route through the authority gate before material mutation.

```text
recover objective
    ↓
recover responsibility lane
    ↓
resolve current AuthorityState
    ↓
verify authority predecessor
    ↓
verify state predecessor when required
    ↓
perform bounded mutation
    ↓
record resulting state + authority evidence
```

Do not invent a second authority mechanism if ACI-001 already expresses the needed invariant. Extend the contract only when a falsifiable case is not representable by the current model.

## Scope boundary

ACI-001 is a research / engineering contract. It does not by itself prove:

- production distributed consensus;
- Byzantine fault tolerance;
- linearizability across arbitrary distributed stores;
- secure identity provisioning;
- lease safety under unbounded clock skew;
- vendor adoption by Anthropic, OpenAI, or another platform;
- production deployment authorization.

The verified claim is narrower: the published reference contract and conformance suite mechanically distinguish current authority from stale authority and independently compose authority-currentness with state-currentness.

## Core rule

```text
state current
≠
authority current
```

and, where both are required:

```text
state predecessor valid
AND
authority predecessor valid
→ action causally admissible
```

---

Signal 017 is operational memory and routing guidance. Native contracts and exact execution evidence remain the verification layer; authorization remains separate.