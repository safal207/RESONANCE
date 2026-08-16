# Public Contract Study 001 — Crossmint Agent Payments Under Ambiguous Commit

**Status:** public-contract analysis + bounded vendor clarification  
**Date:** 2026-08-12; updated 2026-08-15  
**System:** Crossmint agent wallets / wallet transactions / x402  
**Testing:** none performed  
**Relationship:** independent research; no affiliation or endorsement implied

## Question

When an AI agent is authorized to move money and a network failure makes the result of a payment request uncertain, what can an external integrator prove from Crossmint's public contract before deciding whether to retry?

This study is deliberately narrower than a security review. It examines documented recovery primitives, a bounded clarification from Crossmint support, and the evidence boundary visible to a public integrator.

## Result after vendor clarification

Crossmint support confirmed the core reading of the public surface while preserving an important boundary:

- the primitives are documented;
- Crossmint does **not** publish a complete normative precedence rule for the timeout case;
- same-key replay after a timeout is the documented idempotent discovery mechanism for an already-created transaction;
- transaction lookup is the canonical/system-of-record state surface and exposes status plus `onChain.txId` / explorer material;
- terminal transaction states are `success` and `failed`;
- webhooks are at-least-once notifications and must be deduplicated, so webhook delivery is not the canonical record;
- `onChain.txId` is null until broadcast, so chain state is useful for confirmation/settlement evidence and weak for discovery before broadcast.

Crossmint support also made the epistemic boundary explicit: composing those guarantees into

```text
same-key replay
→ transaction lookup until terminal
→ webhook as trigger
→ onChain.txId from terminal record as settlement evidence
```

is a reasonable integration inference, **not a separate provider guarantee that can be cited as normative policy**.

That changes the study from a single `UNRESOLVED` bucket into two distinct conclusions:

```text
NORMATIVE TIMEOUT PRECEDENCE        = UNRESOLVED / NOT PUBLISHED
OPERATIONAL RECOVERY COMPOSITION    = SUPPORTED INFERENCE
```

## Public contract observed

Crossmint's public documentation exposes several primitives relevant to safe financial recovery:

1. **Scoped agent authority.** Stablecoin-wallet delegation can constrain spend amount, allowed counterparties and time window. Card permissions likewise use scoped spending rules.
2. **Idempotent transaction creation.** `POST /wallets/{walletLocator}/transactions` accepts `x-idempotency-key`, documented as preventing duplicate transaction creation; same-key replay can return the existing transaction after an ambiguous create timeout.
3. **Explicit lifecycle state.** Wallet transaction status is exposed as `awaiting-approval`, `pending`, `failed`, or `success`.
4. **Canonical reconciliation.** `GET /wallets/{walletLocator}/transactions/{transactionId}` returns the current transaction state and on-chain identifiers when available.
5. **History reconciliation.** Wallet transaction history can be listed for the wallet.
6. **Asynchronous notification.** Webhooks are at-least-once and require webhook-id deduplication; they are treated as notification/trigger evidence rather than canonical state.
7. **Settlement evidence.** `onChain.txId` appears only after broadcast, making it useful for confirmation and poor for pre-broadcast discovery.
8. **x402 settlement evidence.** The documented x402 flow handles the initial `402 Payment Required`, attaches payment proof on retry, and exposes settlement receipt material after a successful response.

## Failure-path model

```text
logical payment intent
    ↓
create with idempotency identity K
    ↓
response observed? ──────────────────┐
    ↓ yes                             │ no / timeout
transaction id/state                  │
    ↓                                 ↓
lookup state                    SAME-KEY REPLAY
    ↓                                 ↓
pending / success / failed      discover existing transaction
    ↓                                 ↓
terminal evidence ←──────────── canonical lookup
    ↓
settlement / failure disposition
    ↓
separate continuation authorization
```

The important distinction is between **repeating the same logical operation for discovery** and **creating a new financial operation**.

## Recovery invariant

A safe client should preserve a stable logical-operation identity across ambiguous transport failures and should not create a new spend merely because the original HTTP response was lost.

