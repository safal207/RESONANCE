# Engineering Signal 014 — Persistence Frontier / Native Consumer Acceptance Is Not Durable State

**Status:** VERIFIED — 2026-08-14  
**Lineage:** FCRP → self-refactoring → journal-driven skill routing → native cross-repository verification  
**System case:** `FCRP-SYSTEM-004`  
**Authority:** evidence / routing guidance only; this signal grants no database-write, deployment, disclosure, financial, credential, merge, or execution authority

## Signal

The first native `ProofPath → LiminalDB` system test changed the NEO REZONANS model before it changed persistence code.

The previous shorthand said:

```text
ProofPath
   ↓
LiminalDB
   ↓
durable verified state
```

The canonical repositories did not yet justify that statement.

What could actually be proved was narrower:

```text
native ProofPath verification
        ↓
exact evidence receipt
        ↓
dedicated LiminalDB AuditEvent projection
        ↓
canonical LiminalDB artifact validator
        ↓
dry-run compatibility PASS
        ↓
native LTP strict trace + replay
        ↓
STOP BEFORE PERSISTENCE
```

Therefore the current canonical boundary is:

```text
ProofPath
→ verified evidence
→ LiminalDB-compatible artifact
→ persistence frontier
```

not:

```text
ProofPath
→ durable LiminalDB state
```

Core rule:

> **Native consumer acceptance is not durable persistence.**

This is not a wording preference. It is a distinct state-transition boundary that must receive its own evidence before the system may cross it.

---

## Why Signal 013 changed the experiment

Signal 013 established a journal-driven rule:

```text
read journal
→ classify divergence
→ route to existing skills
→ run native contracts
→ verify verifier / path
→ authorize separately
→ write learning back to journal
```

Following that rule prevented two shortcuts.

### Shortcut rejected: reuse Lotus semantics

LiminalDB already had a canonical Lotus v0.2 artifact contract, but that contract is intentionally specific:

```text
actor  = liminalqa-lotus
action = lotus.finding.observed
```

A ProofPath SCIG verification is a different fact.

Relabeling ProofPath evidence as a Lotus finding merely to reuse an existing green validator would have produced a structurally convenient but semantically false result.

The missing component was not a new reasoning skill. Existing causal, evidence, exact-head, replay, transition and LTP lanes already covered the methodology.

The missing component was a **native consumer interface**.

Therefore the repair was:

```text
new skill                    NO
new ProofPath consumer       YES
```

LiminalDB now has a dedicated canonical artifact profile:

```text
actor  = proofpath-scig-native-verifier
action = proofpath.scig.verification.observed
schema = liminaldb-proofpath-audit-event-v0.1
```

Canonical LiminalDB import-contract commit:

`00580ff097dee61b45ad3c8a3c36ae5f548f572d`

AuditEvent semantic contract blob:

`fd733971aaae089df770062bcf7f2c2d6d19ca1d`

The contract remains intentionally:

```text
mode                      = dry_run
write_performed           = false
durable_memory_accepted   = false
live_ingestion_performed  = false
```

---

## Immutable proof chain

### ContractGraph-QA SYSTEM-004

- PR: `safal207/ContractGraph-QA#57`
- canonical merge: `be860d7a6ca089a4514d12a8108d27873b04dfb9`
- exact green head before merge: `08b528352b28d3831711ff0f1bddccdecff3bf49`

### Native identities

ProofPath canonical SCIG capability:

`685d50e256a5125a21f4c4584b326411caaa64ad`

LiminalDB ProofPath artifact-import contract:

`00580ff097dee61b45ad3c8a3c36ae5f548f572d`

LTP native trace inspector revision:

`fc58072d301a487c09227ea09004dc8e99676370`

### Exact-head verification lanes

All six lanes passed on the final SYSTEM-004 head:

- NEO REZONANS Native ProofPath LiminalDB Gate — `31781695579` — SUCCESS
- FCRP v0.2 Contract Gate — `31781695600` — SUCCESS
- CI — `31781695545` — SUCCESS
- Product — `31781695604` — SUCCESS
- Finding report — `31781695612` — SUCCESS
- Portability — `31781695629` — SUCCESS

SYSTEM-004 evidence artifact:

