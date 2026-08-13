# Who Saw the Outcome?

**Article ID:** I001-RN-OUTCOME-PROVENANCE  
**Deck:** The missing provenance layer after an AI agent acts  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-13  
**Languages:** EN  
**Canonical identity:** Issue 001 · The Age of Agents · Trust / Verification

---

## Signal

AI-agent safety is usually framed around a pre-action question:

> Was the agent allowed to do this?

That question matters. It is not enough.

Once an agent touches money, code, infrastructure, data, permissions, or another consequential system, a second question becomes equally important:

> Who says what actually happened?

A public architecture discussion around CrewAI's proposed `GuardrailProvider` exposed a useful convergence. A RESONANCE causal-provenance proposal was compared against an independently developed, already-shipped `verdict_outcome` mechanism. The comparison found substantial agreement on the separation between decision provenance and outcome provenance — and one concrete missing axis.

The shipped mechanism already classified **how** an outcome was established. It did not separately identify **who** observed it or **from what vantage**.

That distinction looks small in a schema.

It is large in a trust system.

---

## The authorization trap

Suppose an agent asks to transfer funds.

A guardrail evaluates the proposed action and returns `ALLOW`.

The transfer API is called. A response arrives. The agent reports success.

What, exactly, has been proven?

Not much beyond the authorization itself.

```text
proposed action
      ↓
pre-action decision
      ↓
ALLOW
      ↓
execution attempt
      ↓
?
```

A valid authorization can prove that a proposed action satisfied a policy at a particular moment. It does **not** prove that the action happened, happened once, settled correctly, reached the intended state, or was independently observed.

The post-action leg needs its own evidence.

---

## Decision provenance is not outcome provenance

The core architectural boundary is simple:

```text
decision_provenance != outcome_provenance
```

The two records may share vocabulary. They should not share identity by assumption.

A decision issuer might be:

- an in-process policy engine;
- an external guardrail service;
- a human approver;
- a governance quorum;
- an independent verifier.

An outcome observer might instead be:

- the agent itself;
- the tool provider;
- an internal ledger;
- a blockchain RPC endpoint;
- a settlement network;
- an external auditor;
- a recomputation from public bytes.

Those are different roles. Treating them as one trust domain lets a system silently grade its own homework.

---

## Four questions a consequential action should answer

A portable causal record should preserve four separate questions.

### 1. Was the action authorized?

Which policy, authority, evidence, and decision allowed or denied the proposed operation?

### 2. Is the later outcome bound to the same operation?

Does the outcome refer to the same logical operation and concrete execution attempt that the guardrail evaluated?

Retries make this distinction essential. A stable logical-operation identity may span several concrete attempts; an execution identity should identify one attempt.

### 3. What outcome was observed?

Did the operation settle, fail, remain uncertain, partially apply, roll back, duplicate, or produce another state?

### 4. Who observed it, from what vantage, against what evidence?

This is the provenance layer most systems still compress too aggressively.

The observer is not the evidence class.

The vantage is not the observer.

The evidence mechanism is not the verdict.

Each answers a different question.

---

## `source_class` is necessary — and insufficient

Imagine two outcome records:

```yaml
source_class: attested
outcome_observer_id: verifier-A
outcome_vantage: ethereum_rpc
```

and:

```yaml
source_class: attested
outcome_observer_id: wallet-provider
outcome_vantage: internal_ledger
```

Both may be `attested`.

They are not equivalent observations.

One may see public chain state. The other may see a provider's internal accounting state. Either can be useful. Their evidentiary meaning is different.

This gives a compact rule:

> **`source_class` tells us how the outcome was established. `observer_id` and `vantage` tell us who observed it and from where.**

If those dimensions are collapsed, a verifier cannot cleanly reason about independence, blind spots, or conflicting observations.

---

## The minimal outcome-provenance receipt

A useful portable receipt does not need to become a giant ontology.

A deliberately small spine could look like this:

```yaml
logical_operation_id: op-123
execution_id: attempt-2
pre_action_decision_ref: sha256:...
observed_outcome: settled
outcome_provenance:
  source_class: attested
  observer_id: verifier-A
  vantage: ethereum_rpc
  observation_basis: on-chain-settlement
  evidence_ref: sha256:...
observed_at: 2026-08-13T00:00:00Z
```

The point is not the exact field names.

The point is that a third-party checker can reconstruct the causal claim:

```text
intent
  ↓
decision
  ↓
authorization provenance
  ↓
execution
  ↓
observed outcome
  ↓
observer
  ↓
vantage
  ↓
evidence
  ↓
verification
```

