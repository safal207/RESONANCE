# FRI Harness Integrity Supplement v0.1

This supplement checks the **trustworthiness of the conformance harness itself**. It does not add new FRI product invariants and does not change FRI-1…FRI-6.

It was added after a field report in the closed Claude Code persistence discussion exposed four distinct ways a verifier can look green while failing to prove what it claims.

Source discussion (reference only):

- https://github.com/anthropics/claude-code/issues/34556#issuecomment-5313171595

The source author explicitly disclosed a commercial interest in agent-memory tooling. The controls below are therefore adopted because they are independently falsifiable patterns, not because of vendor authority.

## Run

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/harness-integrity-v0.1/run_harness_integrity.py
```

Write evidence:

```bash
python benchmarks/fri-agent-primitive-verification-v1.0/supplements/harness-integrity-v0.1/run_harness_integrity.py \
  --output benchmarks/fri-agent-primitive-verification-v1.0/supplements/harness-integrity-v0.1/evidence/reference-run.json
```

## Controls

### HGI-1 — Vacuous pass / antecedent never reached

```text
writes attempted
→ every write refused
→ assertions report PASS anyway
```

Expected: `REJECT_VACUOUS_PASS`

Invariant:

> **assertion passed != tested state was reached**

A negative-control harness should be able to sabotage the antecedent and require the probe to fail.

### HGI-2 — Covered antecedent, non-discriminating fixture

```text
field A = 1
field B = 1
for every fixture
```

A mutant that swaps A and B can survive because the fixtures never force the meanings apart.

Expected: `REJECT_NON_DISCRIMINATING_FIXTURE`

Invariant:

> **antecedent reached != evidence discriminates**

This does **not** require every fixture to kill an arbitrary mutant. The narrow requirement is that fields whose semantics can be confused must have at least one fixture where the competing interpretations produce different observable values.

### HGI-3 — Declared contract, stale live-impact measurement

```text
identifier policy measured at population generation N
store grows to generation N+1
cached impact reused
```

Expected: `REMEASURE_REQUIRED`

Invariant:

> **declared contract != current impact of that contract**

The policy may remain unchanged while its collision/truncation/fold cost changes with the live population. Prefer an executable pre-flight that re-measures over a frozen number in documentation.

### HGI-4 — Side effect committed, acknowledgement failed

```text
write commits
→ rendering/acknowledgement fails
→ process exits non-zero
→ caller retries without reconciliation
```

Expected: `RECONCILE_BEFORE_RETRY`

Invariant:

> **command failed != side effect did not happen**

Before retrying a consequential operation after an ambiguous failure, reconcile whether the logical effect already committed.

## Harness model

A trustworthy conformance case should make four questions independently visible:

```text
REACHABLE      — did the test enter the state it claims to test?
DISCRIMINATING — can the fixture distinguish plausible wrong semantics?
ASSERTED       — does the oracle reject the wrong result?
CURRENT        — is evidence about mutable/live state re-measured when needed?
```

For consequential writes, add a fifth boundary:

```text
EFFECT         — what state transition actually committed, independent of acknowledgement?
```

## Evidence boundary

A green run proves only that this deterministic reference evaluator detects the four declared malformed situations. It does not prove that every product adapter or every FRI fixture is automatically free of vacuity, non-discrimination, stale measurement, or ambiguous-effect bugs.

The supplement is intended as a verifier-of-the-verifier layer for future conformance work.
