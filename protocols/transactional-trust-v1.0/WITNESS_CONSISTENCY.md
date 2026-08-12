# RESONANCE TTP — Witness Consistency / Equivocation Rule

Verified #033 showed that independently authenticated witness evidence can help recover a verifier whose local anti-rollback checkpoint was restored backward. That creates a new trust dependency: the witness history itself.

# **INDEPENDENT WITNESS ≠ CONSISTENT WITNESS**

## Decision rule

```text
RECEIVE WITNESS STATEMENT W
        ↓
AUTHENTICATE W
        ↓
BIND
- witness identity
- witness sequence
- parent statement digest
- authority-head digest
- generation
        ↓
GOSSIP / CROSS-CHECK WITNESS VIEW
        ↓
CONFLICTING AUTHENTIC STATEMENT
FOR SAME WITNESS SEQUENCE + PARENT?
  ├─ yes
  │    ↓
  │  witness_equivocation_detected
  │    ↓
  │  HOLD BEFORE CONSEQUENCE
  │    ↓
  │  QUARANTINE WITNESS
  │    ↓
  │  RESOLVE NON-CONFLICTING INDEPENDENT EVIDENCE
  │    ↓
  │  RECONSTRUCT / RECONCILE TRUST CHECKPOINT
  └─ no
       ↓
   VERIFY WITNESS → HEAD → CHECKPOINT CURRENTNESS
       ↓
   VERIFY AUTHORITY VIEW / RULE / PROOF
       ↓
   CURRENT OWNER ADOPTS
       ↓
   FENCED COMMIT
       ↓
PROVE WITNESS CONSISTENCY → CHECKPOINT → HEAD → EFFECT
```

## I95 — INDEPENDENT WITNESS ≠ CONSISTENT WITNESS

Failure-domain independence from verifier storage does not prove that the witness presents one globally consistent authenticated history.

## I96 — AUTHENTIC WITNESS STATEMENT ≠ UNIQUE WITNESS HISTORY

Cryptographic validity proves origin and integrity of a statement. It does not prove that the signer did not authenticate another incompatible statement for the same history position.

## I97 — SAME WITNESS SEQUENCE + SAME PARENT + DIFFERENT AUTHENTIC CONTENT = EQUIVOCATION EVIDENCE

When two valid statements from the same witness occupy the same sequence and parent position but have different content digests, the contradiction is itself first-class evidence. A verifier must not resolve it by choosing the more permissive branch.

## I98 — EQUIVOCATING WITNESS MUST BE QUARANTINED; RECONSTRUCT TRUST FROM NON-CONFLICTING INDEPENDENT EVIDENCE BEFORE CONSEQUENCE

Once equivocation is established, the conflicted witness cannot remain the sole basis for trust reconstruction. Fail closed, preserve both signed branches, quarantine the witness for the affected authority domain, and recover from a policy-approved non-conflicting evidence set.

## Evidence requirement

Preserve at least:

- both authenticated witness statements;
- witness identity and key identity;
- witness sequence;
- parent statement digest;
- statement digests;
- authority-head digests and generations;
- cross-view/gossip evidence that exposed the fork;
- quarantine disposition;
- recovery evidence source;
- reconstructed checkpoint;
- post-recovery head-currentness decision;
- resulting external effect or proof of no effect.

## Important distinction

```text
witness rollback / stale statement
≠
witness equivocation
```

A merely old statement may be a replay. Equivocation requires incompatible authenticated statements that cannot occupy the same logical position in one linear witness history.

The benchmark uses the strongest simple form:

```text
same witness_id
+ same witness_seq
+ same parent digest
+ different authenticated content
= direct fork evidence
```

## Recovery boundary

Verified #034 demonstrates recovery using a second non-conflicting witness identity. It does not define a universal quorum threshold or Byzantine fault-tolerance policy. Production systems may require transparency logs, multi-witness quorum, gossip, consensus, hardware roots, or another independently justified mechanism.

A later protocol extension should test disagreement among multiple witnesses where no single signer can simply be quarantined and replaced.