This is a causal spine rather than a vendor-specific log shape.

---

## Why the independent convergence matters

The interesting part of the CrewAI thread was not agreement in the abstract.

An external implementer compared the proposal against a shipped `verdict_outcome` mechanism and reported that several boundaries had already emerged independently:

- the outcome carries its own `source_class`;
- outcome `source_class` is separate from decision-side `source_class`;
- the outcome cites the earlier decision;
- the observation mechanism travels with the observation;
- authorization and outcome evidence are separate claims;
- a binding receipt should not silently claim independent execution replay.

Then the comparison exposed a gap in the shipped model:

- no distinct outcome observer identity;
- no distinct outcome vantage beyond the evidence class.

That is stronger than two people liking the same diagram.

It is a small example of **architecture becoming more precise through independent implementation comparison**.

The public sequence is inspectable:

```text
provider-neutral causal proposal
        ↓
comparison against shipped mechanism
        ↓
field-level convergence
        ↓
missing observer/vantage axis
        ↓
separate extension logged
```

The claim boundary matters: this is **not** CrewAI adoption, endorsement, certification, or proof that either implementation is correct. It is a public, falsifiable engineering convergence that generated a concrete next test.

---

## The fifth schema edit is not always the right next move

There is another lesson in the exchange.

The external implementer explicitly declined to patch the shipped schema immediately. Their mechanism had already gone through multiple bug-fix rounds, and adding new provenance fields reactively would create another moving target.

That restraint is good engineering.

A discovered gap should first become a **testable boundary**.

For observer/vantage provenance, the next conformance layer should distinguish at least:

1. same source class, different observer;
2. same observer, different vantage;
3. missing observer identity;
4. missing or ambiguous vantage;
5. evidence mechanism incompatible with the claimed vantage;
6. two observers reporting conflicting outcomes;
7. self-observation incorrectly promoted to independent observation.

Only then should a schema extension be treated as mature enough to standardize.

---

## Causal model

### Safe path

```text
intent
  ↓
authorization decision
  ↓
execution binding
  ↓
outcome observation
  ↓
observer identity + vantage
  ↓
evidence
  ↓
independent verification
```

### Failure path

```text
execution
  ↓
"success"
  ↓
source_class only
  ↓
observer identity unknown
  ↓
vantage unknown
  ↓
trust-domain ambiguity
  ↓
claim promoted beyond evidence
```

The failure is not necessarily a false outcome.

The failure is that the system cannot tell a reviewer **what kind of knowledge the outcome claim actually represents**.

---

## Alternative explanations

Several weaker interpretations should remain possible.

### The field gap may be integration-specific

Some systems may already encode observer identity and vantage elsewhere in their telemetry or evidence objects. A portable receipt would still need to make that relationship explicit enough for an external verifier to follow.

### Vantage may be derivable from evidence

Sometimes the evidence mechanism strongly implies a vantage. But implicit derivation becomes fragile when multiple providers expose similar evidence through different trust paths. Explicit provenance reduces ambiguity.

### More fields can create complexity without more truth

Correct. A schema should not grow merely because another dimension can be named. The test is whether the dimension changes a verification decision under realistic counterexamples. Observer and vantage appear to pass that test because two observations with the same class can have materially different independence and visibility.

---

## Why this matters for agent payments

The issue becomes concrete when an agent can move value.

Consider a programmable wallet with a spending policy.

The policy service says the transaction was allowed. The wallet provider says the debit succeeded. A chain observer says the settlement reverted. A webhook says `completed`. The accounting ledger remains unchanged.

There is no single useful label called `verified=true` for that situation.

A serious verifier needs to ask:

- which action was authorized;
- which execution attempt each record refers to;
- which observer produced each outcome claim;
- which vantage each observer had;
- what evidence each claim rests on;
- which invariants should hold across API, ledger, webhook, chain, and audit state.

That is where outcome provenance stops being metadata and becomes financial control infrastructure.

---

## Why this matters beyond payments

The same pattern appears anywhere agents create durable consequences.

**Code agents:** Did the patch actually merge, or did the agent only observe a local branch?  
**Infrastructure agents:** Did the deployment reach the target environment, or only the orchestrator's desired state?  
**Data agents:** Did a write commit to the source of record, or only to a replica/cache?  
**Security agents:** Was a credential revoked at the authority, or only marked revoked in a local control plane?  
**Scientific agents:** Was a result independently reproduced, or merely re-reported from the originating pipeline?

The invariant is the same:

> The consequence needs a witness, and the witness needs provenance.

---

## First-order implication

