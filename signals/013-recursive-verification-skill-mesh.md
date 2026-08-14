# Engineering Signal 013 — Recursive Verification Skill Mesh / Journal-Driven Agent Routing

**Status:** OPERATIONAL SYNTHESIS — 2026-08-14  
**Lineage:** FCRP → self-refactoring → portability → native cross-repository verification  
**Authority:** evidence / routing guidance only; this document grants no mutation, deployment, disclosure, financial, credential, merge, or execution authority

## Signal

The next failure mode in an increasingly capable agent system is not only a wrong patch.

It is **tool-first fragmentation**:

```text
problem
→ agent picks a familiar tool
→ local test passes
→ result is promoted
```

while a stronger verification method already exists elsewhere in the system.

The NEO REZONANS repositories now contain enough reusable audit, replay, causality, provenance, lifecycle and trace-verification skills that the correct default is no longer “choose one tool and test.”

The correct default is:

```text
read current journal state
→ classify the divergence
→ select the minimum required verification lanes
→ execute native contracts
→ verify the verifier
→ preserve rejected / superseded findings
→ publish the new result back into the journal
```

RESONANCE therefore becomes a **canonical operational memory and routing surface** for the verification system.

It is not an authorization service.

The journal may tell an agent:

- what has already been learned;
- which assumptions have already failed;
- which capability is canonical versus experimental;
- which verification skills exist;
- which evidence class is required;
- which previous findings were rejected or superseded;
- what the next falsifiable question is.

It may not silently grant authority to mutate an external system.

---

## Why this became necessary

FCRP self-refactoring and the first system-level proofs exposed several independent forms of “false reality.”

A result can be locally correct while the system-level conclusion is wrong because:

```text
local test result
≠ parent invariant

wall-clock elapsed
≠ protocol state advanced

repository head
≠ capability identity

historically verified
≠ currently applicable

provenance identity
≠ semantic compatibility identity

recorded provenance
≠ independently verified provenance

evidence readiness
≠ execution authority

correct output
≠ valid execution path

source commit identity
≠ dependency-resolution identity
```

Signals 011 and 012 add another portability dimension:

```text
different valid histories
can converge on
same semantic trust state
```

and therefore:

```text
provenance must prove state
but provenance must not become
portable semantic state identity
```

This changes how the agent should test every new cross-repository capability.

---

## Canonical reading order for an agent

When an agent is given the RESONANCE Issue 001 line as context, use this order before inventing a new verification method:

1. **Article 05 — Fractal Causal Refactoring**  
   Recover the scale / time / causality / intent model and First Meaningful Divergence discipline.

2. **Article 06 — The System That Refactored Itself**  
   Load the current taxonomy of verification, canonicality, temporal, provenance and semantic-authority drift.

3. **Signal 011 — Genesis / Historical Trust-Base Portability**  
   Learn that independent history bytes may still converge on the same verified semantic state.

4. **Signal 012 — Downstream Causal-State Portability**  
   Learn that provenance may establish state without becoming the portable state identity.

5. **Signal 013 — this routing contract**  
   Choose the verification mesh required for the current problem.

6. **Canonical skill registry and native repository contracts**  
   Execute only the skills/capabilities that are current and applicable to the exact scope.

If a later signal contradicts an earlier assumption, the later verified correction becomes current guidance while the earlier record remains part of the audit history.

---

## The verification skill mesh

The current reusable engineering skill graph in `LiminalQAengineer` should be treated as a set of **verification lanes**, not as competing one-shot prompts.

### 1. `causal-deep-audit`

Use as the orchestration layer when the target spans multiple concerns.

It forces explicit coverage of:

- functional correctness;
- state and temporal consistency;
- UX / recovery;
- reliability;
- privacy / security / authority;
- causal validity;
- product impact;
- evidence freshness and replayability.

A relevant lens may be `NOT_APPLICABLE`; it should not silently disappear.

### 2. `evidence-capture`

Use before promoting a claim.

