# Engineering Signal 005 — Independent Verifier Portability

**Status:** verified immutable proof  
**Verified:** 12 Aug 2026  
**Scope:** independent verifier implementations over a shared GitHub/Sigstore attestation substrate  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Not:** proof of independent trust providers, transparency logs, CI providers, or signing infrastructure

## Signal

Portable trust identity survived a change of verifier implementation.

The same producer-attested subjects were verified through two distinct authoritative paths:

```text
GitHub CLI: gh attestation verify
            +
Sigstore Cosign v3.0.6: verify-blob-attestation
            ↓
independent cryptographic verifier implementations
            ↓
exact same subject / signer / source / runner-policy semantics
            ↓
Normalized Verification Receipt A == B
            ↓
Evidence Bundle v0.2 A == B
            ↓
witness transition A == B
```

The Cosign verdict did not derive from the GitHub CLI verification JSON. GitHub CLI was used separately to retrieve/decompress stored Sigstore bundles, while Cosign independently verified those bundle attestations and the workflow independently enforced the required Fulcio certificate policy.

## Immutable proof

Successful one-shot run:

`31623698930` — **SUCCESS**

Pinned caller:

`ff9c14da8e35b3bbf02fa53fd4a64f0243da9755`

Immutable independent-verifier workflow:

`fa20161f4e0c77f4caa97e2e0febfe0cea240d82`

Immutable producer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

Immutable trust-root rotation workflow:

`e2cb6a014236bc561d03c405f4986146026041fa`

Cosign verifier:

- version: `v3.0.6`
- installer commit: `6f9f17788090df1f26f669e9d70d6ae9567deba6`

The reusable workflow bytes passed Python CI, Python Integration and Artillery before being pinned.

## Verified subject identities

Manifest SHA-256:

`5f80518cb671ea0622336adbd9a0a9bd16b72ea803ad09d0ac2abd4415f58be2`

Checkpoint SHA-256:

`74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`

Cosign found six stored attestation bundles satisfying the exact signer/certificate policy for each subject in the successful run.

## Portable identities

Both independent verifiers converged on the same manifest normalized receipt:

`05367cac13290c50dbd413c37b3741a6d1977f19f2b12a29f0e1e154d79e73ca`

Both converged on the same checkpoint normalized receipt:

`fc14a91512662d58a6db21263bf0dd71ce5ad2abcc09a431c027c4bb73a4db70`

Both produced the same Evidence Bundle v0.2:

`63110899de2feb57152232b07e63a48921e3822320d6b1eb5e7cd6b016bd9892`

Both witness decisions were:

```text
authorized: true
reason: checkpoint_witness_advanced
next_witness_sha256: cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f
```

Canonical proof-result SHA-256:

`2b857ced0b8ae39ac700844358ef7017b1badc7149d063a6de3fad30b355c6b3`

External recomputation record SHA-256:

`e128b187b776b3e1da2adacd05cc4e6c299a6d2992d9537a9047c50e01b5f0f8`

A notable result is that these receipt, bundle and witness identities are exactly the same as in the preceding representation-independence experiment. The identity survived both byte-layout drift and verifier-implementation drift.

## External verification

A separate job independently:

- recomputed both subject digests;
- recomputed receipt equality and hashes;
- recomputed Evidence Bundle v0.2 equality;
- confirmed distinct verifier implementations;
- reran Cosign v3.0.6 on selected Sigstore bundles;
- rechecked producer signer SHA, repository, source ref and `github-hosted` runner policy from certificate evidence;
- reverified the immutable producer with GitHub CLI;
- verified the immutable proof signer on both GH/Cosign receipt copies;
- verified the immutable proof signer on both GH/Cosign bundle copies;
- verified the proof result.

Only one canonical copy of each identical receipt/bundle needed direct attestation: the byte-identical copy from the other verifier path independently verified by content identity.

## Evidence artifacts

Independent verifier proof:

- artifact `9152287850`
- `sha256:4ec977fcb559ba2f84bf91c5641798f98a5ccea59d028a4cd22d908c104662e3`

External verification:

- artifact `9152310899`
- `sha256:4ebc4978164bad5708f24fcb610ee35136fcfedc693f61b2c1bd0dd958398b44`

Both have 30-day retention and expire 11 Sep 2026.

## A useful failure on the way

The first pinned attempt failed before Cosign because the direct GitHub `bundle_url` transport was treated as ordinary UTF-8 JSON. The stored object is encoded for transport and requires the supported GitHub CLI decoding path.

The repair deliberately changed only retrieval:

```text
GitHub attestation storage
        ↓
gh attestation download
        ↓
materialized Sigstore bundle
        ↓
Cosign independent verification
```

That distinction matters:

**transport assistance is not verifier agreement.**

## What this proves

For the tested GitHub/Sigstore attestation substrate, changing the cryptographic verifier implementation from GitHub CLI to Sigstore Cosign did not change portable evidence identity or the authorized recovery transition when both independently proved the same security contract.

The resulting trust identity is therefore not bound to one verifier executable.

## What this does not prove

The two verification paths still share:

- GitHub artifact-attestation storage;
- Sigstore/Fulcio signing infrastructure;
- the same transparency-log ecosystem;
- the same producer workflow and subject bytes;
- GitHub Actions as the CI environment.

So this is **verifier portability**, not yet **trust-provider portability**.

## Next falsifiable question

Can the same normalized security contract survive a change of trust/provider substrate rather than only a change of verifier implementation?

```text
GitHub/Sigstore trust path
        +
independent provider trust path
        ↓
normalized security semantics
        ↓
same portable receipt — or hard failure
```

That is the next boundary.
