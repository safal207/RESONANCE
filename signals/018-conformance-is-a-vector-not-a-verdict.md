# Engineering Signal 018 — Conformance Is a Vector, Not a Verdict

**Status:** VERIFIED — 2026-08-23  
**Lineage:** Signal 014 Persistence Frontier → Signal 015 Durability Frontier → Signal 016 Meaning May Change / Trace Must Not → Agent Runtime Conformance Matrix v0.1  
**Executable contract:** `safal207/ContractGraph-QA` PR #91, merged as `cdcedc1ba376e7aa230d652b17fc2ab546294028`  
**Authority:** operational memory / routing guidance only; this signal grants no production mutation, deployment, financial, credential, merge, certification, or external-action authority

## Signal

A runtime can replay the right answer and still expose the wrong storage guarantee.

A profile can be structurally valid and still report a failed semantic capability.

A framework can host a conformant adapter without natively providing the same guarantee.

The compact rule is:

```text
profile validity
≠
projection conformance
≠
persistence
≠
append-only evidence
≠
framework-wide safety
```

> **Conformance is a vector of bounded claims, not a scalar verdict.**

## Why this signal exists

`Witness Projection Conformance v0.1` began as a narrow eight-check contract for deterministic replay of explicit evidence.

The first source-pinned runtime benchmarks exposed an important comparison failure mode: a single score can hide where the guarantee actually comes from.

Five measured boundaries produced three distinct architectural shapes:

```text
CrewAI
native tool-event vocabulary
→ 6/8
→ explicit absence FAIL
→ deadline binding FAIL

LangGraph / AutoGen / Microsoft Agent Framework
hosted state or checkpoint boundary
→ 8/8
→ persistence PASS
→ append-only evidence requires adapter policy

OpenAI Agents SDK
restricted hosted SQLiteSession envelope
→ 8/8
→ persistence PASS
→ native append-only FAIL
→ destructive mutations PRESENT
   pop_item
   clear_session
```

The useful result is not a ranking.

The useful result is that the same semantic projection score can sit above materially different evidence-storage contracts.

## Canonical executable evidence

The current ContractGraph-QA chain is:

```text
Witness Projection Conformance v0.1
PR #77
merge 0da996c0276fbd5317835b92df48f4505bfeb9d4
        ↓
CrewAI source-pinned native-boundary benchmark
PR #79
merge d5e8c030efd5a66d193c10184d6d4d3137eddb62
        ↓
LangGraph hosted checkpoint/state benchmark
PR #80
        ↓
AutoGen hosted saved-state benchmark
PR #81
        ↓
Microsoft Agent Framework checkpoint benchmark
PR #83
merge 98880ce6e4caa037164911273351a87052ffffed
        ↓
OpenAI Agents SDK SQLiteSession benchmark
PR #86
merge b163f4b6ea99903c2ed4979cfe614bb2969bb96a
        ↓
Agent Runtime Conformance Matrix v0.1
PR #89
merge 2d729a2fdfe9d75b18d30945857cf73a63eb4477
        ↓
portable Agent Runtime Conformance Profile v0.1
PR #91
merge cdcedc1ba376e7aa230d652b17fc2ab546294028
```

The external runtime source pins recorded by the matrix are:

```text
CrewAI
crewAIInc/crewAI@f4731f5025f861c78e3af0487cc80bf5e7c64782

LangGraph
langchain-ai/langgraph@f09cfe8ffc1eeffd68f4b628ed69c30f7cad229f

AutoGen
microsoft/autogen@027ecf0a379bcc1d09956d46d12d44a3ad9cee14

Microsoft Agent Framework
microsoft/agent-framework@d9d3fb6252f7ae9e7f8104edce7266f0782a813c

OpenAI Agents SDK
openai/openai-agents-python@7f7a44f8dc0650296bd5ab6c745c9bcbaa6ac3b7
```

## Seven-axis comparison

The matrix freezes seven independent axes:

```text
projection
replay
explicit absence
deadline binding
persistence
append-only evidence
destructive mutations
```

Current measured summary:

| Runtime | Projection | Replay | Explicit absence | Deadline binding | Persistence | Append-only | Destructive mutations |
|---|---:|---:|---:|---:|---:|---:|---:|
| CrewAI | 6/8 FAIL | PASS | FAIL | FAIL | N/M | N/M | N/M |
| LangGraph | 8/8 PASS | PASS | PASS | PASS | PASS | ADAPTER | N/M |
| AutoGen | 8/8 PASS | PASS | PASS | PASS | PASS | ADAPTER | N/M |
| Microsoft Agent Framework | 8/8 PASS | PASS | PASS | PASS | PASS | ADAPTER | N/M |
| OpenAI Agents SDK | 8/8 PASS | PASS | PASS | PASS | PASS | FAIL | PRESENT |

`N/M` means not measured at that pinned boundary. It does not mean the runtime lacks the capability elsewhere.

`ADAPTER` means the substrate can host the guarantee, but the guarantee is supplied by the bounded adapter/reducer policy rather than proven as an immutable native storage contract.