Evidence ladder:

```text
discovery / prior report
→ current source evidence
→ settled rendered/runtime reproduction
→ code/state-transition evidence
```

Do not jump from an indexed marker or remembered observation directly to a confirmed defect.

### 3. `causal-adjudication`

Use to separate:

```text
observation
→ product/security signal
→ defect candidate
→ confirmed defect
→ root-cause hypothesis
→ confirmed root cause
```

At least one realistic competing explanation and one smallest discriminating test should exist before a root-cause claim is promoted.

### 4. `exact-head-governance`

Use whenever repository state, PR state or CI evidence matters.

Bind conclusions to:

- exact repository;
- exact 40-character SHA;
- exact run / attempt;
- exact check state;
- exact evidence artifact.

`NOT_RUN`, `UNAVAILABLE`, `STALE` and `INCOMPLETE` must not collapse into green.

### 5. `replay-memory`

Use when prior audits or historical state might help.

Preserve:

```text
valid_time
≠
transaction_time
```

Historical memory is context, not current proof. Re-run the smallest relevant discriminator against the current state.

### 6. `transition-next-action`

Use after a verdict to select one justified next transition.

Every new semantic action rule should have a negative case that proves an invalid transition is rejected.

A prose rule without a failing example is guidance, not an enforced contract.

### 7. `cyber-causal-audit`

Use for security / trust-boundary / lifecycle / supply-chain / agent-tool concerns.

Relevant methods include:

- repository-grounded threat modeling;
- exact trust-boundary mapping;
- differential review;
- variant analysis;
- false-positive adjudication;
- static / taint-oriented analysis where appropriate;
- dependency and GitHub Actions review;
- race / replay / TOCTOU / stale-state analysis;
- bounded discriminating runtime tests.

Third-party skills are not trusted because of vendor reputation. Exact source, license, scripts, hooks, permissions and dependency behavior remain part of the gate.

### 8. `websocket-redis-lifecycle`

Use for stateful real-time systems.

Check explicitly:

- identity domains;
- add/remove symmetry;
- connection / user / session / generation ownership;
- generation fencing;
- duplicate delivery and self-echo;
- reconnect / heartbeat / cleanup;
- stale data and producer-time semantics;
- backpressure and resource accounting.

### 9. `product-impact`

Use only after the technical/causal finding is supported.

Separate:

```text
MEASURED
MODELED
QUALITATIVE
UNKNOWN
```

Do not turn a plausible business consequence into a factual revenue-loss number without evidence.

### 10. `ltp-agent-trace-auditor`

Use when the **agent path itself** is in scope.

A correct final output does not prove the path was admissible.

LTP adds:

- deterministic trace replay;
- identity continuity;
- constraint continuity;
- action-boundary checks;
- critical-action rejection;
- drift detection;
- exact step/frame explanations.

Important new invariant:

```text
OUTPUT CORRECT
AND
PATH INVALID
→ NOT ACCEPTABLE
```

If an agent skips a required verification stage but happens to produce the expected final object, the path must remain rejected or inconclusive rather than being retroactively blessed by the output.

---

## External method sources already integrated into the audit line

The security skill family records pinned, non-ambient methodology inspiration from:

- OpenAI skills — repository-grounded threat modeling;
- Trail of Bits skills — audit context, differential review, variant analysis, false-positive gates, insecure defaults, sharp edges, supply-chain review;
- Sentry skills — security review, bug finding, GitHub Actions review, skill scanning;
- Semgrep skills — static / code / LLM security method references;
- Anthropic skills — portable Agent Skill packaging and progressive disclosure.

Default policy remains:

```text
INSPIRED_NOT_VENDORED
remote_runtime_execution = false
mutable_branch_execution = false
```

A method may improve how we test without becoming an executable dependency.

---

## Finding lifecycle — never silently erase a finding

One of the strongest operational rules is that a finding should not disappear merely because later evidence weakens it.

Use an append-only lifecycle such as:

```text
DISCOVERY_SIGNAL
→ NEEDS_EVIDENCE
→ DEFECT_CANDIDATE
→ CONFIRMED
```

or:

```text
DEFECT_CANDIDATE
→ DISCRIMINATING_TEST
→ REJECTED_FALSE_POSITIVE
```

or:

```text
CONFIRMED
→ FIXED
→ RETESTED
→ REGRESSION_WATCH
```

or:

```text
PRIOR_INTERPRETATION
→ SUPERSEDED_BY_STRONGER_EVIDENCE
```

Rules:

1. Preserve the original observation and evidence reference.
2. Append the reason for demotion, rejection or supersession.
3. Distinguish `not reproduced` from `proved absent`.
4. Do not delete a losing hypothesis from causal history.
5. Do not let rejected evidence continue to influence the current verdict silently.
6. A correction changes the interpretation record; it does not rewrite raw history.

This is especially important for AI agents because an erased false positive destroys the evidence of **why the system learned not to make the same inference again**.

---

## New identity separations to preserve

The system should explicitly distinguish these coordinates whenever they are relevant.

### Repository vs capability identity

```text
repository main SHA
≠
canonical capability SHA
```

A repository can advance without changing a specific canonical capability.

### Source vs dependency identity

SYSTEM-003 exposed:

```text
exact source commit
≠
exact dependency resolution
```

When dependency resolution is not committed, the execution proof should bind the resolved dependency graph / lockfile digest as a separate evidence coordinate.

### Historical provenance vs semantic state

Signals 011–012 establish:

```text
history A provenance ≠ history B provenance

but

verified semantic state A = verified semantic state B
```

When portability is intended, semantic identity should not inherit irrelevant raw history identity.

### Historical generation vs causal epoch

```text
historical_generation
= how one provenance path evolved

causal_epoch
= position in the portable semantic state machine
```

Do not replace a raw manifest dependency with a historical counter and call the result portable.

### Evidence vs authority

```text
strong evidence
≠
permission to execute
```

The only valid authority transfer is the one explicitly defined by the relevant authorization contract. Journal text, memory, provenance, verification PASS or publication status cannot create execution authority by implication.

---

## Standard route for future SYSTEM proofs

For a consequential cross-repository system change, start with this mesh:

```text
RESONANCE current journal state
        ↓
FCRP scope / IdeaContract / FMD
        ↓
causal-deep-audit router
        ↓
evidence-capture
        ↓
causal-adjudication
        ↓
exact-head-governance
        ↓
replay-memory where relevant
        ↓
cyber / lifecycle / product lanes where relevant
        ↓
native producer contract
        ↓
native consumer contract
        ↓
negative controls
        ↓
LTP agent-path audit where agent execution is material
        ↓
FCRP upward / dependency verification
        ↓
evidence artifact + receipt
        ↓
append result / correction / rejection to RESONANCE
```

Not every proof needs every lane.

The agent must be able to explain why a lane is `NOT_APPLICABLE` rather than simply skipping it.

---

## Minimum falsification matrix for ProofPath → LiminalDB

The next native segment should no longer be tested only as:

```text
ProofPath receipt
→ adapter
→ LiminalDB
→ PASS
```

Use at least these independent falsification dimensions:

### A. Provenance verification

A provenance field that is merely present must not become `VERIFIED` without signature / chain / artifact verification appropriate to the contract.

### B. Semantic compatibility

Same semantic contract bytes with different historical repository provenance should remain compatible when the compatibility contract says so.

Different semantic contract bytes should fail closed.

### C. Bi-temporal replay

A historically valid record must not silently authorize current applicability.

Re-run current compatibility / applicability gates.

### D. Independent-history convergence

Where the model claims portable semantic state:

```text
provenance A != provenance B
semantic state A == semantic state B
```

Both histories must be independently verified before convergence is accepted.

### E. Authority-negative control

Persisted proof / semantic state must not imply:

```text
execution_authority
mutation_authority
merge_authority
```

