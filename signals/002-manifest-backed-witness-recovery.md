# Engineering Signal 002 — Manifest-Backed Witness Recovery

**Status:** verified immutable recovery proof  
**Verified:** 12 Aug 2026  
**Scope:** open-source engineering signal  
**System:** `safal207/Liminal` trusted-recovery witness chain  
**Not:** a claim that physical artifact paths are trustworthy by themselves

## Signal

A real GitHub Actions trusted-recovery chain moved from hard-coded artifact-path recovery to a manifest-backed evidence identity model and completed an immutable one-shot proof end to end.

The engineering transition was triggered by an ordinary but important failure: logical evidence existed and was correctly attested, while the downloaded physical artifact appeared at a nested path that the consumer did not expect.

The resulting design now separates:

```text
logical evidence identity
→ attested manifest
→ logical_id + generation
→ expected SHA-256
→ bounded physical candidate field
→ digest match
→ re-anchor
→ checkpoint attestation verification
→ witness recovery
→ external verification
```

## Claim classification

### Verified fact

The final one-shot GitHub Actions run completed successfully:

- run: `31610364021`
- caller commit: `d2d2fc897062b5fb211631dc2f1cd97ae76f474f`
- immutable manifest-producing checkpoint workflow: `f31b56a5e21a668bcb98791b05542652760dcc27`
- immutable manifest-backed witness workflow: `3f0af42a680f42923cb18591ba127206b2292599`
- immutable trust-root rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

The run completed all of the following stages successfully:

1. trust-root rotation drill;
2. accepted generation-1 checkpoint creation;
3. Evidence Manifest generation;
4. checkpoint attestation;
5. manifest attestation;
6. manifest locator resolution;
7. manifest signer verification;
8. strict manifest parse;
9. `logical_id + generation` lookup;
10. SHA-256 matching against bounded physical candidates;
11. manifest-backed re-anchor;
12. checkpoint signer verification;
13. witness recovery;
14. stale-checkpoint rejection;
15. witness/result attestation;
16. external witness-chain recomputation;
17. external immutable signer verification.

### Verified evidence artifacts

The successful run produced four retained workflow artifacts:

- trust-root rotation evidence — `sha256:506a6b90697c4389160535483e888edbf051577fce2183c26b55936265aa36d9`
- attested checkpoint + manifest evidence — `sha256:bab22855fd44188909ca097985a473ed02fe3b59050348557200baba17e4b991`
- witness evidence — `sha256:21fd0ded16a9e05529bc881ef3aa7f33d8945ff2ec5f1c8dfcf17aa12856d160`
- external witness verification — `sha256:f248ff305f6e2364d77f55173a1ef4503fbfd0d6ac9840b7b0371922dbff1109`

The artifacts are retained by that run until 11 Sep 2026.

## Causal trajectory

```text
checkpoint evidence exists
→ consumer expects wrong physical path
→ ResolutionFailure
→ bounded locator adapter
→ ReAnchor
→ successful immutable witness proof
→ Evidence Manifest primitive
→ producer binds logical identity to SHA-256
→ producer attests manifest
→ witness verifies manifest signer first
→ witness resolves checkpoint by digest, not filename
→ checkpoint signer verification
→ VerifiedRecovery
→ external proof succeeds
```

The important transition is not "we fixed a path." The path failure exposed a more general distinction:

> Logical evidence identity is not the same thing as physical artifact location.

## Why it matters

Hard-coding a downloaded path makes trust consumers accidentally depend on packaging topology. A nested directory, archive-layout change or transport-specific extraction rule can then break recovery even when the trusted evidence itself is intact.

Manifest-backed recovery moves the stable identity to evidence properties that survive path drift:

```text
logical_id
+ generation
+ producer
+ evidence_type
+ SHA-256
+ verification expectations
```

The physical locator becomes an observed fact used for retrieval, not a trust identity.

The model also keeps resolution and verification separate:

- finding bytes is not proof that they are trusted;
- matching a manifest digest is not signer verification;
- the manifest itself must be verified before its digest contract is used;
- the recovered checkpoint must still pass its own signer/attestation checks;
- ambiguity fails closed rather than being ranked heuristically.

## Safety boundary

This signal proves one concrete GitHub Actions recovery chain and its recorded immutable workflow/run evidence. It does **not** prove:

- that every artifact transport or CI provider implements the same topology semantics;
- that SHA-256 identity alone establishes authority;
- that a manifest can replace signer, policy, registry or attestation verification;
- that ambiguous matching candidates should be auto-selected;
- that the current implementation is a universal standard.

## Next verification gate

The next useful falsifiable step is to bind the manifest itself into the downstream recovery evidence so the witness result can expose a single inspectable chain:

```text
manifest digest
→ evidence digest
→ recovery result
→ witness digest
→ external verification
```

A stronger follow-up would then reproduce the same logical evidence identity contract through a second artifact packaging/topology implementation without changing the trust decision.

## Primary / inspectable references

1. Liminal PR #124 — recovery routing / evidence-resolution work: https://github.com/safal207/Liminal/pull/124
2. Successful manifest-backed one-shot run: https://github.com/safal207/Liminal/actions/runs/31610364021
3. Immutable manifest producer commit: https://github.com/safal207/Liminal/commit/f31b56a5e21a668bcb98791b05542652760dcc27
4. Immutable manifest-backed witness commit: https://github.com/safal207/Liminal/commit/3f0af42a680f42923cb18591ba127206b2292599
5. One-shot caller commit: https://github.com/safal207/Liminal/commit/d2d2fc897062b5fb211631dc2f1cd97ae76f474f

---

**RESONANCE classification:** Verified Engineering Signal — a real recovery failure was converted into a manifest-backed, digest-resolved, independently verified immutable recovery chain.
