# RESONANCE Verified Report #041

# ASTRA–CaPU v1.0-A7 — Authenticated Device Outcome Receipts

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#102`  
**Verified CaPU content head:** `5cdaa5280348841bf8448c5a7844c273df257c5d`  
**Base A6 head:** `2cf971e6f9cdefd213e72b4e79d4840c6ed83808`  
**Primary workflow:** `ASTRA-CaPU v1.0-A7 Authenticated Device Receipts`  
**Primary run:** `33256771503`

## Result

# **PASS — bounded authenticated device-receipt gate verified**

A6 accepted exact `NOT_COMMITTED / COMMITTED / CONFLICT` outcome evidence for one unresolved accelerator-like attempt, but trusted the supplied outcome discriminator. A7 inserts a trusted-device receipt gate in front of A6:

```text
accelerator receipt
+ trusted device ID
+ trusted key epoch
+ monotonic receipt sequence
+ exact full attempt identity
+ exact outcome binding
+ authenticated envelope tag
        ↓
A7 authentication gate
        ↓
A6 exact outcome reconciliation
```

Only an authenticated exact receipt is allowed to drive A6 reconciliation.

## Trust identity and sequence

Trusted state:

```text
trusted_device_id
trusted_key_epoch
trusted_key_material
trusted_next_receipt_sequence
```

Authenticated receipt identity:

```text
device_id
+ key_epoch
+ receipt_sequence
+ authority_tag
+ queue_incarnation
+ queue_epoch
+ slot_id
+ command_id
+ attempt_id
+ effect_id
+ outcome
+ synthetic_auth_tag
```

The receipt sequence is monotonic and consumed on authentication acceptance, including when the downstream A6 semantic reconciler rejects an authenticated but stale receipt. This prevents the same authenticated envelope from being replayed against a later state.

## Deterministic evidence

The exact-head RTL trajectory produced:

```text
a7_attempt0_forwarded outcome=UNKNOWN effect_count=0
a7_forged_receipt_blocked reject_code=5 next_receipt_seq=0
a7_negative_receipt_authenticated seq=0 outcome=NOT_COMMITTED next_receipt_seq=1
a7_attempt1_forwarded outcome=UNKNOWN effect_count=1
a7_stale_receipt_replay_blocked reject_code=4 next_receipt_seq=1
a7_foreign_device_receipt_blocked reject_code=2 next_receipt_seq=1
a7_committed_receipt_authenticated seq=1 terminal_committed=1 next_receipt_seq=2
a7_terminal_replay_blocked reject_code=11 effect_count=1
ASTRA_CAPU_V1_A7_AUTHENTICATED_DEVICE_RECEIPT_PASS
```

The deterministic software mirror and 11 focused unit tests passed. The complete A6 RTL trajectory, all 13 A6 unit tests and the A6 bounded proof also remained green.

Canonical deterministic result:

```text
schema:
capu.astra.authenticated-device-receipt.result.v1.0-a7

result digest SHA256:
6781dbfbd1b529866709980a3a85a38bd37f505daaddd53fd7c8e106ab863d2f

external_effect_count: 1
persistent_next_attempt: 2
next_receipt_sequence: 2
last_outcome: COMMITTED
forged_receipt_reject_code: 5
stale_receipt_reject_code: 4
foreign_device_reject_code: 2
terminal_replay_reject_code: 11
```

## Exact-head CI

Verified content head:

```text
5cdaa5280348841bf8448c5a7844c273df257c5d
```

GitHub Actions checked PR merge ref:

```text
c8de47b9e2f4968bb72400854049b7cdc3325eec
```

All exact-head workflows were green:

- `ASTRA-CaPU v1.0-A7 Authenticated Device Receipts` — run `33256771503` — PASS
  - deterministic job `99111772866` — PASS
  - formal job `99111773047` — PASS
- `Validate Examples` — run `33256771604` — PASS
- `CaPU Core v0 RTL Smoke` — run `33256771575` — PASS
- A6 deterministic and unit regressions — PASS
- A6 bounded-safety regression — PASS

## Formal evidence

Schema:

```text
capu.hardware.astra-authenticated-device-receipt-formal-proof.v1.0-a7
```

Result:

