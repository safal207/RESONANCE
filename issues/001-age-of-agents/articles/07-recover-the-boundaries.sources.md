# Sources — Article 07: Recover the Boundaries

**Article ID:** I001-RN-RLC  
**Last verified:** 2026-08-15  
**Purpose:** Preserve source identity, claim classification, verification boundaries, and explicit non-claims for Article 07.

---

## S1 — OpenAI Codex issue #29356

**Type:** Primary public issue / user-reported product behavior  
**Repository:** `openai/codex`  
**Issue:** `#29356` — *Context compaction loses operational continuity in long Codex tasks; preserve the last 5 operational steps verbatim*  
**URL:** https://github.com/openai/codex/issues/29356

Supports:

- the existence of a public context-compaction continuity issue;
- the distinction between compressed historical summary and a recent operational tail;
- reported user impact around forgotten corrections, rejected approaches, touched files, and verification targets.

Does **not** independently prove frequency, root cause, or affected population across all Codex users.

---

## S2 — averriK reproducible macOS case

**Type:** Primary public issue comment / reported reproduction  
**Comment ID:** `5080913510`  
**URL:** https://github.com/openai/codex/issues/29356#issuecomment-5080913510

Reported environment included:

- Codex Desktop on macOS;
- bundled `codex-cli 0.145.0-alpha.18`;
- model `gpt-5.6-sol`, reasoning effort `ultra`;
- local project/worktree workflow;
- explicit durable recovery contract.

Reported post-compaction behavior included:

- conflation of two separate responsibility lanes;
- overengineered continuation despite a simple architecture ruling;
- reappearance of fallback-like behavior contrary to recent user correction;
- partial checks described as approaching completion while end-to-end artifact still failed;
- delayed acknowledgement of the compaction event.

This source is the direct trigger for the Responsibility-Lane Continuity failure model.

Classification boundary:

> Verified that the report exists and says this. The report is not independently reproduced by RESONANCE inside Codex Desktop.

---

## S3 — Nightshift continuity comment

**Type:** Primary public issue comment / practitioner report  
**Author:** `orwa-mahmoud`  
**Comment ID:** `5298091869`  
**URL:** https://github.com/openai/codex/issues/29356#issuecomment-5298091869

Supports the distinction between:

- external durable project state for punch lists, decisions, progress, next actions and verification requirements; and
- native compaction behavior needed to preserve subtle recent conversational corrections.

The linked Nightshift project is the author's implementation and is not treated as independent validation of RLC-001.

---

## S4 — RESONANCE / pythiaLabs Verifiable Continuation Envelope

**Type:** First-party engineering artifact  
**Repository:** `safal207/pythiaLabs`  
**RFC:** `standards/agent-continuity/RFC-001-VERIFIABLE-CONTINUATION-ENVELOPE.md`  
**Prior reviewed merge:** `pythiaLabs#208`

Canonical principle:

> Preserve continuity without inventing history, and restore information without silently restoring authority.

Supports the pre-existing split between:

- operational tail;
- durable artifact/evidence references;
- authority classes;
- restore requirements/results;
- fail-closed continuation.

RLC-001 is additive to this contract.

---

## S5 — RLC-001 draft implementation

**Type:** First-party executable engineering artifact  
**Repository:** `safal207/pythiaLabs`  
**PR:** `#258` — *Add responsibility-lane continuity gate for agent recovery*  
**URL:** https://github.com/safal207/pythiaLabs/pull/258

Head used for Article 07 verification:

```text
259fb3213e4c5862f3e406e6b126293dc6ca717f
```

RLC-001 adds:

- `responsibility_lanes`;
- owner references;
- lane objectives;
- allow/deny mutation scope;
- lane-specific done conditions;
- latest ruling references;
- durable source references;
- event-to-lane bindings;
- lane-scoped next action;
- source-revalidation results;
- conflict handling;
- lane and extension digests.

Status boundary:

> Draft PR / research contract. Not a Codex native implementation and not a production authorization claim.

---

## S6 — RLC-001 specification

**Type:** First-party specification  
**Path:** `standards/agent-continuity/extensions/RLC-001-RESPONSIBILITY-LANE-CONTINUITY.md`  
**Branch:** `agent/responsibility-lane-continuity`

Core invariant:

