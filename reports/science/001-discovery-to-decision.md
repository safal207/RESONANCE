# RESONANCE Science Report #001

## From Discovery to Decision: The Missing Evidence Layer in Biology

**Status:** draft research note  
**Desk:** RESONANCE Science  
**Scope:** evidence interpretation and translation readiness  
**Research boundary:** no wet-lab instructions, clinical claims, safety approval or experiment authorization

## Question

A controlled biological study can produce a valid and important result while still leaving a second question unanswered:

> What additional evidence is needed before that result should influence a real-world biological decision?

This report treats that gap as a first-class evidence state rather than as an afterthought.

## Why this matters

Scientific communication often stops at the strongest justified conclusion inside the study.

Operational decisions do not.

They must also ask whether the result transfers across:

- populations;
- environments;
- timescales;
- intervention contexts;
- demographic histories;
- ecological constraints;
- unmeasured risks and confounders.

The core distinction is:

```text
VALID RESULT
    ≠
DECISION-READY RESULT
```

A translation gap is not a criticism of the original study. It is a separate scientific object.

## Founding case prompt: genetic rescue

The first RESONANCE Science field-translation prompt was developed around genetic rescue research and a direct outreach question to a study author.

The prompt is intentionally narrow:

> Which additional evidence would most change confidence when translating a result from replicated laboratory populations to a real endangered population?

Candidate evidence dimensions include, but are not limited to:

- donor–recipient genomic distance;
- local adaptation;
- pathogen or disease context;
- demographic history;
- multigenerational follow-up;
- long-term fitness consequences;
- ecological context;
- another factor identified by domain experts.

These are **translation questions**, not claims that any specific study failed to address them.

A related working evidence map is maintained in Kairos Gate:

- https://github.com/safal207/Kairos-Gate-for-X-Cell/issues/65

## Proposed translation-readiness states

The following states are editorial/research bookkeeping states. They are not biological truth labels and are not certification grades.

### `OBSERVED_IN_SCOPE`
A result is supported in the defined experimental scope.

### `REPLICATED_IN_MODEL_SYSTEM`
The relevant result has been reproduced across the defined controlled system or repeated units, where replicate semantics are established.

### `TRANSFER_ASSUMPTIONS_EXPLICIT`
The assumptions required to generalize beyond the original scope are named.

### `TRANSFER_EVIDENCE_PARTIAL`
Some external-validity evidence exists, but material gaps remain.

### `FIELD_VALIDATION_PENDING`
The evidence required for the target real-world context has not yet been established.

### `DECISION_READINESS_UNRESOLVED`
The result may be scientifically meaningful, but the evidence is not sufficient to justify a broader decision claim inside this framework.

These states are deliberately non-linear. Different scientific questions may require different paths.

## The evidence map

A useful field-translation record should distinguish at least four layers.

| Layer | Question | Example output |
|---|---|---|
| Result | What was actually observed? | source-bound finding |
| Interpretation | What does the result support? | bounded conclusion |
| Transfer | What must remain true outside the study? | explicit assumptions |
| Decision | What additional evidence would change action? | readiness gap |

The purpose is not to add bureaucracy. It is to prevent an implicit jump from layer 1 or 2 directly to layer 4.

## The translation-gap record

A minimal machine-readable or human-readable record could contain:

```yaml
claim: <narrow scientific claim>
source_scope: <population / system / environment / time>
evidence_state: <reported / recalculated / replicated / causal / unresolved>
translation_target: <new population / field context / decision>
transfer_assumptions:
  - <assumption>
negative_or_conflicting_evidence:
  - <evidence or none known>
missing_evidence:
  - <gap>
next_discriminating_evidence: <one result that would most change confidence>
decision_boundary: <what should not yet be concluded or authorized>
```

## What RESONANCE is testing

The hypothesis is not that every biological decision can be reduced to a checklist.

The narrower hypothesis is:

> Making translation assumptions and missing evidence explicit may improve scientific review, AI-assisted research and downstream decision quality without pretending that judgment can be automated away.

That hypothesis can be wrong.

The Science Desk therefore treats researcher disagreement as evidence about the model itself.

## Open question to conservation genetics

If a controlled genetic-rescue result is scientifically convincing inside its study system, what is usually the **largest remaining evidence gap** before it should inform a real conservation intervention?

Possible answers may involve genomics, ecology, disease, demography, timescale, fitness, implementation context—or something the current model misses entirely.

One precise correction is more useful than broad agreement.

## Next step

A substantive researcher reply should produce one of four outcomes:

1. **CONFIRM** — one proposed translation dimension is genuinely decision-relevant;
2. **CORRECT** — the current framing misstates the scientific boundary;
3. **ADD** — an important missing evidence dimension is identified;
4. **REJECT** — translation readiness is too context-dependent for this representation to be useful.

Each outcome is publishable evidence about the framework.

## Non-claims

This report does not:

- assess the validity of a particular genetic-rescue paper;
- claim that laboratory work automatically generalizes or fails to generalize;
- recommend any conservation intervention;
- provide biological protocols;
- imply endorsement by any contacted scientist or institution;
- replace domain-expert judgment.

## RESONANCE principle

**A discovery is not automatically a decision.**

The path between them should be visible.