- artifact ID: `9211945351`
- name: `neo-rezonans-system-004-57`
- digest: `sha256:ad4c484d53e6b519625d9030cba9e2a7635161b5e0fcf24f8205b5177cc79106`

The native gate independently executed the relevant repositories rather than trusting a shared narrative artifact.

---

## Native path

The successful final path was:

```text
ContractGraph-QA provider evidence
        ↓
exact local replay
        ↓
ProofPath SCIG projection
        ↓
current ProofPath capability manifest
        ↓
canonical proofpath.scig.v0.1 bytes
        ↓
generated + evidence-bound Cargo.lock
        ↓
native Rust proofpath-scig
        ↓
RESULT VALID
        ↓
deterministic ProofPath native receipt
        ↓
ProofPath-specific LiminalDB AuditEvent
        ↓
canonical LiminalDB validator
        ↓
mode = dry_run
write_performed = false
        ↓
LTP strict inspector
        ↓
LTP deterministic replay
        ↓
stop-before-persistence
```

This path preserves one native logical operation identity:

`crossmint-public-example-001`

---

## Identity inheritance: do not rename reality to fit the diagram

The first SYSTEM-004 run failed before ProofPath native execution.

The new fixture had been assigned a visually convenient global identity:

```text
lop:neo-rezonans:heartbeat:001
```

But the existing native SYSTEM-003 source case already had its own exact logical operation:

```text
crossmint-public-example-001
```

The initial assertion failed because the system was trying to continue one native execution under a different semantic operation identity.

The fix was **not** to rewrite the real source evidence.

The child segment inherited the existing native identity.

New rule:

> **Cross-system continuation must inherit the logical operation identity of the real upstream execution unless an explicit, separately modeled operation-mapping contract exists.**

In compact form:

```text
pretty global ID
        ≠
actual upstream logical operation
```

and:

```text
continuation
→ inherit identity
```

not:

```text
continuation
→ rename identity for diagram consistency
```

This is a concrete form of semantic continuity protection.

---

## Output correctness is still not path admissibility

After the identity repair, the experiment passed:

- native ProofPath verification;
- ProofPath receipt construction;
- LiminalDB AuditEvent projection;
- canonical LiminalDB artifact validation;
- construction of a four-frame agent trajectory.

Then the first LTP run returned red.

At that moment, a tempting interpretation was:

```text
LTP rejected the agent path
```

That interpretation was wrong.

The exact evidence showed the wrapper invocation was:

```text
pnpm -w ltp:inspect -- trace ...
```

The package script already forwarded arguments directly to `inspect.ts`, so the native tool received the literal separator `--` as its first argument.

It failed with:

```text
Missing command (trace | replay | explain)
```

The strict inspector had not yet parsed the trace.

Therefore the hypothesis:

```text
agent trajectory invalid
```

was rejected.

The supported finding was:

```text
wrapper invocation invalid
```

After changing only the invocation to:

```text
pnpm -w ltp:inspect trace ...
pnpm -w ltp:inspect replay ...
```

with strict mode preserved, both native LTP inspection and replay passed.

New rule:

> **A verifier transport or wrapper failure is not evidence that the object being verified failed its semantic contract.**

Formally:

```text
verifier invocation failed
        ≠
verified subject rejected
```

This is the same discipline as distinguishing:

```text
FAILED_BEFORE_CHECK
REJECTED_BY_CHECK
UNKNOWN_AFTER_CHECK
```

rather than compressing all three into `FAIL`.

---

## Finding lifecycle: preserve the losing hypothesis

Signal 013 requires append-only finding history.

SYSTEM-004 provides two concrete examples.

### Finding A — logical-operation mismatch

```text
OBSERVATION
new segment ID differs from upstream native ID
        ↓
CAUSE CONFIRMED
manually invented child operation identity
        ↓
FIX
inherit crossmint-public-example-001
        ↓
RETEST
PASS
```

### Finding B — apparent LTP path rejection

```text
OBSERVATION
LTP lane red
        ↓
INITIAL HYPOTHESIS
trace/path invalid
        ↓
DISCRIMINATING EVIDENCE
native inspector reports Missing command before trace parsing
        ↓
REJECTED HYPOTHESIS
path invalid not established
        ↓
SUPPORTED CAUSE
CLI wrapper invocation invalid
        ↓
FIX
remove literal separator
        ↓
RETEST
strict inspect + replay PASS
```

