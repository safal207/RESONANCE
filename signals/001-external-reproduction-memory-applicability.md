# Engineering Signal 001 — External Reproduction of Memory Applicability

**Status:** externally reproduced / interoperability loop active  
**Verified:** 11 Aug 2026  
**Scope:** open-source engineering signal  
**Not:** an Anthropic endorsement, product commitment, or official Anthropic implementation

## Signal

A second public agent-memory implementation has consumed the frozen CML Current-State Applicability fixture verbatim and implemented the same six-outcome applicability contract.

The important event is not praise or discussion. It is a transition from one implementation to two inspectable implementations sharing the same executable fixture.

## Claim classification

### Verified fact

The CML fixture at:

- `safal207/Causal-Memory-Layer/tests/fixtures/memory_applicability_v0.1.json`

and the vendored Inspeximus fixture at:

- `DanceNitra/inspeximus/tests/fixtures/cml_memory_applicability_v0.1.json`

have the same Git blob SHA:

`ec27aad145c6051e22e993a4ef30e57a9063af48`

This verifies byte-for-byte fixture identity at the Git object level.

The Inspeximus conformance test explicitly:

- loads that frozen fixture;
- requires at least 15 cases;
- checks that all six applicability outcomes are exercised;
- runs each case against `evaluate_applicability()`;
- asserts `expected_status`;
- asserts declared `expected_reasons`.

### Direct participant report

DanceNitra reported in `anthropics/claude-code#34556` that the second implementation agrees on **15/15** frozen cases and that declared reasons are asserted too.

RESONANCE treats the 15/15 count as a direct statement from the implementation author. The fixture identity and public conformance harness are independently inspectable in the repositories above.

### Verified CML-side transition

The external discussion then produced a new lineage/supersession failure case: a derived memory can still match its own source while one upstream dependency has been superseded, retired, erased or changed.

CML turned that case into PR #272 and merged it to `main` as commit:

`0c27e1918c27e5223fe8343df0aac77b2db5ccdb`

The merged transition passed post-merge CI, Python Package Validation and Security Baseline on that exact `main` SHA.

## Causal trajectory

```text
CML proposal
→ frozen fixture
→ external implementation attempts compatibility
→ missing REVALIDATE capability exposed
→ second implementation adopts the contract
→ 15/15 agreement reported
→ shared measurement language improves
→ external lineage/supersession failure case
→ CML executable lineage contract
→ PR #272 merged + post-merge checks green
→ next: second lineage reproduction
```

This is the signal RESONANCE cares about: an idea entered another implementation, produced disagreement, changed both systems, and returned as a new executable test surface.

## Why it matters

A specification with one implementation can still be an internal convention. A frozen fixture consumed by a second implementation creates a stronger interoperability object because disagreement becomes observable.

The contract now separates:

```text
retrieval reliability
→ source integrity
→ lineage / supersession
→ current-state applicability
→ authority
→ action
→ evidence
```

The key invariant remains:

> Historical truth is not automatically current authority.

## Uncertainty

- DanceNitra is an external open-source contributor participating in a public Anthropic repository discussion; this is **not** an Anthropic endorsement.
- The 15/15 result is currently attributed to the implementation author's direct report plus a public conformance harness; RESONANCE has verified fixture identity and test structure, not independently re-executed Inspeximus locally.
- The new lineage fixture has not yet been reproduced by the second implementation.

## Next verification gate

The next transition is intentionally falsifiable:

```text
CML memory_lineage_v0.1.json
→ vendor byte-for-byte
→ second implementation
→ compare expected_status
→ compare expected_reasons
→ compare exclusion accounting
→ freeze agreement OR disagreement
```

Until that happens, lineage interoperability remains **pending**.

## Primary / inspectable references

1. Anthropic Claude Code issue #34556 — public memory discussion and DanceNitra reports: https://github.com/anthropics/claude-code/issues/34556
2. Inspeximus conformance test: https://github.com/DanceNitra/inspeximus/blob/e7c030e0efa50e2f3fe1f15865fb56648de12f8e/tests/test_cml_memory_applicability_contract.py
3. Inspeximus vendored frozen fixture: https://github.com/DanceNitra/inspeximus/blob/e7c030e0efa50e2f3fe1f15865fb56648de12f8e/tests/fixtures/cml_memory_applicability_v0.1.json
4. CML frozen fixture: https://github.com/safal207/Causal-Memory-Layer/blob/0c27e1918c27e5223fe8343df0aac77b2db5ccdb/tests/fixtures/memory_applicability_v0.1.json
5. CML Current-State Applicability PR #270: https://github.com/safal207/Causal-Memory-Layer/pull/270
6. CML lineage/supersession PR #272: https://github.com/safal207/Causal-Memory-Layer/pull/272
7. Frozen lineage fixture: https://github.com/safal207/Causal-Memory-Layer/blob/0c27e1918c27e5223fe8343df0aac77b2db5ccdb/tests/fixtures/memory_lineage_v0.1.json

---

**RESONANCE classification:** Verified Engineering Signal with one explicitly attributed participant-reported metric (15/15) and a pending next reproduction gate.
