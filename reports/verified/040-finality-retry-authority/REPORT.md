# Verified Report #040 — Finality ≠ Retry Authority

**Date:** 2026-08-12  
**Status:** Verified market-driven model correction  
**Source implementation:** `safal207/ContractGraph-QA`  
**Source merge commit:** `24ca237ba01d98e8bb2150f51db5309bd403ecb9`  
**Provider profile:** `payram-payout-public` / Provider Adapter Contract v0.3

## Signal

Agent-payment recovery needs two separate proofs:

1. **What happened to the previous financial operation?**
2. **Is the agent authorized to create another financial effect now?**

Those are related, but they are not the same claim.

A provider can expose a final-looking failure state while its public contract does not establish that a new payout is safe. Treating every final `failed` state as automatic retry permission silently collapses reconciliation into authority.

## Model correction

The earlier recovery model could derive:

```text
reconciliation = FINAL / failed
⇒ retryAllowed = true
```

The PayRam public-contract mapping exposed why that implication is too strong.

Provider Adapter Contract v0.3 now separates the two dimensions:

```text
reconciliation finality
        ≠
retry authority
```

The new fail-closed representation is:

```text
reconciliation = FINAL / failed
retrySemanticsStatus = unresolved
retryAllowedAfterProviderStates = []

⇒ retryAllowed = false
⇒ retryBlockReason = retry_semantics_unresolved
```

The benchmark can therefore know that the previous attempt reached a provider-final state while still refusing to authorize another monetary action.

## PayRam public-contract evidence used

The merged public profile records only what was established from PayRam's reviewed public payout/API/SDK documentation:

- Create Payout returns a withdrawal `id` used for follow-up status checks;
- a dedicated payout-status lookup exposes provider states;
- the public state machine includes approval, broadcast and terminal-looking outcomes;
- `processed` is mapped to `committed` because its public description includes on-chain confirmation and accounting recording;
- `sent` remains `pending` in the adapter;
- `failed`, `rejected`, and `cancelled` normalize to `failed` as provider outcomes;
- Create Payout idempotency / same-request replay was not established in the reviewed public contract;
- the public contract did not establish which failure states authorize a safe new payout.

The adapter therefore records:

```text
retrySemanticsStatus = unresolved
retryAllowedAfterProviderStates = []
```

This is not a statement that a retry is unsafe. It is a statement that **retry authority was not proven by the reviewed public contract**.

## Why this matters for autonomous agents

For a human operator, an undocumented retry boundary may become a support question or manual review step.

For an autonomous financial agent, an undocumented boundary can become a second monetary action.

The safer causal rule is:

```text
FINALITY(previous operation)
+
AUTHORITY(next operation)
=
permission to continue
```

not:

```text
FAILED(previous operation)
=
permission to retry
```

This distinction is especially important when the agent can act faster than a human can inspect ledger, webhook, API, or settlement evidence.

## Evolution of the standard

The provider-adapter line is now being corrected by independent market surfaces:

```text
Provider Adapter v0.1
  ↓
Crossmint public contract
  ↓
v0.2 — evidence precedence may be UNRESOLVED
  ↓
PayRam public contract
  ↓
v0.3 — retry authority may be UNRESOLVED
```

Crossmint exposed uncertainty about **which evidence wins**.

PayRam exposed uncertainty about **whether a reconciled failure grants authority to act again**.

These are separate coordinates and now remain separate in the executable model.

## Evidence boundary

This report verifies the merged ContractGraph-QA model change and the public-contract profile that motivated it.

It does **not** claim that PayRam is vulnerable, unsafe, non-compliant, or endorsed by RESONANCE. No PayRam production API or payment system was tested for this report.

The profile is a conservative interpretation of reviewed public documentation. Any future provider clarification can narrow `UNRESOLVED` without rewriting the vendor-neutral recovery invariant.

## RESONANCE conclusion

A payment agent should not ask only:

> Do I know how the previous operation ended?

It must also ask:

> What evidence gives me authority to create the next financial effect?

**Finality is evidence about the past. Retry authority is permission for the future.**