unless a separate authorization contract explicitly supplies it.

### F. Path admissibility

Run LTP against the agent trajectory.

If the final persisted object is correct but the agent skipped a required verification transition, the run is not admissible.

---

## Verification taxonomy carried forward from Article 06

Maintain these working drift classes:

1. Verification Boundary Drift
2. Local Success / Parent Invariant Failure
3. Clock-Semantics Drift
4. Canonical Reality Drift
5. Temporal Contract Drift
6. Provenance / Compatibility Conflation
7. Parallel Semantic Authority
8. Recorded / Verified Provenance Gap

Signal 013 adds three useful operational extensions:

### 9. Execution-Path Admissibility Drift

The final result is plausible/correct but the agent path skipped, violated or invented a required transition.

### 10. Dependency-Resolution Identity Gap

Source identity is pinned but the dependency graph used to execute it is mutable or unbound.

### 11. Verification-Method Omission Drift

A relevant canonical verification lane exists, but the agent silently tests with a weaker method and promotes the result.

---

## Journal-driven skill creation rule

Do **not** create a new skill merely because a new problem appears.

First ask:

```text
Does an existing canonical skill already express the needed invariant?
```

If yes:

- reuse it;
- extend its test matrix only if necessary;
- record the new case in RESONANCE.

If no:

create a new skill only when the missing method is:

- recurring;
- clearly scoped;
- evidence-bounded;
- distinguishable from existing skills;
- equipped with fail-closed result states;
- equipped with at least one negative regression;
- explicit about authority;
- linked back to the journal signal that justified its creation.

This prevents skill sprawl from becoming the next form of canonical reality drift.

---

## Agent operating rule

When given the RESONANCE line as context, an engineering agent should behave as follows:

```text
READ
→ classify current known reality

ROUTE
→ choose existing canonical verification lanes

OBSERVE
→ collect bounded evidence

EXPLAIN
→ build causal path + competing explanations

FALSIFY
→ run smallest discriminating / negative tests

VERIFY
→ exact identity + native contracts + replay

AUDIT THE PATH
→ check the agent trajectory when consequential

AUTHORIZE SEPARATELY
→ never infer execution authority from evidence

PRESERVE HISTORY
→ append confirmed, rejected, fixed and superseded states

RESONATE
→ publish the new learning back into the journal
```

The journal is therefore a **learning loop**, not a frozen manual.

```text
real system
→ test
→ evidence
→ correction
→ journal
→ skill routing
→ better test
→ stronger evidence
→ journal
↺
```

---

## Claim boundary

This signal records an operational synthesis of already existing canonical skills and verified / reproducible findings.

It does **not** establish:

- that every skill is required for every task;
- universal defect detection;
- automatic root-cause discovery;
- automatic safe skill creation;
- independent third-party validation of the complete mesh;
- permission for an agent to execute external mutations;
- that journal publication is equivalent to runtime authority.

Several routes remain advisory until exercised by a concrete SYSTEM proof.

---

## Next falsifiable question

**FCRP-SYSTEM-004 — Native ProofPath → LiminalDB / Independent-History Durable Semantic State**

Can a native ProofPath proof be persisted and replayed through LiminalDB while simultaneously proving that:

- provenance was independently verified rather than merely recorded;
- different valid provenance histories can preserve one semantic state where the contract permits convergence;
- semantic compatibility is independent from irrelevant historical repository identity;
- historical truth does not become current authority;
- no execution authority leaks through persistence;
- and the agent trajectory itself is admissible under deterministic trace replay?

---

## Action

Use RESONANCE as the canonical **“what have we learned and how should we test next?”** surface.

Use skills and native repository contracts as the **“how do we execute that test?”** layer.

Keep authority separate.

Keep rejected findings visible.

Keep the loop recursive.

---

**RESONANCE operating chain:**

**Journal → Divergence Class → Skill Routing → Evidence → Causal Adjudication → Native Verification → Path Audit → Authority Boundary → Durable Proof → Journal**