## Portable profile boundary

PR #91 turns the matrix vocabulary into a portable submission contract.

A runtime can publish one source-pinned profile and evaluate it with:

```text
cgqa runtime-conformance-profile --input profile.json
```

The evaluator deliberately returns separate claims:

```text
profileValid
projectionConformant
replay
explicitAbsence
deadlineBinding
persistence
appendOnly
destructiveMutations
```

This prevents a structurally valid profile from being confused with a semantic PASS.

It also prevents an 8/8 projection result from being silently promoted into an append-only storage guarantee.

## Profile-validity rule

A valid profile means:

```text
schema recognized
AND
source pinned
AND
fields internally consistent
AND
claim boundary present
AND
evidence references present
```

It does **not** mean:

```text
referenced evidence is authentic
OR
referenced evidence is complete
OR
runtime is secure overall
OR
storage is immutable
OR
vendor endorses the result
```

The evidence references remain independently auditable claims.

## Hosted capability ≠ native guarantee

A hosted adapter result answers:

> Can this pinned substrate carry the complete witness contract without inventing facts from ambient time?

It does not answer:

> Does every application built on this runtime preserve that contract?

For LangGraph, AutoGen and Microsoft Agent Framework, the measured state/checkpoint substrate can host the witness contract, but append-only evidence behavior is still an adapter responsibility at the measured boundary.

For OpenAI Agents SDK, the distinction is even sharper:

```text
hosted projection  8/8 PASS
persistence        PASS
native Session     mutable
append-only        FAIL
```

because the native session protocol exposes destructive history operations.

## Boundary-specific FAIL ≠ framework failure

CrewAI's 6/8 result is intentionally narrow.

The measured native tool-event vocabulary can represent start / finish / error / failure, but at the pinned boundary it cannot represent the explicit observation:

```text
checked this window
observed no response
deadline was d
```

Therefore:

```text
explicit absence       FAIL
deadline bound evidence FAIL
```

The valid statement is:

> The measured native event boundary cannot express the complete witness contract.

The invalid statement is:

> CrewAI as a whole is nondeterministic or unsafe.

## Working taxonomy additions

Signal 018 adds these internal working names:

36. **Conformance-Score / Guarantee-Vector Conflation** — one aggregate score is treated as if every relevant runtime guarantee were measured;
37. **Projection / Persistence Conflation** — deterministic semantic replay is treated as proof that the evidence has a durable storage path;
38. **Persistence / Immutability Conflation** — successful save/load is treated as proof that evidence cannot later be deleted or rewritten;
39. **Hosted-Adapter / Native-Guarantee Conflation** — a guarantee enforced by a bounded adapter is attributed to the framework's unrestricted native API;
40. **Profile-Validity / Safety-Verdict Conflation** — structural and internal consistency of a conformance profile is reported as overall framework safety;
41. **Boundary-Failure / Framework-Failure Conflation** — failure of one pinned surface is generalized into a claim about the entire runtime;
42. **Evidence-Reference / Evidence-Authenticity Conflation** — presence of an evidence pointer is treated as proof that the referenced artifact is authentic and complete.

These names are working engineering taxonomy, not an external standard.

## Agent routing rule

When an agent encounters a claim such as:

```text
"Framework X passes conformance"
```

it should expand the claim before using it:

```text
Which pinned source revision?
        ↓
Which measured boundary?
        ↓
Native guarantee or hosted adapter?
        ↓
Which axes were actually measured?
        ↓
Which axes passed / failed / require adapter policy?
        ↓
Are destructive mutations exposed?
        ↓
What evidence references support the row?
        ↓
What remains explicitly unmeasured?
```

Do not compress the result back into a single safety label unless the governing contract explicitly defines and verifies that larger claim.

## Scope boundary

The current matrix and profile format do not by themselves prove:

- vendor adoption or endorsement;
- production security of any measured framework;
- authenticity or completeness of third-party evidence references;
- distributed consistency of arbitrary storage backends;
- side-effect correctness outside the measured witness contract;
- application-level correctness for arbitrary agents;
- immutable evidence storage unless the append-only axis is independently measured;
- that the current v0.1 vocabulary is a public industry standard.

The verified claim is narrower: ContractGraph-QA now has an executable, source-pinned method for keeping projection, replay, explicit absence, deadline binding, persistence, append-only evidence and destructive mutation claims separately inspectable, plus a portable profile format that fails closed on internally contradictory claims.

## Core rule

```text
one green score
        ≠
one universal guarantee
```

Instead:

```text
claim
  ↓
source pin
  ↓
measured boundary
  ↓
independent capability axes
  ↓
evidence references
  ↓
explicit unmeasured space
```

> **A useful conformance result says exactly what passed, where it passed, what supplied the guarantee, and what was not measured.**

---

Signal 018 is operational memory and routing guidance. ContractGraph-QA remains the executable verification layer for this signal; publication in RESONANCE does not itself certify any runtime or authorize external action.