Guardrail interfaces should leave room for a provider-neutral causal binding between the pre-action decision and the post-action outcome.

That does **not** require the framework to own the verifier, the ledger, or the evidence substrate.

It requires the framework to preserve enough identity for another verifier to join the records correctly.

---

## Second-order implication

A market is likely to form around independent observation and verification of agent consequences.

The valuable layer may not be another agent framework. It may be infrastructure that can answer, across heterogeneous systems:

```text
What was intended?
What was authorized?
What executed?
What changed?
Who observed it?
From where?
Against which evidence?
Can another party recompute the claim?
```

This is especially relevant for agent payments, programmable wallets, deployment systems, governance, compliance, and any workflow where an AI system can create an irreversible or costly state transition.

---

## Who wins / who loses

### Likely winners

- guardrail providers that emit portable, inspectable decisions;
- observability systems that preserve causal identity across execution boundaries;
- independent verification and audit infrastructure;
- wallets and payment systems that expose evidence instead of opaque success states;
- agent frameworks that make provenance composable without owning the trust root.

### Likely losers

- systems where the actor is also the only observer;
- opaque `success=true` APIs with no durable evidence path;
- trust models that collapse decision, execution, observation, and verification into one provider assertion;
- compliance layers that can produce a report but cannot reconstruct the causal chain.

---

## What to watch next

The next useful signal is not another architecture comment.

It is a conformance test that proves observer identity and vantage are behaviorally meaningful.

Watch for:

- portable outcome-receipt proposals;
- cross-provider execution identity;
- observer/vantage fields in agent audit schemas;
- independent settlement observers for agent payments;
- mutation tests where changing observer or vantage changes the verdict;
- tooling that detects conflicting observations across ledger, API, webhook, chain, and audit planes.

---

## Hot Question

> **When your AI agent reports that a consequential action succeeded, who is currently allowed to declare that outcome — and can a third party verify that observer's identity, vantage, and evidence without trusting the agent itself?**

That question is intentionally uncomfortable.

If the answer is “the agent” or “the same provider that executed it,” you may have an outcome record.

You do not yet have independent outcome provenance.

---

## Action

For builders, a practical next step is small:

Take one consequential workflow and draw two records instead of one.

```text
PRE-ACTION
intent → policy → decision → decision provenance

POST-ACTION
execution → observed outcome → observer → vantage → evidence
```

Then try to join them using only stable references that a third party could inspect.

Where the join breaks, you have found a real trust boundary.

---

## Verification checklist

- [x] Distinguishes authorization from observation.
- [x] Distinguishes logical operation from concrete execution attempt.
- [x] Distinguishes source class from observer identity.
- [x] Distinguishes observer identity from observation vantage.
- [x] Does not imply execution replay from a binding receipt.
- [x] Preserves external discussion as context rather than endorsement.
- [x] Links the public comparison that exposed the gap.
- [x] Links the underlying RESONANCE engineering signal.

---

## Evidence

### Primary

1. CrewAI public discussion, Issue #4877 — `GuardrailProvider interface for pre-tool-call authorization`:  
   https://github.com/crewAIInc/crewAI/issues/4877
2. External implementation comparison that explicitly identifies field-level convergence and the missing `outcome_observer_id` / `outcome_vantage` axis:  
   https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5276112082
3. RESONANCE comment defining separate decision and outcome provenance with shared vocabulary:  
   https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5274665965

### RESONANCE evidence

4. Engineering Signal 008 — Independent Outcome-Provenance Convergence:  
   https://github.com/safal207/RESONANCE/blob/main/signals/008-independent-outcome-provenance-convergence.md
5. Follow-up publication link posted into the public CrewAI thread:  
   https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5276161189

See the companion source note: [`04-who-saw-the-outcome.sources.md`](04-who-saw-the-outcome.sources.md).

---

## Uncertainty

This article establishes an architecture argument and documents a public implementation comparison. It does **not** establish that CrewAI has adopted this model, that the external `verdict_outcome` implementation is correct, that the proposed receipt shape is standardized, or that observer/vantage fields have been validated in production.

Those are future claims and require separate evidence.

---

## Corrections

If any cited public thread, field mapping, or claim boundary is represented incorrectly, open an issue or pull request in the RESONANCE repository with the exact source and proposed correction.

---

## Verification chain

```text
public proposal
  → public external comparison
  → field-level convergence
  → explicit schema gap
  → RESONANCE engineering signal
  → this feature article
  → next falsifiable test: observer/vantage conformance
```

**RESONANCE — Find the signal. Verify the path. Understand the future.**
