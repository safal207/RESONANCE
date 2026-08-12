# Verified Report #038 — Crossmint Public Recovery Contract → UNRESOLVED

**Date:** 2026-08-12  
**Status:** Verified market → model evolution  
**Source implementation:** `safal207/ContractGraph-QA`  
**Provider Adapter v0.1 merge:** `c04ad1a07c6500c1210b57d7df29161072da74b6`  
**Crossmint-driven v0.2 merge:** `593d4a864b517fa210798ea5daf538e53d09ae19`

## Signal

RESONANCE Verified Report #034 established a vendor-neutral recovery invariant for agent payments:

```text
AMBIGUOUS(payment A)
  ⇒
NO NEW FINANCIAL ACTION
  UNTIL
RECONCILED(payment A)
```

The next engineering step was to make provider-specific reconciliation semantics declarative instead of hard-coding them into the benchmark.

That produced Provider Adapter Contract v0.1.

The first attempt to map a real public provider contract — Crossmint wallet transactions — exposed a useful limitation in the adapter model itself.

## What the public contract supported

The Crossmint public-contract profile records documented surfaces for:

- create-transaction idempotency via `x-idempotency-key`;
- transaction states including `awaiting-approval`, `pending`, `success` / `succeeded`, and `failed`;
- GET transaction status;
- wallet transfer webhook observations.

The resulting profile is checked into ContractGraph-QA at:

`benchmarks/agent-payment-recovery-v0.1/provider-adapters/crossmint-public-contract.v0.1.json`

## What remained unresolved

In the reviewed public documentation, the model did **not** find enough published contract information to safely manufacture:

1. a canonical precedence between GET transaction evidence and transfer-webhook evidence;
2. a documented same-key replay recovery procedure after an ambiguous Create Transaction timeout.

This is an evidence-boundary statement, not a claim that such internal semantics do not exist.

The important modeling decision was therefore:

```json
{
  "evidencePrecedenceStatus": "unresolved",
  "evidencePrecedence": []
}
```

and:

```json
{
  "sameKeyReplayDocumented": false
}
```

## Model correction

Provider Adapter v0.1 implicitly assumed that every real provider profile could supply a complete evidence precedence.

Crossmint showed that this assumption was too strong.

Instead of filling the missing ordering with an analyst guess, ContractGraph-QA evolved the adapter contract so that **unknown provider semantics can remain first-class and fail-closed**.

The corrected path is:

```text
public provider contract
→ documented observations
→ missing canonical precedence
→ UNRESOLVED
→ no fabricated ordering
→ retry remains blocked where reconciliation authority is insufficient
```

## Why this matters

This is the first concrete example of the market changing the verification standard rather than merely being evaluated by it.

The loop is now:

```text
market surface
→ formal model
→ model mismatch
→ explicit uncertainty
→ contract evolution
→ stronger benchmark
```

That matters because independent verification becomes weaker, not stronger, when undocumented semantics are silently converted into assumptions.

A useful adapter must be able to say:

> The public contract does not currently give us enough authority to resolve this transition.

That is a result, not a failure of the analysis.

## Evidence chain

```text
RESONANCE Verified Report #034
Agent Payment Recovery Benchmark v0.1
        ↓
ContractGraph-QA PR #29
Provider Adapter Contract v0.1
merge c04ad1a...
        ↓
Crossmint public-contract mapping
        ↓
precedence could not be justified from reviewed public docs
        ↓
ContractGraph-QA PR #30
Provider Adapter v0.2 + UNRESOLVED semantics
merge 593d4a8...
```

## Boundary

No Crossmint production system was tested for this report.

No claim is made that Crossmint is vulnerable, unsafe, non-compliant, or incorrectly implemented. The report records a limitation of what could be established from the reviewed public contract and the resulting improvement to our own verification model.

The Crossmint profile itself preserves the source documentation references used for the mapping.

## RESONANCE conclusion

A verification standard should not force certainty where the source contract does not provide it.

The important transition is therefore not:

```text
unknown → guessed precedence
```

but:

```text
unknown → explicit UNRESOLVED → fail closed → ask for discriminating evidence
```

Crossmint became the first real provider surface to drive that correction into the Agent Payment Recovery standard.
