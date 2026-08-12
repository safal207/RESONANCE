# RESONANCE Checkpoint Storage Rollback / Restored Verifier State v1.0

Verified #032 showed that an authentic old authority head must be rejected when it falls below a verifier's monotonic high-watermark. This benchmark attacks the high-watermark itself.

## Question

What happens if the verifier really reached generation 9, but its durable database is later restored from an older backup containing generation 7?

## Core law

**DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT.**

## Deterministic trajectory

```text
1. verifier observes authentic H7
   local checkpoint = 7
   capture backup snapshot S7

2. verifier observes authentic H9
   local checkpoint = 9
   independent authenticated witness W9 = 9

3. restore local verifier state from S7
   local checkpoint = 7
   witness W9 still = 9

4. replay authentic H7
   unsafe local-only verifier:
     7 >= local 7
     → ACCEPT
     → one external effect

5. witness-aware verifier:
     local 7 < witnessed 9
     → checkpoint_storage_rollback_detected
     → zero effects
     → reconstruct local checkpoint to 9

6. replay H7 after reconstruction
     7 < local 9
     → authority_head_rollback_detected
     → zero effects

7. fresh authentic H9 / R2
     → succeeds exactly once
```

## Witness fixture

The benchmark uses a second deterministic HMAC-SHA256 key to authenticate a witness statement that binds generation 9 to the exact H9 digest. This is a test fixture, not production PKI or a production witness design.

## Scope

The restore is modeled as an explicit database-state rollback of the verifier-local checkpoint row to a previously captured snapshot. The benchmark does not claim PostgreSQL backup systems are unsafe and does not model malicious storage, hardware rollback protection, quorum consensus, transparency-log gossip, or production disaster recovery.

## Score

Five checks, two points each, maximum 10/10.