The rejected interpretation remains useful because it teaches future agents what **not** to infer from the same failure shape.

---

## Canonical Reality Drift occurred during the experiment

SYSTEM-004 initially branched from SYSTEM-003 merge:

`0219a22cb403f3d1fc621f2a1a0a2b508355d4ea`

While the experiment was being built, `ContractGraph-QA/main` advanced to:

`6baf9e8396ad216556a4e932356b2aab080aaffe`

The new canonical commit added an independent FCRP Core v0.3 / credential-boundary slice and did not overlap the six SYSTEM-004 files.

Silently retaining the stale base would have recreated Canonical Reality Drift.

Silently force-rebasing away the experimental history would have weakened provenance.

Instead a two-parent reconciliation commit was built:

`2812659ac2f767e506221acd08e267a6cd17901b`

with:

```text
parent 1 = existing SYSTEM-004 research history
parent 2 = current canonical main
```

and a tree equal to:

```text
current canonical main
+ exact SYSTEM-004 six-file delta
```

The branch was then fast-forwarded without force.

New operational rule:

> **Repository advancement requires reconciliation or revalidation, not suppression of the stale-base fact.**

The workflow was also corrected to separate:

```text
SYSTEM_003_ANCHOR
```

from:

```text
EXPECTED_CURRENT_PR_BASE
```

because lineage identity and current integration base are different facts.

---

## The persistence frontier

SYSTEM-004 makes several boundaries explicit.

### 1. Consumer compatibility is not a write

```text
artifact accepted by validator
        ≠
state mutated
```

### 2. A write is not durability

Even a future successful append would not alone prove:

- restart recovery;
- journal/index atomicity;
- retention;
- rollback semantics;
- cross-process visibility;
- crash safety.

Therefore:

```text
write success
        ≠
durable state
```

### 3. Durability is not truth

Persisting an evidence object does not transform the underlying claim into universal truth.

```text
stored evidence
        ≠
truth
```

### 4. Durability is not authority

Even correctly persisted, independently verified evidence must not silently gain permission to act.

```text
durable evidence
        ≠
execution authority
```

The full separation is:

```text
proof
≠ truth
≠ consumer compatibility
≠ write
≠ durability
≠ persistence authority
≠ execution authority
```

Each arrow requires its own contract.

---

## Identity model after SYSTEM-004

The native segment now keeps these coordinates separate:

```text
logical_operation_id
    = semantic operation continuity

ProofPath capability commit
    = verifier capability identity

ProofPath Cargo.lock digest
    = dependency-resolution identity

SCIG digest
    = evidence-object identity

ProofPath native receipt digest
    = producer verification receipt identity

LiminalDB repository commit
    = consumer snapshot provenance

LiminalDB AuditEvent Git blob
    = semantic compatibility identity

LTP repository commit + pnpm lock
    = path-verifier implementation/dependency identity
```

No coordinate is allowed to impersonate another.

This composes earlier journal laws:

```text
repository head ≠ capability identity
source commit ≠ dependency-resolution identity
provenance identity ≠ semantic compatibility identity
historical truth ≠ current authority
output correct ≠ path admissible
```

---

## What SYSTEM-004 proves

Within the tested bounded synthetic/public-contract scenario and pinned revisions:

- the actual upstream logical operation identity survives the native continuation;
- native ProofPath verification precedes LiminalDB projection;
- the ProofPath capability is canonical and default-consumable at the observed manifest state;
- ProofPath dependency resolution is made explicit and bound rather than left ambient;
- the ProofPath-native receipt is bound to exact SCIG bytes;
- LiminalDB has a dedicated ProofPath consumer profile rather than a relabeled Lotus profile;
- the exact current LiminalDB AuditEvent contract blob is used as semantic compatibility identity;
- the canonical LiminalDB consumer accepts the event only as an artifact-only dry run;
- no live ingestion or durable-memory acceptance is claimed;
- no execution, mutation or persistence authority crosses the boundary;
- native LTP strict inspection and deterministic replay accept the final four-stage trajectory;
- the trajectory terminates explicitly at `stop-before-persistence`;
- FCRP-SYSTEM-004 returns PASS with `mutationAuthorized=false`.