```text
proof method: bounded model checking
formal device width: 2 bits
formal tag width: 2 bits
formal identity width: 2 bits
formal auth-tag width: 4 bits
trusted device count: 1
trusted key-epoch count: 1
maximum unresolved attempts: 1
safety depth: 32 — PASS
cover depth: 56 — PASS
VCD witnesses: 9
synthetic MAC model: true
monotonic receipt sequence: true
authenticated semantic reject consumes sequence: true
A6 bounded-safety regression: PASS
```

Pinned toolchain:

```text
SBY b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input SHA256:
66c56e74e3ce48b29205e6d401e3175a2482cb3b1783db504dd249a4dcf36815

safety log SHA256:
d80f67ea54c05bb494dd0cc4a9886b890e6863242704dc5a2c426fdec756d397

cover log SHA256:
191d838f5a71acbf3cb06c26d3979c7205675833b6c8a9ee8449536584909dc1

A6 regression log SHA256:
1686343dca7671a25fe1536f089bcdc4ecbf5f300ac79cd6888ede4766bd185e
```

## Sealed artifacts

Executable evidence:

```text
artifact: astra-capu-v1-a7-authenticated-device-receipt-evidence
artifact ID: 9716040264
ZIP SHA256:
eb9e1c6c6a03642a83c8c395f6dea97e0eb230c1db03f9484f0c2863c0744268
```

Formal evidence:

```text
artifact: astra-capu-v1-a7-authenticated-device-receipt-formal-evidence
artifact ID: 9716074483
ZIP SHA256:
ad63eb4a1dfd4735a0c7294b179a1341582417d9e3635d75c26931a5162d11b5
```

## Verified bounded invariants

```text
A6_RECONCILE_VALID
=> A7_AUTH_ACCEPT
```

```text
A7_AUTH_ACCEPT
=> EXACT_DEVICE_ID
&& EXACT_KEY_EPOCH
&& RECEIPT_SEQ == TRUSTED_NEXT_RECEIPT_SEQ_PRE
&& EXACT_FULL_ATTEMPT_IDENTITY
&& EXACT_OUTCOME_BINDING
&& AUTH_TAG_MATCH
```

```text
AUTH_REJECT
=> NO_A6_RECONCILIATION
&& NO_TRUST_STATE_MUTATION
```

```text
AUTH_ACCEPT
=> TRUSTED_NEXT_RECEIPT_SEQ_POST
   == TRUSTED_NEXT_RECEIPT_SEQ_PRE + 1
```

```text
AUTH_ACCEPT + A6_SEMANTIC_REJECT
=> SEQUENCE_CONSUMED
&& NO_A6_PERSISTENT_OUTCOME_MUTATION
```

```text
FOREIGN_DEVICE_OR_KEY_EPOCH
=> NO_AUTH_ACCEPT
```

```text
STALE_RECEIPT_SEQUENCE
=> NO_AUTH_ACCEPT
```

## Meaning of the result

A7 moves the ASTRA–CaPU accelerator boundary from “exact evidence identity” to “authenticated receipt envelope”:

- a forged receipt cannot create `NOT_COMMITTED` replay authority;
- a stale authenticated receipt cannot be reused after its sequence is consumed;
- a receipt from a foreign device cannot mutate the A6 persistent outcome state;
- an exact authenticated `COMMITTED` receipt can terminally close replay authority.

This is the first bounded CaPU slice in the line where the outcome source itself participates in the trust boundary rather than merely supplying an unverified discriminator.

## Claim boundary

The A7 authentication tag is a transparent rotate/XOR **synthetic MAC model** for state-machine verification. It is not production cryptography and does not establish cryptographic unforgeability, key secrecy, or standards conformance.

This is a **bounded reduced-width single-device model** with one trusted device, one key epoch, one persistent receipt sequence, one A6 lineage and one unresolved attempt.

It does **not** prove:

- SPDM, DICE, TPM, secure-element, PKI, certificate-chain or remote-attestation conformance;
- real cryptographic unforgeability;
- secure provisioning or key secrecy;
- key rotation or re-attestation;
- Byzantine-resistant multi-source reconciliation;
- actual NVRAM or complete power-loss persistence;
- real accelerator transport;
- CDC or memory-order correctness;
- FPGA timing or PPA;
- liveness or availability;
- production widths;
- unbounded correctness.

CaPU PR #102 remains draft and unmerged at publication time.
