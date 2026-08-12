# Public Contract Study 001 — Crossmint Agent Payments Under Ambiguous Commit

**Status:** public-contract analysis only  
**Date:** 2026-08-12  
**System:** Crossmint agent wallets / wallet transactions / x402  
**Testing:** none performed  
**Relationship:** independent research; no affiliation or endorsement implied

## Question

When an AI agent is authorized to move money and a network failure makes the result of a payment request uncertain, what can an external integrator prove from Crossmint's public contract before deciding whether to retry?

This study is deliberately narrower than a security review. It examines documented recovery primitives and the evidence boundary visible to a public integrator.

## Public contract observed

Crossmint's public documentation exposes several primitives relevant to safe financial recovery:

1. **Scoped agent authority.** Stablecoin-wallet delegation can constrain spend amount, allowed counterparties and time window. Card permissions likewise use scoped spending rules.
2. **Idempotent transaction creation.** `POST /wallets/{walletLocator}/transactions` accepts `x-idempotency-key`, documented as preventing duplicate transaction creation.
3. **Explicit lifecycle state.** Wallet transaction status is exposed as `awaiting-approval`, `pending`, `failed`, or `success`.
4. **Direct reconciliation.** `GET /wallets/{walletLocator}/transactions/{transactionId}` returns the current transaction state and details.
5. **History reconciliation.** Wallet transaction history can be listed for the wallet.
6. **Asynchronous evidence.** Wallet transfer webhooks report outgoing transfer success or failure; successful API-originated transfers can expose a `transferId` usable with the Get Transaction API.
7. **x402 settlement evidence.** The documented x402 flow automatically handles the initial `402 Payment Required`, attaches payment proof on retry, and exposes a settlement receipt from response headers after a successful response.

## Failure-path model

```text
logical payment intent
    ↓
request created
    ↓
transaction accepted? ───────────────┐
    ↓                                │
response observed                    │ response lost / timeout
    ↓                                │
awaiting-approval / pending           │
    ↓                                │
onchain success / failure            │
    ↓                                │
receipt / webhook / status            │
                                     ↓
                              AMBIGUOUS COMMIT
                                     ↓
                              reconcile first
                                     ↓
                         retry only if evidence allows
```

The important distinction is between **repeating the same logical operation** and **creating a new financial operation**.

## Recovery invariant

A safe client should preserve a stable logical-operation identity across retries and should not create a new spend merely because the original HTTP response was lost.

A conservative recovery rule is:

```text
if outcome is uncertain:
    do not widen authority
    do not create a new logical payment
    reconcile durable state
    reuse the same idempotency identity where applicable
    require evidence before proceeding
```

This is an integrator-side inference from the documented primitives, not a claim about Crossmint's internal implementation.

## Evidence hierarchy available publicly

For wallet transactions, the public contract exposes multiple potentially useful evidence surfaces:

```text
request + idempotency identity
        ↓
transaction id
        ↓
GET transaction state / transaction history
        ↓
webhook transfer outcome
        ↓
onchain identifiers / finality
```

The public docs make those surfaces available, but the pages reviewed do not define a complete normative precedence rule for every ambiguous network-failure case.

## What the reviewed public contract establishes

- transaction creation has an idempotency-key mechanism;
- transaction state is durable enough to be queried by transaction ID;
- pending and final states are distinguished;
- outgoing transfer webhooks distinguish success from failure;
- successful outgoing API transfers can be linked back to transaction retrieval via `transferId`;
- x402 exposes settlement receipt material after a successful paid response.

## What remains unresolved from the reviewed public pages

The following are **open public-contract questions**, not defect claims:

1. What is the documented retention/lifetime of a transaction idempotency key?
2. If the same idempotency key is retried with materially different transaction parameters, what behavior is guaranteed?
3. After a timeout where the client never received a transaction ID, is same-key replay the canonical first reconciliation mechanism, or is another lookup path preferred?
4. What public evidence should take precedence if API state, webhook timing and onchain observation are temporarily out of sync?
5. In the x402 flow, what recovery behavior is recommended when payment may have settled but the post-payment HTTP response is lost?
6. Is there a documented stable logical-operation identifier that spans request creation, transaction record, webhook event and onchain settlement, or should integrators construct that lineage themselves?

## Bounded verification plan

If Crossmint explicitly authorizes staging testing, the smallest useful experiment would avoid adversarial load and real funds:

```text
create one staging transaction with idempotency key K
→ interrupt/withhold the client response at controlled points
→ retry with K
→ reconcile by transaction list / GET / webhook
→ verify exactly one logical financial transition
→ preserve complete evidence
```

A second case would retry `K` with changed parameters to document the public conflict semantics.

No such test has been performed as part of this report.

## Market question

> For an integrator using only Crossmint's public wallet APIs, after a timeout on transaction creation with an idempotency key, which public evidence path should be treated as canonical before any further financial action: same-key replay, transaction lookup/history, webhook outcome, onchain state, or a defined precedence among them?

A precise answer would convert an implicit recovery assumption into an explicit integration invariant.

## Sources reviewed

- Crossmint Docs — Agents / How Agents Pay: https://docs.crossmint.com/agents/how-agents-pay
- Crossmint Docs — Wallets / Create Transaction: https://docs.crossmint.com/api-reference/wallets/create-transaction
- Crossmint Docs — Wallets / Get Transaction: https://docs.crossmint.com/api-reference/wallets/get-transaction
- Crossmint Docs — Wallets / Get Wallet Transactions: https://docs.crossmint.com/api-reference/wallets/get-transactions
- Crossmint Docs — Wallets / Transfer Webhooks: https://docs.crossmint.com/wallets/guides/webhooks
- Crossmint Docs — Agents / x402: https://docs.crossmint.com/agents/payment-flows/x402

## Boundary

This report uses public documentation only. It does not claim a vulnerability, does not infer private architecture, does not test production systems, and does not represent Crossmint or its staff as endorsing RESONANCE.