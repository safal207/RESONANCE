# Article 08 Sources — Authority Has a History

**Article ID:** I001-RN-ACI  
**Article:** [`08-authority-has-a-history.md`](08-authority-has-a-history.md)  
**Last verified:** 2026-08-15

---

## Evidence policy

This file separates:

- public reported observations;
- verified repository facts;
- executable conformance results;
- design inference;
- explicit non-claims.

The article does **not** claim that Anthropic, OpenAI or another vendor has adopted ACI-001.

---

## S1 — Claude Code inter-session coordination thread

**Source:** `anthropics/claude-code#24798`  
**Type:** Public GitHub issue / discussion

Canonical issue:

https://github.com/anthropics/claude-code/issues/24798

The thread contains multiple reports and architecture proposals around cross-session messaging, shared state, append-only event logs, delivery semantics, session identity, ownership and coordination.

Use of the thread in Article 08 is limited to public statements visible in the issue.

---

## S2 — `deemwario`: ownership-per-key as a special case of causal CAS

**Source comment:**

https://github.com/anthropics/claude-code/issues/24798#issuecomment-5300376905

**Classification:** Public reported implementation/design observation

The comment states that their system used ownership-per-key so two loops could not hold write authority over the same key. The author explicitly characterizes this as cheaper than general causal CAS and notes the boundary: static partitioning works while ownership can be assigned ahead of time, but dynamic work-stealing or runtime-dependent ownership returns the system to a general compare-and-swap problem.

### What this supports

- static ownership can structurally eliminate some write races;
- static partitioning has a workload boundary;
- dynamic ownership requires additional coordination.

### What this does not independently prove

- that ACI-001 is the only valid solution;
- that all dynamic ownership requires the exact `authority_epoch` representation used in the prototype;
- any vendor defect.

---

## S3 — ACI-001 executable prototype

**Repository:** `safal207/pythiaLabs`  
**Pull request:** #259

https://github.com/safal207/pythiaLabs/pull/259

**Classification:** Verified repository fact

The PR introduces:

```text
standards/agent-continuity/authority-causality/
├── ACI-001-AUTHORITY-CAUSALITY-INVARIANT.md
├── schema/
│   ├── authority-state.schema.json
│   ├── authority-transition.schema.json
│   └── mutation-request.schema.json
├── conformance/
│   ├── aci_reference.py
│   ├── test_aci_conformance.py
│   └── requirements.txt
└── fixtures/
    ├── accepted-static-owner.json
    ├── accepted-authority-transfer.json
    └── rejected-authority-cases.json
```

The PR remains a research/prototype artifact unless separately merged/promoted.

---

## S4 — ACI conformance workflow

**GitHub Actions run:** `31863547583`

https://github.com/safal207/pythiaLabs/actions/runs/31863547583

**Classification:** Verified CI result

Observed result on 2026-08-15:

```text
ACI conformance
status: completed
conclusion: success

Ran 16 tests
OK
```

The suite includes positive and negative cases for:

- static ownership;
- authority digest tamper detection;
- valid authority transfer;
- predecessor-digest mismatch;
- stale authority epoch;
- invalid epoch increment;
- stale writer after handoff;
- current owner after handoff;
- wrong actor;
- effect outside authority scope;
- revoked authority;
- split authority;
- combined authority + state CAS;
- stale state with current authority;
- stale authority with current state.

---

## S5 — Concrete stale-writer model

**Fixture:** `rejected-authority-cases.json`

The reference case models:

```text
previous:
  worker:A owns key:X @ epoch 17

handoff:
  worker:B owns key:X @ epoch 18

late mutation:
  actor = worker:A
  presented_authority_epoch = 17
```

The validator returns:

```text
BLOCKED
```

A corresponding mutation from `worker:B` carrying epoch 18 and the current authority digest is:

```text
ADMISSIBLE
```

### Supported claim

In the reference model, current state knowledge does not compensate for stale authority.

### Non-claim

This fixture is not a benchmark of production distributed consensus performance.

---

## S6 — Split-authority model

The rejected fixture also models:

```text
key:X
├── worker:A @ epoch 7 ACTIVE
└── worker:B @ epoch 7 ACTIVE
```

The reference implementation marks this as a split-authority conflict.

This supports Article 08's recommendation to fail closed rather than choose a winner using timestamp order alone.

---

## S7 — Relation to Article 07 / Responsibility-Lane Continuity

**Article 07:**

https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/07-recover-the-boundaries.md

Article 07 distinguishes recovered operational state from recovered responsibility topology after compaction/recovery.

Article 08 adds a separate layer:

```text
responsibility topology recovered
        ≠
authority necessarily current
```

This is an editorial/design composition, not a claim that the two protocols have been vendor-integrated.

---

## Claim map

| Claim | Primary evidence | Strength |
|---|---|---|
| Ownership-per-key was used to avoid competing writers | S2 | Public report |
| Static ownership has a boundary under dynamic work-stealing | S2 | Public report / design boundary |
| Authority can be represented with causal predecessor + epoch | S3 | Implemented prototype |
| Stale writer after handoff is mechanically rejected | S4 + S5 | Verified reference result |
| Authority and state predecessor checks are independent | S4 | Verified reference result |
| Split authority can be made a fail-closed condition | S4 + S6 | Verified reference result |
| This architecture generalizes to every distributed system | None | **Not claimed** |
| Claude Code implements ACI | None | **Not claimed** |
| OpenAI/Codex implements ACI | None | **Not claimed** |

---

## Explicit non-claims

Article 08 and ACI-001 do not claim:

- production Byzantine fault tolerance;
- globally linearizable ownership;
- correctness under arbitrary network partitions;
- cryptographic actor authentication;
- production lease semantics;
- vendor-native adoption;
- formal proof of safety/liveness;
- complete delegation hierarchy semantics;
- universal superiority over locks, leases, consensus, transactional databases or actor models.

The narrow demonstrated result is:

> A reference contract can make authority predecessor, epoch, scope and owner first-class, and can mechanically reject stale/split authority independently from state freshness.

---

## Reproduction

From the PR branch, the reference suite is intended to run with:

```bash
python -m pip install -r standards/agent-continuity/authority-causality/conformance/requirements.txt
python -m unittest discover \
  -s standards/agent-continuity/authority-causality/conformance \
  -p 'test_*.py' \
  -v
```

The GitHub Actions run in S4 is the canonical remote execution cited by the article.
