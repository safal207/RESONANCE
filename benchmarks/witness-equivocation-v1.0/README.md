# RESONANCE Witness Rollback / Equivocation Benchmark v1.0

Verified #033 used an independently authenticated witness to detect rollback of verifier-local checkpoint storage. This benchmark attacks that new trust dependency.

## Question

What if the witness is independent from verifier storage, but the witness itself presents inconsistent authenticated histories to different verifiers?

# **INDEPENDENT WITNESS ≠ CONSISTENT WITNESS**

## Fixture

The authority has two authentic heads:

```text
H7 = generation 7 / R1 ACTIVE
H9 = generation 9 / R2 ACTIVE
```

`witness-A` first emits a legitimate parent statement `WA42` at witness sequence 42 for H7.

It then equivocates at sequence 43 by authenticating two different children of exactly the same parent:

```text
WA43-good:
witness_id = witness-A
witness_seq = 43
previous_statement_digest = digest(WA42)
generation = 9
head_digest = digest(H9)
MAC = valid

WA43-fork:
witness_id = witness-A
witness_seq = 43
previous_statement_digest = digest(WA42)
generation = 7
head_digest = digest(H7)
MAC = valid
```

Both statements are locally authentic. They cannot both be one linear witness history.

A second independent `witness-B` authenticates H9 and is used only after witness-A has been quarantined.

## Failure experiment

An isolated verifier sees only `WA43-fork`, has local checkpoint 7, and receives authentic H7 with a generation-7 R1 replica.

If the verifier checks only witness authenticity and local consistency, it accepts and commits one external effect even though another verifier was shown `WA43-good` at the same witness sequence.

## Safe experiment

The two witness-A statements are gossiped/cross-checked before consequence.

If the same witness identity signs different statement digests at the same sequence with the same parent, the verifier returns:

```text
witness_equivocation_detected
→ HOLD
→ 0 adoption rows
→ 0 external effects
```

Recovery quarantines witness-A, authenticates independent witness-B at generation 9, reconstructs the local checkpoint to 9, rejects H7 as an authority-head rollback, synchronizes R2/H9, and allows the current path exactly once.

## Scope

This is a deterministic benchmark. HMAC keys model authenticated identities; they are not production PKI. Gossip is modeled by explicitly presenting both signed statements to the verifier. The benchmark does not claim a production Byzantine quorum protocol or transparency-log design.

It isolates one property: **a single independent witness can still equivocate, and locally valid signed statements require consistency evidence before they can anchor consequential recovery.**