---

## What it does not prove

SYSTEM-004 does **not** establish:

- live LiminalDB journal append;
- durable storage after process restart;
- `valid_time` / `transaction_time` preservation through storage and replay;
- tenant or namespace isolation for ProofPath ingestion;
- idempotent durable append semantics;
- transaction atomicity between journal, indexes and acknowledgement;
- crash recovery from a partially committed ingestion;
- rollback / rejection semantics after partial failure;
- retention, compaction or archival safety;
- independent organizational replication;
- universal truth of arbitrary ProofPath claims;
- persistence authority;
- execution authority.

The Crossmint input remains a bounded public-contract/synthetic verification scenario, not a claim that a production Crossmint system was tested or found vulnerable.

---

## New working taxonomy additions

Signal 014 adds several named failure shapes to the operational taxonomy. These are internal working terms, not industry standards.

### 12. Persistence-Frontier Collapse

A system treats consumer acceptance, a write, durable state and authority as one transition.

```text
accepted
→ assumed persisted
→ assumed durable
→ assumed actionable
```

### 13. Logical-Operation Renaming Drift

A downstream segment assigns a new operation identity to an existing native continuation without an explicit operation-mapping contract.

### 14. Verifier-Invocation / Subject-Verdict Conflation

A verifier fails to start or parse its command, but the failure is reported as if the subject itself was semantically rejected.

### 15. Integration-Base / Causal-Ancestor Conflation

One SHA is used both as the historical causal anchor and as the required current integration base after the repository has advanced.

These classifications should be used only when their exact causal shape is supported.

---

## Journal-driven routing update

For a future evidence-to-memory boundary, the default route is now:

```text
RESONANCE journal
        ↓
recover prior divergence classes
        ↓
exact-head / capability identity
        ↓
producer-native verification
        ↓
consumer-native compatibility
        ↓
negative authority controls
        ↓
path / trace admissibility
        ↓
STOP at unproven persistence frontier
        ↓
only then design persistence experiment
```

Do not create a new skill merely because persistence is now the next question.

The current skills already provide the required reasoning and audit lanes. The next missing capability is an explicitly bounded **native persistence contract**, not another meta-skill.

---

## Next falsifiable question

### FCRP-SYSTEM-005 — Durable Proof Ingestion v0.1

Can an explicitly authorized **local/test** LiminalDB ingestion path take the currently accepted ProofPath artifact across the persistence frontier and reproduce it after restart while preserving:

```text
logical_operation_id
producer provenance
consumer contract identity
valid_time
transaction_time
idempotent append identity
zero execution-authority escalation
```

and fail closed on:

```text
duplicate event
stale event
incompatible contract
namespace mismatch
partial transaction
ack-before-durable-commit
restart before index update
rollback-required ingestion
replayed old authority
```

Minimum independent lanes should include:

1. exact source + consumer identity;
2. local/test-only persistence authorization;
3. namespace / tenant isolation;
4. idempotent durable append identity;
5. journal transaction atomicity;
6. `valid_time` / `transaction_time` preservation;
7. process restart and deterministic replay;
8. crash / partial-commit recovery;
9. negative stale / duplicate / incompatible cases;
10. LTP path admissibility;
11. zero evidence-to-execution authority escalation;
12. FCRP upward verification.

Until those conditions are proved, the system map must continue to stop at:

```text
LiminalDB-compatible artifact
→ persistence frontier
```

---

## Operational memory rule

This signal is intended to be read by future engineering agents before they continue the NEO REZONANS system line.

The agent should carry forward not only the final PASS, but also:

- why Lotus reuse was rejected;
- why the logical operation ID was corrected;
- why the first LTP red did not establish path failure;
- why repository-base drift required reconciliation;
- why artifact acceptance does not permit durable-state language;
- what exact evidence is still missing before SYSTEM-005.

That is the purpose of the journal:

> **Preserve not only what the system believes now, but the causal evidence for why earlier interpretations lost.**

---

**RESONANCE operational chain:**

**Journal → Divergence → Skill Routing → Native Evidence → Counterfactual → Path Verification → Authority Boundary → Canonical Result → Journal**
