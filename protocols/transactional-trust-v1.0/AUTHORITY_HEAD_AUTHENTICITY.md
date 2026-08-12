# TTP Extension — Authority Head Authenticity

## Core law

# **FRESHNESS CLAIM ≠ AUTHENTIC FRESHNESS EVIDENCE**

A verifier cannot safely use an authority-generation watermark until the watermark's source, domain and contents are authenticated.

Verified #030 established a monotonic authoritative generation as a fence against stale regional authority replicas. This extension defines the next precondition: **the head used as that fence must itself be trustworthy evidence.**

## Invariants

### I83 — FRESHNESS CLAIM ≠ AUTHENTIC FRESHNESS EVIDENCE

A claimed generation number has no consequential authority merely because it is well-formed or plausible.

### I84 — AUTHORITY HEAD IDENTITY, DOMAIN, GENERATION, AND CONTENT MUST BE AUTHENTICATED BEFORE THEY CAN FENCE A CONSEQUENCE

Authentication should bind, at minimum:

- authority namespace / domain
- head generation
- rule or registry identity / digest
- rule status where applicable
- successor / transition identity where applicable
- signer / key identity

### I85 — UNAUTHENTICATED OR TAMPERED AUTHORITY HEAD → HOLD BEFORE REGIONAL FRESHNESS EVALUATION

Do not execute:

```text
replica_generation >= claimed_head_generation
```

until `claimed_head_generation` is authenticated as part of the exact head statement.

### I86 — AUTHENTIC HEAD EVIDENCE CAN FENCE A STALE REPLICA, BUT AUTHENTIC OLD-HEAD REPLAY REQUIRES AN ADDITIONAL MONOTONICITY MECHANISM

Authenticity proves who produced a statement and that its bytes were not modified. It does not, by itself, prove that the statement is the newest authentic head ever issued.

## Decision chain

```text
RECEIVE AUTHORITY HEAD H
        ↓
VERIFY AUTHENTICATION
- signer/key trusted?
- authority domain bound?
- payload canonical and intact?
- signature/MAC valid?
        ↓
 authentic?
 ├─ no → HOLD / REJECT HEAD
 └─ yes
      ↓
   EXTRACT AUTHENTICATED GENERATION G
      ↓
   VERIFY REGIONAL VIEW CURRENTNESS
      ↓
   replica_generation >= G ?
      ├─ no → STALE AUTHORITY VIEW → HOLD
      └─ yes
           ↓
       VERIFY RULE STATUS / DIGEST / GENERATION
           ↓
       VERIFY PROOF + SCOPE
           ↓
       CURRENT OWNER ADOPTS
           ↓
       FENCED COMMIT
           ↓
PROVE HEAD AUTHENTICITY → VIEW CURRENTNESS → PROOF AUTHORITY → EFFECT
```

## Why order matters

Unsafe order:

```text
read untrusted generation
→ compare replica
→ conclude fresh
→ later inspect authentication
```

can already turn a forged lower watermark into stale authorization.

Safe order:

```text
authenticate exact head bytes
→ only then extract generation
→ only then compare regional freshness
```

## Minimal evidence object

```text
authority_head = {
  authority_namespace,
  generation,
  registry_or_rule_root,
  status / transition identity,
  signer_or_key_id,
  authentication_algorithm,
  signature_or_mac
}
```

The cryptographic scheme and key-management model are deployment-specific. The protocol requirement is evidence binding, not a particular signature primitive.

## Boundary

The Verified #031 benchmark uses deterministic HMAC-SHA256 with a fixed test key. This models authentication and tamper detection only; it is not a recommended production key-distribution or PKI architecture.

Replay of a historically authentic head is intentionally outside this extension's solved scope. A verifier needs a monotonic witness, checkpoint, transparency log, trusted local watermark, quorum, or equivalent mechanism to distinguish **authentic old** from **authentic current**.

## Reference benchmark

`benchmarks/authority-head-authenticity-v1.0/`

Verified Report #031: `reports/verified/031-authority-head-authenticity/REPORT.md`
