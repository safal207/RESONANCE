# Engineering Signal 012 — Semantic Reference vs Occurrence Reference

**Status:** architecture hypothesis grounded in public shipped proof structure; outcome-side occurrence binding still requires direct falsification  
**Observed:** 14 Aug 2026  
**Scope:** causal/provenance binding across decision semantics, concrete signed decision issuance, external temporal anchoring, execution, and observed outcome  
**External context:** [`crewAIInc/crewAI#4877`](https://github.com/crewAIInc/crewAI/issues/4877) and public independent Baby Blue / OSuite proof fixtures  
**Not:** a claim that Baby Blue, CrewAI, OSuite, or any referenced implementation is incorrect

## Main signal

> **A reference to the semantic identity of a decision is not necessarily a reference to the concrete historical occurrence of that decision.**

This is the same class of distinction as:

```text
logical_operation_id != execution_id
```

A logical operation can remain the same across several execution attempts. Likewise, a semantic decision can remain the same across several concrete issuances of that decision.

The stronger causal chain therefore needs to distinguish:

```text
decision semantics
        !=
decision occurrence
```

or, more generally:

```text
semantic identity != historical occurrence
```

## Why this surfaced

A public Baby Blue proof fixture exposes two distinct identifiers:

```text
decision_ref
signed_event_id
```

The `decision_ref` is derived from a declared semantic preimage containing fields such as:

```text
artifact_hash
artifact_type
policy_version
verdict
source_class
vantage_limitation
related_decision_ref
intended_audience
...
```

The concrete signed Nostr event is a different object. Its event id commits to the full signed event content, including fields outside the `decision_ref` preimage.

Public fixture:

- [`OndCo/Agent-Action-Boundary-Benchmark` proof verification](https://github.com/OndCo/Agent-Action-Boundary-Benchmark/blob/7e95eb00ce887c665d41ea7a94de6349a371bf7c/examples/baby-blue-github-saas-run/live-2026-08-11/proof-verification.json)
- [`OndCo/Agent-Action-Boundary-Benchmark` packet](https://github.com/OndCo/Agent-Action-Boundary-Benchmark/blob/7e95eb00ce887c665d41ea7a94de6349a371bf7c/examples/baby-blue-github-saas-run/live-2026-08-11/packet.json)

The same packet carries both a semantic decision reference and a concrete signed event reference.

That separation is useful and appears intentional.

## Decision identity and issuance identity answer different questions

```text
decision_ref
```

answers approximately:

> **What decision, under what semantic decision inputs, was made?**

while:

```text
signed_event_id
```

answers approximately:

> **Which concrete signed issuance of that decision is this?**

A verifier may need both.

## Temporal precedence makes the distinction load-bearing

The distinction becomes security-relevant when a protocol claims:

```text
authorization existed before execution
```

A semantic hash alone does not establish historical precedence.

Baby Blue's public description of its OpenTimestamps path explicitly anchors the **signed event id** as the timestamped digest. That is the concrete historical occurrence, not merely the semantic `decision_ref`.

This is the correct shape for precedence:

```text
decision semantics
        ↓
signed decision occurrence
        ↓
external temporal anchor
        ↓
execution
```

The external anchor establishes that a particular decision occurrence existed no later than a verifiable time.

## The new question on the outcome side

The public `verdict_outcome` discussion reports:

```text
cites_decision_ref
```

and maps it to the proposed portable:

```text
pre_action_decision_ref
```

This establishes a semantic link from outcome to decision.

The still-open question is narrower:

> **Does the outcome also bind to the exact concrete signed/anchored decision occurrence that existed before execution, or only to the semantic decision identity?**

This is a question, not a bug claim.

There may already be another field or proof edge that provides this binding. If so, the architecture is stronger when that edge is explicit and independently recomputable.

## Falsification experiment

Construct two concrete issuances with the same semantic decision identity:

```text
same semantic decision inputs
            │
            ├── issuance E1
            │     decision_ref = D
            │     signed_event_id = E1
            │     externally anchored before execution
            │
            └── issuance E2
                  decision_ref = D
                  signed_event_id = E2
                  issued later or in another context
```

Then publish or evaluate an outcome receipt containing only:

```text
cites_decision_ref = D
```

Ask an independent verifier:

> Which concrete issuance authorized the execution whose outcome is being reported?

### Pass condition

The verifier can derive, without trusting the ledger operator, a unique chain such as:

```text
outcome receipt
  → concrete execution
  → concrete pre-action decision occurrence E1
  → external precedence anchor
  → semantic decision D
```

### Fail / ambiguous condition

The verifier can establish only:

```text
outcome
  → semantic decision D
```

while both E1 and E2 remain compatible with the receipt.

That would mean semantic authorization is bound, but historical authorization occurrence is not uniquely bound.

## Minimal portable causal spine

A portable receipt can keep these identities deliberately separate:

```text
logical_operation_id
execution_id / attempt_id

pre_action_decision_ref
pre_action_decision_event_ref
pre_action_anchor_ref

observed_outcome
outcome_observer_id
outcome_observation_event_ref
outcome_evidence_ref
```

The exact field names are not the point. The decomposable responsibilities are.

### Responsibility split

| Element | Question answered |
|---|---|
| `logical_operation_id` | Which semantic operation is this? |
| `execution_id / attempt_id` | Which concrete execution attempt occurred? |
| `pre_action_decision_ref` | What semantic authorization decision applied? |
| `pre_action_decision_event_ref` | Which concrete decision issuance is claimed? |
| `pre_action_anchor_ref` | What proves that issuance existed before execution? |
| `outcome_observation_event_ref` | Which concrete observation occurrence produced the outcome claim? |
| `outcome_evidence_ref` | What evidence supports that observation? |

## General invariant

The broader invariant is:

```text
semantic identity != occurrence identity
```

and it applies recursively:

```text
intent semantics != intent event

decision semantics != decision issuance

logical operation != execution attempt

outcome class != observation event

evidence type != concrete evidence artifact
```

A trustworthy causal graph should make it possible to traverse from semantic identity to the exact historical occurrences that instantiated it.

## Why a signed full payload does not remove the distinction

A concrete proof event can cryptographically commit to metadata that is not part of the semantic `decision_ref` preimage.

That is useful: it prevents silent modification of that concrete proof event.

But it does not make `decision_ref` and `event_id` interchangeable.

They intentionally carry different identity semantics:

```text
decision_ref = semantic equivalence class

event_id = concrete signed occurrence
```

The question for downstream receipts is therefore not whether the event is signed. It is whether the downstream causal edge selects the correct identity level for the claim being made.

## Mutation tests

A portable conformance fixture should include at least these mutations:

### M1 — same semantics, different issuance

Keep every `decision_ref` preimage field unchanged but generate a second valid signed decision event.

Expected:

```text
decision_ref same
event_ref different
```

An outcome receipt claiming pre-action precedence should not treat the two occurrences as interchangeable unless both satisfy the same required temporal/binding conditions.

### M2 — late re-issuance

Create an otherwise semantically equivalent decision occurrence after execution.

Expected:

- semantic decision equality may still hold;
- pre-action precedence must fail for the late occurrence.

### M3 — outcome reference downgrade

Start with a receipt bound to both `decision_ref` and concrete `decision_event_ref`; remove the occurrence reference.

Expected:

- semantic linkage remains;
- occurrence-level / precedence assurance degrades explicitly rather than silently retaining the same verification class.

### M4 — wrong anchored occurrence

Provide two same-semantic decision events, anchor only one before execution, but point the outcome receipt at the other.

Expected:

- semantic comparison passes;
- occurrence/precedence verification fails.

### M5 — replay across execution attempts

Reuse the same semantic decision across two execution attempts where only one attempt was actually covered by the concrete authorization occurrence.

Expected:

- `logical_operation_id` can remain stable;
- `execution_id` changes;
- authorization-to-execution binding must identify the covered attempt rather than infer coverage from semantic equality.

## Verification depth interpretation

This distinction also refines verification depth.

A chain such as:

```text
outcome
  → decision_ref
```

may be semantically deep but historically shallow if the verifier cannot descend to the concrete pre-action occurrence and its external precedence anchor.

The stronger path is:

```text
outcome
  → execution occurrence
  → decision occurrence
  → semantic decision
  → external anchor
```

Each edge answers a different claim.

## Relationship to Signal 008

Signal 008 separated:

```text
decision provenance != outcome provenance
```

and then:

```text
observer identity != observer vantage != decision-vantage resolution state
```

Signal 012 adds an orthogonal dimension:

```text
semantic reference != occurrence reference
```

Together they produce a stronger causal model:

```text
INTENT
  ↓
semantic operation
  ↓
decision semantics
  ↓
decision occurrence
  ↓
external temporal anchor
  ↓
execution occurrence
  ↓
outcome semantics
  ↓
observation occurrence
  ↓
observer + actual vantage
  ↓
evidence artifact
  ↓
verification
```

## Implementation guidance

Do not add fields merely because they look complete.

For any claimed occurrence-level field, require a conformance test that proves the runtime can actually use it to distinguish histories that share the same semantics.

A useful generic test rule is:

> **If two histories are semantically equal but causally different, an occurrence-sensitive verification result must be able to distinguish them.**

That keeps the schema from collapsing concrete history back into semantic labels.

## Research question

> **When a post-action receipt cites a pre-action authorization, can an independent verifier prove which exact signed and externally anchored authorization occurrence preceded the concrete execution — rather than only proving that an equivalent semantic decision exists?**

If the answer is yes, the causal chain has occurrence-level binding.

If the answer is no, the chain may be semantically consistent while still underdetermining its actual history.
