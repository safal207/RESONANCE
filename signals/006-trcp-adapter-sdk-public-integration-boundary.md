# Engineering Signal 006 — TRCP Adapter SDK Public Integration Boundary

**Status:** verified project milestone  
**Verified:** 13 Aug 2026  
**Scope:** public integration boundary for deterministic external-workload evidence binding  
**System:** `safal207/LiminalOSAI` TRCP Adapter SDK v0.1  
**Not:** proof of independent execution, production isolation, live-provider safety, or financial-system correctness

## Signal

TRCP crossed a boundary from an internal research pipeline to a public integration surface that external consumer code can use without importing replay-core internals.

The new integration chain is:

```text
external adapter
    ↓
public TRCP SDK
    ↓
normalized workload
    ↓
bound evidence
    ↓
independent binding verification
    ↓
deterministic receipt
```

Consumer code imports only:

`from sdk.liminal_trcp.sdk import ...`

A minimal external adapter needs only a stable `consumer_type` and `normalize()` implementation. Task construction, provider fixtures, evidence assembly and replay-core details remain behind the SDK boundary.

## Immutable implementation point

TRCP Adapter SDK v0.1 landed in `LiminalOSAI/main` through PR #188.

Feature commit:

`f3d1001b30f2bca4212a26c5987328b3eb02d757`

Merge commit:

`1c0e70cd12c7784bbf9b615c39ab1fb58b31c703`

Public API:

`sdk.liminal_trcp.sdk`

Reference integration:

`examples/trcp_external_consumer_reference/`

Five-minute guide:

`docs/TRCP_ADAPTER_SDK.md`

## Verified project checks

The merged SDK milestone reported:

- **21/21** focused Adapter SDK tests passing;
- **200/200** full TRCP regression tests passing;
- reference order-system consumer producing binding `PASS`;
- reference runs with execution replay `NOT_RUN` and `PASS` modes;
- identical workload, bundle and receipt hashes across those modes;
- TRCP/Core/Governance and related CI workflows passing on the reviewed head;
- no open review threads before merge.

These are project-local regression results. They are not external certification percentages.

## Semantic boundary

The important architectural result is not merely that another example passed.

TRCP now distinguishes two different claims:

### Binding verification

Confirms that the normalized workload, task/provider references, evidence bundle and deterministic receipt remain cryptographically and causally bound under the defined local protocol.

### Execution replay

Optionally asks consumer-owned code to execute the workload again and compare the result.

Execution replay is deliberately reported separately. A binding `PASS` does **not** mean the external business system was independently re-executed.

That separation prevents the receipt from claiming more than the verifier actually observed.

## Why this matters

Before this milestone, proving a new consumer path still required knowledge of internal TRCP construction details.

After this milestone, the product-facing contract becomes:

```text
consumer-specific code
      ↓ normalize()
stable public SDK boundary
      ↓
provider-neutral evidence contract
      ↓
deterministic verification receipt
```

This is the first reusable integration surface in the TRCP line: protocol → benchmark → generic external consumer → public SDK.

## What this proves

Within the defined LOCAL_ONLY / SYNTHETIC_ONLY scope, a third-party-style stateful consumer can enter the TRCP evidence pipeline through a small public adapter interface without consumer-specific logic in the core verifier.

The result is a deterministic binding receipt whose identity remains separate from optional execution replay status.

## What this does not prove

This milestone does not show that:

- a remote or production system was independently re-executed;
- adapter code is sandboxed or trusted;
- a live provider or wallet is safe;
- the external producer cannot coherently recompute a false but internally consistent evidence chain;
- the protocol is an external security certification.

Those are separate layers.

## Market question

For an AI agent that can move money, approve payouts, reserve inventory, release escrow or exercise delegated authority:

**is an independently verifiable binding receipt enough for your control model — or would you require independent execution replay before the financial state transition can be trusted?**

That difference defines the next product boundary.