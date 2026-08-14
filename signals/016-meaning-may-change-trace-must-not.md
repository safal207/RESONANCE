# Engineering Signal 016 — Meaning May Change / Trace Must Not

**Status:** VERIFIED — 2026-08-14  
**Lineage:** FCRP → durable evidence → immutable source trace → bounded reinterpretation  
**System case:** `FCRP-SYSTEM-006`  
**Authority:** operational memory / routing guidance only; this signal grants no truth, source mutation, production persistence, executable handoff, publication, deployment, financial, credential, merge, or external-action authority

## Signal

SYSTEM-005 proved that canonical ProofPath evidence could become a restart-replayable local/test LiminalDB durable record without creating a duplicate effect or execution authority.

SYSTEM-006 tested the next architectural edge:

```text
LiminalDB durable evidence state
        ↓
RINSE immutable source trace
        ↓
canonical reflection graph
        ↓
REFLECTION_ONLY interpretation
```

The verified result is:

> **A durable source may be reinterpreted without being rewritten, replaced, promoted to truth, or converted into execution authority.**

The core parent invariant is the RINSE rule:

> **Meaning may change. Trace must not.**

## Canonical evidence

RINSE durable-source consumer:

```text
repository  safal207/rinse
merge       3be0d2ceb1440641b141cdb80c82ed118e4186dd
PR          #27
```

Independent system verification:

```text
repository  safal207/ContractGraph-QA
merge       b54173530c675083426137176cde0aed0b90853a
PR          #60
```

Exact-head subject before merge:

`d52787bb67d9bc33047e922adeffa0192d96445b`

Independent evidence artifact:

```text
artifact  9215723726
digest    sha256:a5b53c56bbb64d367b1b56ca602a0710de60f58ecc4ba9b7734782caa003c26c
```

Pinned source identities:

```text
SYSTEM-005 ancestor
efe3efe637372815bef55ec3862c49cc69244b88

LiminalDB durable consumer
61b02fc81e0cb5cf1f1ed4658ecff58f683cb728

ProofPath capability
685d50e256a5125a21f4c4584b326411caaa64ad

RINSE durable-source consumer
3be0d2ceb1440641b141cdb80c82ed118e4186dd

logical_operation_id
crossmint-public-example-001
```

## 1. Durable record identity remains source identity

RINSE does not rename the durable source.

SYSTEM-006 requires:

```text
source_trace.id
=
liminaldb-proof-durable:<durable_record_hash>
```

The reflection receives a separate deterministic RINSE identity and digest.

Therefore:

```text
durable source identity
≠
reflection identity
```

The reflection may point to the source. It may not replace it.

## 2. Reinterpretation must use one canonical interpretation authority

The SYSTEM-006 consumer does not implement a ProofPath-specific reflection engine.

Its entire interpretation path is:

```text
validate durable bundle
→ build normalized source trace
→ existing create_reflection_record()
→ existing build_reflection_graph()
```

That preserves the earlier SELF-008 result:

> **One interpretation semantics, many domain adapters.**

A new source type is not a reason to create a new interpretation authority.

## 3. Persisted evidence is not truth

The bounded RINSE statement is intentionally narrow:

```text
this canonical ProofPath verification evidence
was durably recorded and restart-replayable
```

It does **not** conclude:

```text
the represented real-world claim is therefore true
```

The reflection is created as:

```text
status = SUPPORTED_WITH_LIMITS
verdict = ACCEPT_WITH_LIMITS
```

with missing evidence that explicitly includes:

```text
production-persistence-authorization
underlying-real-world-outcome-truth
```

Thus:

```text
durable
≠ true
```

## 4. Reflection is not execution authority

SYSTEM-006 requires the canonical RINSE authority boundary:

```text
classification = REFLECTION_ONLY
source_trace_mutation_authorized = false
evidence_mutation_authorized = false
truth_authorized = false
execution_authorized = false
```

Every candidate handoff remains:

```text
execution_allowed = false
```

The durable source may influence interpretation. It does not become permission to act.

## 5. Exact source bytes remain unchanged

The independent workflow writes a real SYSTEM-005-shaped durable record, closes the writer, reopens the LiminalDB store and recovers:

- the exact AuditEvent bytes;
- the exact artifact-admission bytes;
- the durable summary and record hash.

Before RINSE interpretation, the source files are hashed.

After deterministic reflection derivation, they are hashed again.

SYSTEM-006 requires exact equality.

Therefore the downstream consumer proves:

```text
read source
→ derive interpretation
→ source bytes unchanged
```

not:

```text
read source
→ normalize by rewriting history
```

## 6. Hash consistency is not semantic contract consistency

The strongest negative control changes the source event meaning:

```text
event.details.persistence.durable_memory
false → true
```

and updates the exported source-event digest to match the changed bytes.

A consumer that checks only:

```text
bytes match digest
```