```text
if outcome is uncertain:
    preserve logical operation identity
    reuse the same idempotency identity for discovery where documented
    reconcile canonical durable state
    treat webhook delivery as a trigger, not the source of truth
    require terminal evidence
    require separate authority before any new monetary operation
```

The first four steps are grounded in documented primitives and the bounded vendor clarification. The complete ordered composition remains an integrator-side inference rather than a published normative Crossmint timeout policy.

## Evidence provenance

The study now keeps three evidence classes separate:

```text
DOCUMENTED PUBLIC GUARANTEE
        ↓
BOUNDED VENDOR CLARIFICATION
        ↓
DERIVED INTEGRATION COMPOSITION
```

The third layer must never be upgraded into the first merely because it composes cleanly.

## What is now resolved

The following earlier questions are materially narrowed:

- **Same-key replay after timeout:** documented as the way to discover the existing transaction rather than create a duplicate.
- **Canonical transaction state:** transaction lookup is the system-of-record surface.
- **Webhook role:** notification/trigger evidence, not canonical state; delivery is at-least-once and requires deduplication.
- **On-chain role:** confirmation/settlement evidence after broadcast, not reliable discovery before broadcast.

## What remains unresolved

These remain open public-contract questions, not defect claims:

1. What is the documented retention/lifetime of a transaction idempotency key?
2. If the same idempotency key is replayed with materially different transaction parameters, what behavior is guaranteed?
3. Crossmint does not publish a complete normative precedence rule for the timeout-recovery case; should such a rule be made explicit for autonomous agents?
4. After a canonical terminal `failed` transaction, what public contract explicitly authorizes creation of a new financial operation, if any?
5. In the x402 flow, what recovery behavior is recommended when payment may have settled but the post-payment HTTP response is lost?
6. Is there a documented stable logical-operation identifier spanning creation, transaction record, webhook event and on-chain settlement, or should integrators construct that lineage themselves?

## Derived continuation gate

The clarified evidence supports a fail-closed continuation invariant:

```text
if canonical payment state is nonterminal or unknown:
    block new monetary action
    reconcile

if canonical payment state is success:
    stop the same logical operation

if canonical payment state is failed:
    do not infer retry authority
    require a separate documented/local authorization rule
```

This is the Crossmint instance of the provider-neutral **Ambiguous Financial State Protocol (AFSP)** now modeled in ContractGraph-QA.

## Bounded verification plan

If Crossmint explicitly authorizes staging testing, the smallest useful experiment would avoid adversarial load and real funds:

```text
create one staging transaction with idempotency key K
→ interrupt/withhold the client response at controlled points
→ replay K
→ reconcile by GET / history / webhook
→ verify exactly one logical financial transition
→ preserve complete evidence
```

A second case would retry `K` with changed parameters to document conflict semantics.

No such test has been performed as part of this report.

## Sources reviewed

- Crossmint Docs — Agents / How Agents Pay: https://docs.crossmint.com/agents/how-agents-pay
- Crossmint Docs — Wallets / Create Transaction: https://docs.crossmint.com/api-reference/wallets/create-transaction
- Crossmint Docs — Wallets / Get Transaction: https://docs.crossmint.com/api-reference/wallets/get-transaction
- Crossmint Docs — Wallets / Get Wallet Transactions: https://docs.crossmint.com/api-reference/wallets/get-transactions
- Crossmint Docs — Webhooks / Best Practices: https://docs.crossmint.com/introduction/platform/webhooks/best-practices
- Crossmint Docs — Wallets / Transfer Webhooks: https://docs.crossmint.com/wallets/guides/webhooks
- Crossmint Docs — Agents / x402: https://docs.crossmint.com/agents/payment-flows/x402
- Bounded Crossmint support clarification received 2026-08-14; summarized without internal workflow or failure data.

## Boundary

This report does not claim a vulnerability, does not infer private architecture, does not test production systems, and does not represent Crossmint or its staff as endorsing RESONANCE. The support clarification is treated as bounded external evidence, not as permission to publish internal information and not as a substitute for normative public documentation.
