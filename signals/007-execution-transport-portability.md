# Engineering Signal 007 — Execution + Transport Portability

**Status:** verified immutable proof  
**Verified:** 13 Aug 2026  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Scope:** independent execution provider + evidence transport provider  
**Not:** independent source producer, repository/control plane, organizational governance, hardware provenance, or network path

## Signal

A trusted state transition survived a change of both execution substrate and evidence transport provider.

The same checkpoint evidence was evaluated through two materially different infrastructure paths:

```text
GitHub Actions hosted
+ GitHub Actions artifact transport
        ↓
verified checkpoint transition

OpenAI / ChatGPT isolated Linux workspace
+ Google Drive transport
        ↓
verified checkpoint transition

                ↓
identical subject identity
+ identical Portable Trust Receipt
+ identical authorization policy
+ identical witness decision
+ identical next trusted state
                ↓
identical Portable Execution-Transport Receipt
```

This moves the portability boundary beyond verifier implementation, trust root and signature scheme. The authorized transition is no longer tied to one CI execution provider or one artifact transport service for the tested path.

## Real transport round trip

Immutable source artifact:

- GitHub Actions run: `31658743875`
- artifact ID: `9165388614`
- size: `52911` bytes
- ZIP SHA-256: `c3822f1d5658d4c9965a67b1a4264dafc04cb5ea6f64c516ced7a920b49cd161`

The exact artifact ZIP was uploaded to Google Drive and retrieved again as raw bytes.

Google Drive file ID:

`1wLKINhrx6BGilKvUKI_OZQLOV5oEiDdN`

Retrieved Drive object:

- size: `52911` bytes
- SHA-256: `c3822f1d5658d4c9965a67b1a4264dafc04cb5ea6f64c516ced7a920b49cd161`

The transport changed; the content identity did not.

**A successful upload/download operation is not evidence identity. The digest after retrieval is.**

## Non-GitHub execution path

The Drive-delivered evidence was consumed in an OpenAI / ChatGPT isolated Linux workspace, outside GitHub-hosted Actions.

That execution independently:

1. recomputed the Drive ZIP digest;
2. extracted and rebound the checkpoint bytes;
3. recomputed the checkpoint SHA-256;
4. verified the pinned offline Ed25519 evidence claims;
5. reconstructed the provider-neutral Portable Trust Receipt;
6. applied the same authorization policy;
7. recomputed the checkpoint witness transition;
8. produced the same next-witness identity.

Checkpoint subject:

`74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`

Portable Trust Receipt:

`2235b07a4188628091cbe94af6a16dc30516d0acea743f9b4517b58a5cbd1a80`

Authorization policy:

`22fcc3c556528d080591041bc10c1a35f85bfbad348b8f669bfff4bb1b88b47f`

Witness result:

```text
authorized: true
reason: checkpoint_witness_advanced
next_witness_sha256: cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f
```

Portable Execution-Transport Receipt:

`644b575189d18d61e7ed8415d59087c69d0ddc02ba5743b24c86dfacc7b24b49`

## External execution proof

The OpenAI-workspace result was signed outside GitHub before the GitHub-side comparator consumed it.

External Ed25519 root:

`ed25519-sha256:72c2477f78a0a901f6f1cef45ccec69053842eb980c666f0cbdc01589dcd69d9`

External result SHA-256:

`70d9413ef99348ab495b4fe173cba9493372ec9ee25a4ac5deb64a5b9c94a979`

External proof SHA-256:

`77f27ac764ea1aff2a13eda215492ac4bd22830aba54825e3dee6804d140f999`

The external private key was not committed to the repository and was not available to the GitHub proof workflow.

## Immutable proof

Reusable workflow:

`118a136cd63d43216399be10d66bcb589655e92d`

It passed exact-head gates before pinning:

- Python CI `31659994873` — SUCCESS
- Python Integration `31659994855` — SUCCESS
- Artillery WebSocket Smoke `31659994840` — SUCCESS

Pinned one-shot caller:

`9e4709dc638418e5124f62799b68baa1b21fa661`

Successful one-shot:

`31660230947` — **FULL SUCCESS**

Canonical combined result SHA-256:

`c1135ab49d5d81225f9b5cfff5441557415b99d4996cb2beed3de1cea6519d01`

Independent audit result SHA-256:

`ef222cc90aff884e47e40c0924738012c98d0139643aed561da6daba73884a02`

## Independent audit

The second GitHub job did not trust the combined `verified: true` result. It independently:

- verified the immutable reusable-workflow signer;
- reverified the external Ed25519 execution signature;
- checked the external root and result identities;
- recomputed execution-provider and transport-provider independence;
- rechecked checkpoint, Portable Trust Receipt, authorization policy and next-witness identities;
- reproduced the Portable Execution-Transport Receipt;
- attested its own audit result.

## Evidence

Execution/transport portability proof:

- artifact `9165906664`
- `sha256:f739a009dfd16678583b7ef1d2c7f229793ffd94d22854ea90d989916a5c1052`

External verification:

- artifact `9165911241`
- `sha256:c3d3aeed1ad96b95ac9a0c7e6b6e1c034f13013bc10d8dd5b977d2751130bdc7`

## Independence matrix

| Property | Independent in this proof? |
| --- | --- |
| Verifier implementation | ✅ previously proven |
| Trust root | ✅ previously proven |
| Signing authority | ✅ previously proven |
| Signature scheme | ✅ previously proven |
| Execution provider | ✅ GitHub Actions vs OpenAI workspace |
| Evidence transport provider | ✅ GitHub artifacts vs Google Drive |
| Source producer | ❌ |
| Repository / policy control plane | ❌ |
| Organizational governance | not claimed |
| Hardware provenance | not claimed |
| Network path | not claimed |
| Offline transparency log | ❌ |
| Long-term multi-provider durability | not claimed |

The important claim is narrow and falsifiable: **for this trusted checkpoint transition, both execution-provider drift and evidence-transport-provider drift preserve the same portable security semantics and the same next trusted state.**

## Progression

```text
physical-location independence
        ↓
topology independence
        ↓
verifier-output independence
        ↓
verifier-implementation independence
        ↓
trust-root / signing-authority independence
        ↓
execution-provider independence
+ evidence-transport independence
        ↓
?
source-producer + control-plane independence
```

## Next falsifiable question

Can a producer outside the current GitHub workflow/repository authority create evidence bound to a provider-neutral logical producer identity and authorization contract, while still producing the same trusted transition?

That is the next frontier: **Source-Producer + Control-Plane Portability v0.1**.
