# Engineering Signal 008 — Independent Outcome-Provenance Convergence

**Status:** externally observed architecture convergence; original observer-identity gap subsequently shipped; semantic-vantage boundary remains under test  
**Observed:** 13 Aug 2026  
**Scope:** comparison of a public RESONANCE/CrewAI causal-provenance proposal against an independently developed, shipped `verdict_outcome` mechanism  
**External context:** [`crewAIInc/crewAI#4877`](https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5276112082)  
**Not:** CrewAI endorsement, adoption, certification, or proof that either implementation is complete or correct

## Main signal

> **Independent implementation comparison converged on the same decision/outcome provenance split and exposed one concrete missing axis: `source_class` says how an outcome was established, but not who observed it or from what vantage.**

This matters because the comparison was made against a shipped mechanism rather than only against an abstract proposal.

The external implementer reported that their existing `verdict_outcome` model had independently arrived at several of the same boundaries:

- the outcome carries its own `source_class`;
- outcome `source_class` is explicitly separate from decision-side `source_class`;
- `cites_decision_ref` plays the role of the proposed `pre_action_decision_ref`;
- `outcome_evidence.mechanism` is close to the proposed `observation_basis` and travels with the observation;
- decision provenance and outcome provenance should remain separate while sharing vocabulary.

The comparison also exposed a gap they explicitly logged for a later careful extension:

- no distinct `outcome_observer_id`;
- no distinct `outcome_vantage` beyond `source_class`.

Their summary of the gap was precise: `source_class` answers **how** the outcome was graded, but not **who specifically observed it, from where**.

## Four-question causal boundary

The useful split is:

1. **Was the action authorized?**
2. **Is the claimed outcome bound to the same logical operation and concrete execution?**
3. **What outcome was observed?**
4. **Who observed it, from what vantage, and against what evidence?**

The fourth question is not redundant with `source_class`.

For example:

```text
source_class: attested
outcome_observer_id: verifier-A
outcome_vantage: ethereum_rpc
```

and:

```text
source_class: attested
outcome_observer_id: wallet-provider
outcome_vantage: internal_ledger
```

may share the same evidence class while representing materially different observation positions and trust boundaries.

## Minimal outcome-provenance extension

The comparison suggests a deliberately small extension boundary rather than another immediate schema expansion:

```text
outcome_provenance:
  source_class
  observer_id
  vantage
  evidence_ref / mechanism
```

The design invariant is:

```text
decision_provenance != outcome_provenance
```

but both should use a compatible vocabulary so a third-party verifier can reason across the causal chain without collapsing the two legs into one trust domain.

## Causal spine

```text
intent
  ↓
decision
  ↓
authorization provenance
  ↓
execution
  ↓
outcome
  ↓
observer
  ↓
vantage
  ↓
evidence
  ↓
verification
```

A binding authorization receipt and an outcome receipt are therefore different claims. Neither should silently imply independent execution replay unless the cited evidence actually supports that stronger verification class.

## Why this signal is stronger than agreement

The external response did three things that are independently useful:

1. compared the proposal against an already-shipped mechanism;
2. named concrete field-level convergence rather than broad conceptual similarity;
3. identified and logged a specific missing observer/vantage layer exposed by that comparison.

That makes the public sequence falsifiable:

```text
provider-neutral causal proposal
        ↓
external comparison against shipped mechanism
        ↓
field-level convergence identified
        ↓
missing observer/vantage axis identified
        ↓
separate extension logged
```

The value is not that two systems use identical names. The value is that independent implementations arrived at the same separation of responsibilities, and the comparison revealed where one axis was still overloaded.

## Engineering restraint is part of the signal

The external implementer explicitly declined to perform a reactive fifth schema edit after four real bug-fix rounds. That was the correct boundary at the time of the initial comparison.

The useful next step was therefore not to claim adoption, but to make observer identity and observation vantage separately testable with cases that distinguish:

- same source class, different observer;
- same observer, different vantage;
- missing observer identity;
- missing/ambiguous vantage;
- evidence whose mechanism does not support the claimed vantage.

## Subsequent implementation update

The originally identified identity gap did not remain hypothetical. A later public implementation update reported that `verdict_outcome` now carries:

- `outcome_observer_id`, required for newly published entries and explicit `null` on migrated records rather than invented identity;
- `outcome_vantage`, derived rather than caller-supplied.

External update: [`crewAIInc/crewAI#4877` — shipped observer fields](https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5284839948).

This closes the **missing observer identity** part of Signal 008 at the schema level.

It also exposes a narrower semantic question. The reported `outcome_vantage` is derived from the outcome entry's `source_class` plus whatever can be recovered from the cited decision's `vantage_limitation`, with states including `none`, `unrecovered`, and `unrecognized`.

Those states may be useful, but they appear to mix two different axes:

```text
observer_vantage
  = where/how this observer actually observed the outcome

decision_vantage_resolution
  = what could be recovered about the cited decision's vantage metadata
```

A falsification test is therefore:

> Can two outcome observers with the same `source_class`, citing the same decision, observe the same outcome from genuinely different surfaces or positions?

If yes, and the current derivation necessarily gives them the same `outcome_vantage`, then that field is modeling a lineage/provenance-resolution relation to the cited decision rather than the observer's actual vantage.

This does **not** establish an implementation defect. `outcome_evidence.mechanism` may already carry some or all of the actual observation surface. The point is to keep the ontology decomposable:

```text
observer identity != observer vantage != decision-vantage resolution state
```

A public follow-up raised exactly this falsification test without asserting the answer: [`crewAIInc/crewAI#4877`](https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5291435538).

## Research / market question

When an agent system reports that an authorized action produced a particular outcome:

> **Can an independent verifier determine not only how that outcome was graded, but who observed it, from what actual vantage, and against which evidence — without confusing observer context with metadata-resolution state and without trusting the decision issuer or outcome reporter?**

If not, the system may have attributable outcome provenance while still conflating the semantics of observation position and lineage recovery.
