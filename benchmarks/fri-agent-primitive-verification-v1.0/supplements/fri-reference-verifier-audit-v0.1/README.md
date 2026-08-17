# FRI Reference Verifier Integrity Audit v0.1

This supplement applies the harness-integrity rules back to the FRI reference evaluator itself.

It exists to prevent a green FRI-1…FRI-6 run from being treated as meaningful if the evaluator can also pass on missing evidence, collapse distinct failure causes, or fail to distinguish the negative fixture from its positive control.

## Audit shape

Each FRI rule gets paired controls:

```text
negative path
+
positive contrast
+
missing/insufficient evidence path where relevant
+
discriminating boundary cases where two semantics could otherwise agree accidentally
```

The audit therefore checks more than the six canonical negative fixtures.

## Findings before hardening

The self-audit exposed four real weaknesses in the original reference evaluator:

1. **FRI-2 vacuous health** — `instrumented_reads=0` and `observation_records=0` returned `HEALTHY`, even though liveness was not observable.
2. **FRI-5 vacuous allow** — missing `verified_state_version` and missing `current_state_version` compared equal (`None == None`) and could return `ALLOW`.
3. **FRI-3 cause collapse** — no delivery and stale ownership both collapsed into `BLOCK_STALE_OWNER`.
4. **FRI-6 cause collapse** — no recovered state and a true lane mismatch both collapsed into `BLOCK_LANE_MISMATCH`.

The hardened evaluator now distinguishes these states explicitly.

## New fail-closed verdicts

```text
FRI-1
NO_PERSISTED_MEMORY

FRI-2
NOT_OBSERVABLE

FRI-3
BLOCK_NO_DELIVERY
BLOCK_AUTHORITY_UNPROVEN

FRI-4
BLOCK_DEPENDENCY_NOT_COMPLETE

FRI-5
BLOCK_MISSING_VERIFICATION_EVIDENCE

FRI-6
BLOCK_NO_RECOVERED_STATE
BLOCK_LANE_UNPROVEN
```

The original FRI-1…FRI-6 canonical fixture verdicts are unchanged.

## Manual semantic mutation matrix

`run_mutation_control.py` keeps one mandatory, human-selected semantic mutant per FRI rule. These mutants model known-dangerous mistakes such as ignoring supersession, ignoring ownership epoch, allowing a completion receipt to override a non-complete dependency label, or treating missing versions as equal authorization evidence.

The gate requires:

```text
FRI-1 … FRI-6 covered
mutation_score = 1.0
```

This is a bounded semantic adequacy check, not a claim of complete mutation coverage.

## Automatic boundary mutation campaign

`run_boundary_mutation_campaign.py` discovers comparison and guard sites inside `evaluate()` and generates single-site mutants automatically.

Generated families in v0.1:

- comparison boundary flips: `== ↔ !=`, `< ↔ <=`, `> ↔ >=`, `is ↔ is not`, `in ↔ not in`;
- guard bypass: replace a non-dispatch guard with `False`;
- guard negation: negate a non-dispatch guard.

Rule-dispatch comparisons such as `rule == "collector_liveness"` are deliberately excluded so trivial routing failures do not inflate the score.

The automatic campaign is fail-closed in CI with `--required-score 1.0`. If any generated mutant survives, the FRI verifier-integrity job fails and the surviving site is emitted in machine-readable evidence.

Order-inversion mutations are intentionally not part of this gate yet because adjacent guards can be semantically equivalent; they need an equivalence-aware policy before they can support a meaningful required score.

## Run

Reference self-audit:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/run_audit.py
```

Manual semantic mutation matrix:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/run_mutation_control.py
```

Automatic boundary campaign:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/run_boundary_mutation_campaign.py \
  --required-score 1.0
```

## Current established result

Reference self-audit: **22/22 PASS**.

Manual semantic mutation matrix: **6/6 KILLED**, with complete FRI-1…FRI-6 rule coverage.

The automatic campaign result is produced by the FRI verifier-integrity CI artifact and must be read from the exact run that evaluated the current head; this README does not freeze a live-generated mutant count.

These results concern the deterministic reference evaluator and its test harness. They remain separate from any product-runtime certification.
