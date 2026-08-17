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

## Run

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/run_audit.py
```

Write evidence:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/run_audit.py \
  --output benchmarks/fri-agent-primitive-verification-v1.0/supplements/fri-reference-verifier-audit-v0.1/evidence/reference-run.json
```

## Result

Reference audit: **20/20 PASS** after hardening.

This means only that the deterministic reference evaluator now distinguishes the declared contrast and missing-evidence paths. It remains separate from any product-runtime certification.
