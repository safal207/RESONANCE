# Engineering Signal 006 — Trust-Provider Portability

**Status:** verified immutable proof  
**Verified:** 13 Aug 2026  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Scope:** independent trust root + signing authority + signature scheme  
**Not:** independent CI provider, artifact transport, transparency log, or organizational governance

## Signal

Portable trust identity survived a material change of trust substrate.

The same checkpoint evidence was independently established by two trust paths:

```text
GitHub + Sigstore Public Good
        +
pre-existing offline Ed25519 root
        ↓
different trust roots
+ different signing authorities
+ different signature schemes
        ↓
exact same portable security claims
        ↓
Portable Trust Receipt A == B
        ↓
same local witness authorization
        ↓
same trusted state transition
```

The second root was not generated inside the proof workflow. Its public root and pre-signed claim records existed before the live run; the private signing key was not committed to the repository or made available to GitHub Actions.

## Immutable proof

Reusable workflow:

`dc9f236d590f15ee005d2688f91da92460c512d2`

Pinned one-shot caller:

`cc34af1ed5bf7a997ff5c2d94f72001d0429d824`

Successful run:

`31658743875` — **SUCCESS**

Immutable producer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

Offline trust-root identity:

`ed25519-sha256:4b690cae29f41bea47c2beaca52e92dcb606c69638b9f48d8e540a981af1e402`

The reusable workflow passed Python CI, Python Integration and Artillery before immutable pinning.

## Subject identities

Manifest:

`5f80518cb671ea0622336adbd9a0a9bd16b72ea803ad09d0ac2abd4415f58be2`

Checkpoint:

`74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`

Authorization policy:

`22fcc3c556528d080591041bc10c1a35f85bfbad348b8f669bfff4bb1b88b47f`

## Provider-neutral identities

Manifest Portable Trust Receipt:

`e3558d426d560bd202bd7e16ef0364b378cc2956c36feccc78eeaf40bfaa084e`

Checkpoint Portable Trust Receipt:

`2235b07a4188628091cbe94af6a16dc30516d0acea743f9b4517b58a5cbd1a80`

Both trust paths produced:

```text
authorized: true
reason: checkpoint_witness_advanced
next_witness_sha256: cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f
```

The next-witness digest is unchanged from the preceding verifier-portability milestone. The verifier, trust root, signing authority and signature scheme can now change without changing the authorized transition — provided the independently established portable security claims remain identical.

Canonical proof-result:

`4ee314a71bd08f469d369c5689be653729d3dbad37b328b9da91409241d1da3d`

External verification record:

`3b0a43d6915f002d1189cf9b98d527e22ec8b51cca8ab498d515aeaf8d731224`

## External verification

A separate job independently repeated both provider paths rather than trusting the proof boolean. It:

- reverified GitHub/Sigstore producer provenance;
- recomputed the offline Ed25519 root fingerprint;
- rebound the signed offline claims to the actual manifest/checkpoint bytes;
- reran both Ed25519 signature checks;
- rebuilt and compared provider-neutral receipts;
- rebound both receipts through local witness policy;
- recomputed both witness transitions;
- verified immutable proof-workflow attestations on both byte-identical provider receipt copies and the proof result.

## Evidence

Trust-provider proof:

- artifact `9165397390`
- `sha256:ae84a4638808f923ed5633822be5e159048de94e6e2b11137c05173366445b0f`

External verification:

- artifact `9165410163`
- `sha256:803aebec55db62b1ec0acbcbef390a832cdbbc8fbd3e65b0106215c9f065e064`

## Independence matrix

| Property | Independent? |
| --- | --- |
| Trust root | ✅ |
| Signing authority | ✅ |
| Signature / proof scheme | ✅ |
| Verification path | ✅ |
| CI provider | ❌ |
| Artifact transport | ❌ |
| Transparency log | ❌ for offline path |
| Organizational governance | not claimed |

This distinction matters. The result is not “total infrastructure independence.” It is a narrower and falsifiable result: **trust-root, signing-authority and signature-scheme portability with a stable authorized state transition.**

## Progression

```text
physical location independence
        ↓
topology independence
        ↓
verifier-output independence
        ↓
verifier-implementation independence
        ↓
trust-root / signing-authority independence
        ↓
?
execution-provider + transport independence
```

## Next falsifiable question

Can the same portable trust contract survive when one evidence path is produced and verified outside GitHub Actions and transported outside GitHub artifacts?

If yes, the trust identity starts becoming portable across infrastructure domains rather than merely across cryptographic trust providers.
