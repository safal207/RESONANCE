# Sources — Who Saw the Outcome?

**Article:** [`04-who-saw-the-outcome.md`](04-who-saw-the-outcome.md)  
**Last verified:** 2026-08-13

## Primary public discussion

### CrewAI GuardrailProvider proposal

- Thread: https://github.com/crewAIInc/crewAI/issues/4877
- Scope used by this article: provider-neutral pre-action authorization, causal binding, post-action outcome provenance, and public implementation comparison.

### RESONANCE causal-spine proposal

- Public comment: https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5274447003
- Relevant claim: an outcome should be causally bound to the same logical operation and concrete execution that the guardrail authorized, without conflating binding verification with execution replay.

### Separate outcome provenance

- Public comment: https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5274665965
- Relevant claim: `observed_outcome` needs provenance separate from the pre-action decision provenance, while using compatible vocabulary such as source class, vantage, and evidence references.

### Independent implementation comparison

- Public comment by `babyblueviper1`: https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5276112082
- Reported convergence:
  - shipped `verdict_outcome` has outcome-side `source_class` separate from decision-side `source_class`;
  - `cites_decision_ref` performs a role analogous to `pre_action_decision_ref`;
  - outcome evidence mechanism travels with the observation;
  - outcome and decision provenance remain separate claims.
- Reported gap:
  - no distinct `outcome_observer_id`;
  - no distinct `outcome_vantage` beyond `source_class`.
- Important boundary: the author logged the gap for later careful work rather than claiming it had already been implemented.

### RESONANCE publication follow-up

- Public comment: https://github.com/crewAIInc/crewAI/issues/4877#issuecomment-5276161189
- Purpose: links the public discussion back to Engineering Signal 008 and preserves the narrow claim boundary.

## Internal RESONANCE evidence

### Engineering Signal 008

- https://github.com/safal207/RESONANCE/blob/main/signals/008-independent-outcome-provenance-convergence.md
- Status: externally observed architecture convergence + concrete schema gap.
- Explicitly excludes claims of CrewAI endorsement, adoption, certification, or implementation correctness.

## Claim boundary

This source package supports the following narrow claims:

1. a public provider-neutral causal-provenance proposal was compared against an independently developed shipped outcome-verdict mechanism;
2. the comparison identified concrete field-level convergence;
3. the comparison identified a missing observer/vantage axis;
4. the gap was logged rather than immediately declared solved.

It does **not** support claims that:

- CrewAI adopted the proposed model;
- CrewAI endorsed RESONANCE;
- the external mechanism is complete or correct;
- observer/vantage fields are already implemented;
- the proposed receipt is a standard;
- a production conformance suite has validated the extension.

## Next falsifiable evidence

A stronger follow-up should produce conformance fixtures that force observable verdict movement for:

- same source class + different observer;
- same observer + different vantage;
- missing observer;
- missing or ambiguous vantage;
- observation mechanism inconsistent with claimed vantage;
- conflicting observers;
- self-observation promoted incorrectly to independent observation.