could accept the modified source.

The canonical RINSE adapter also checks the SYSTEM-005 semantic boundary and rejects it because the historical artifact event must still say:

```text
write_mode = artifact_only
durable_memory = false
```

Durability was granted later through a **separate storage admission**, not by rewriting the historical AuditEvent.

Therefore:

> **Digest-consistent does not imply contract-consistent.**

## 7. Time coordinates remain separate facts

SYSTEM-006 maps the durable source clocks into RINSE without collapsing them:

```text
valid_time_ms
→ reflection.valid_time.from

transaction_time_ms
→ reflection.recorded_time

explicit downstream review time
→ reflection.reviewed_time
```

The review time may not precede the durable recorded time.

This preserves:

```text
when the represented fact is valid
≠
when it was durably recorded
≠
when a downstream interpretation was reviewed
```

## 8. Consumer capability is not system proof

RINSE PR #27 first made the adapter canonical and green against the existing reflection core.

SYSTEM-006 did not record that self-test as sufficient system proof.

ContractGraph-QA independently rebuilt:

```text
real CGQA evidence
→ ProofPath native VALID
→ LiminalDB artifact admission
→ separate storage admission
→ durable append
→ process restart
→ exact durable replay
→ exact canonical RINSE consumer
→ deterministic reflection
→ semantic negative control
→ LTP strict/replay
→ FCRP PASS
```

The system claim therefore comes from an independent caller exercising the exact canonical consumer revision.

## 9. Absence of external review is not external approval

For ContractGraph-QA PR #60, CodeRabbit did not perform a substantive review because its rate limit was exhausted.

We did not reinterpret that absence as a green review.

Promotion instead used:

```text
FULL exact-head execution
+ zero unresolved review threads
+ explicit bounded manual diff review
+ unchanged canonical base
```

This distinction belongs in operational memory:

```text
review unavailable
≠
review passed
```

## Working taxonomy additions

Signal 016 adds these internal working names:

24. **Source-Trace / Reflection-Identity Conflation** — derived interpretation identity replaces or obscures durable source identity;
25. **Durability / Truth Conflation** — persistence of evidence is treated as proof that the represented real-world claim is true;
26. **Domain-Adapter / Interpretation-Authority Conflation** — a new source type creates a second interpretation engine instead of projecting into the canonical core;
27. **Digest-Consistency / Semantic-Contract Conflation** — matching bytes and digest are treated as sufficient despite incompatible authority semantics;
28. **Recorded-Time / Review-Time Conflation** — durable recording time is silently reused as downstream review time;
29. **Review-Unavailable / Review-Passed Conflation** — an unavailable reviewer or rate-limited review is reported as approval.

These are working engineering labels, not an external standard.

## Current verified boundary

SYSTEM-006 proves, within pinned revisions and ephemeral local/test durable state:

1. the real SYSTEM-005 durable record can be replayed and consumed by canonical RINSE;
2. the durable record hash remains the normalized RINSE source-trace identity;
3. exact source event/admission bytes remain unchanged through interpretation;
4. the existing reflection core alone creates reflection identity and digest;
5. the derived statement remains `SUPPORTED_WITH_LIMITS` / `ACCEPT_WITH_LIMITS`;
6. truth and execution authority remain false;
7. candidate handoff remains non-executable;
8. valid, recorded and reviewed time remain distinct;
9. semantic authority escalation is rejected even when the source-event digest is updated;
10. the complete trajectory is accepted by native LTP strict/replay;
11. the FCRP causal case evaluates to PASS.

## What SYSTEM-006 does not prove

Do not extend the result to:

- production persistence authorization;
- truth of the underlying incident;
- source write-back from RINSE;
- executable Kairos transitions;
- production reflection-promotion policy;
- publication authority;
- distributed replication;
- external action authority.

## Next system gate — FCRP-SYSTEM-007

The NEO REZONANS loop can now test its return path:

```text
RINSE REFLECTION_ONLY result
        ↓
RESONANCE operational memory
        ↓
append-only journal entry
        ↓
future-agent routing context
```

### Falsifiable question

Can RESONANCE ingest the exact bounded SYSTEM-006 reflection as operational memory while preserving:

- the durable source record reference;
- the RINSE reflection ID and digest;
- `REFLECTION_ONLY` / non-executable status;
- uncertainty and missing-evidence boundaries;
- append-only correction / supersession history;
- separation between publication and truth;
- separation between journal routing and execution authority;
- deterministic evidence and path replay?

The critical rule becomes:

> **Publication may preserve an interpretation. Publication must not promote it to truth or authority.**

## Core rule

```text
source trace
≠ reflection
≠ truth
≠ authority
```

and:

```text
Meaning may change.
Trace must not.
```

---

Signal 016 is operational memory and routing guidance. Native repository contracts and exact execution evidence remain the verification layer; authorization remains separate.