> A continuation is not valid merely because state was recovered. Ownership and mutation boundaries must also be recovered and revalidated before mutation.

Normative invariant families include:

- material event lane attribution;
- mutation-scope preservation;
- source-based ownership recovery;
- latest-ruling preservation;
- fail-closed lane conflation;
- fail-closed contradictory sources;
- revalidation of all live lanes;
- tamper-evident digests.

---

## S7 — Rejected lane-conflation fixture

**Type:** First-party negative conformance fixture  
**Path:** `standards/agent-continuity/extensions/fixtures/rlc-rejected-lane-conflation.json`

Fixture structure:

```text
spec-authoring lane
  allowed: artifact-rfc, artifact-schema

verification lane
  allowed: capability:verify
  denied: artifact-rfc, artifact-schema

negative binding
  artifact-rfc + artifact-schema mutation
  rebound to verification lane
```

Expected decision:

```text
BLOCKED
```

Supports Article 07 claim that the described lane-conflation failure class has been converted into a machine-checkable rejection case.

---

## S8 — Reference conformance suite

**Type:** First-party executable tests  
**Path:** `standards/agent-continuity/extensions/conformance/test_rlc_conformance.py`

At Article 07 verification time:

```text
21 / 21 tests PASS locally
```

The suite checks positive and negative cases including:

- schema validation;
- lane identity;
- lane/extension digest integrity;
- active lane existence;
- next-action scope;
- material event lane binding;
- cross-lane effect rejection;
- missing source checks;
- digest mismatch;
- pending/failed/conflict restore outcomes;
- tampering;
- unknown dependencies;
- allow/deny overlap.

---

## S9 — GitHub Actions conformance run

**Type:** First-party CI execution evidence  
**Repository:** `safal207/pythiaLabs`  
**Run:** `31861074959`  
**URL:** https://github.com/safal207/pythiaLabs/actions/runs/31861074959

Observed result on PR #258 head:

```text
VCE conformance suite — success
Responsibility-lane continuity suite — success
```

Same head also had:

```text
Security — success
CI — success
```

This proves the reference suites executed successfully in GitHub Actions at the cited head. It does not prove production safety or vendor adoption.

---

## S10 — AutoGen Mission Keeper discussion

**Type:** External public design discussion  
**Repository:** `microsoft/autogen`  
**Issue:** `#7487`

Relevant design convergence:

- verifier should be structurally unable to execute the transition it verifies;
- pre-action verdict and observed outcome should remain separate;
- verifier vantage and stake should be auditable;
- read-only/no-tool-route separation makes independence mechanical rather than declarative.

Article 07 uses this only as a related architectural analogy:

> If separation of powers is structural before compaction, recovery must not silently erase that separation afterwards.

No claim is made that AutoGen has adopted RLC-001.

---

## Claim classification rules used by Article 07

### Verified repository fact

Directly inspectable in a cited repository, PR, fixture, commit, schema, workflow or run.

### Public reported case

A public author reports observed behavior. RESONANCE verifies the report's existence and exact scope, not the underlying product root cause unless independently reproduced.

### Design inference

A conclusion derived from multiple artifacts or reports. Marked as an architectural interpretation rather than vendor fact.

### Scope limitation

Explicit boundary preventing research/prototype evidence from being promoted to production or vendor-adoption claims.

---

## Explicit non-claims

Article 07 does **not** claim:

- OpenAI has accepted, endorsed or implemented RLC-001;
- `openai/codex#29356` is caused by one confirmed internal root cause;
- every context-compaction failure is a responsibility-topology failure;
- the public macOS reproduction has been independently recreated by RESONANCE;
- pythiaLabs PR #258 is production-ready;
- passing 21 conformance tests proves universal agent continuity safety;
- project-local state is sufficient without native recent-tail preservation;
- responsibility lanes remove the need for task-specific verification or authorization.

---

## Evidence chain

```text
public continuity issue
        ↓
reported durable-recovery failure
        ↓
responsibility-lane conflation hypothesis
        ↓
RLC-001 machine-readable contract
        ↓
accepted fixture
        ↓
rejected lane-conflation fixture
        ↓
reference validator
        ↓
21-test conformance suite
        ↓
GitHub Actions success
        ↓
RESONANCE Article 07
```

The journal preserves this chain as evidence and interpretation. Publication does not convert it into execution authority or vendor truth.
