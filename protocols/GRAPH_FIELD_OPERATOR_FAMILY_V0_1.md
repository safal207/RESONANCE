# Graph–Field Operator Family v0.1

Status: **experimental / advisory**

## 1. Purpose

Graph–Field Dynamics is a family of bounded field operators over graphs, not one universal scoring formula.

The shared question is:

> Given a bounded graph and current observations, which graph location or transition should become the next candidate for attention, recovery, investigation, or handoff?

The operator family unifies the lifecycle and trust boundary while allowing each operator to use domain-specific field components.

Canonical invariant:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

A field result never grants execution, merge, deployment, payment, production mutation, security, or privilege authority.

## 2. Operator family

### OrientationOperator

Question: **Where should we inspect or work next?**

Current implementation: `skills/graph-field-orientation/score_graph_field.py`.

Field channels currently include divergence, uncertainty, blast radius, freshness gap, open pressure, opportunity and blockedness, with bounded one-hop diffusion.

### RecoveryOperator

Question: **Where should we re-enter after context loss or interruption?**

Existing implementation: `safal207/Causal-Memory-Layer` Focus–Field Recovery v0.2.

The CML operator scores bounded recovery anchors using concept, value, goal, causal, phase, time, unresolved-work and evidence signals. Current CML also separates historical usefulness from `trusted_continuation`: an exploratory anchor may be selected without becoming a trusted continuation point.

Relationship:

```text
Focus–Field Recovery ⊂ Graph–Field Operator Family
```

The family does **not** copy CML scoring logic into RESONANCE and does not require CML to import RESONANCE runtime code.

### CalibrationLoop

Question: **After an independently observed outcome, what bounded parameter proposal is worth testing next?**

Current implementation: `skills/graph-field-orientation/calibrate_graph_field.py`, specified by `protocols/GRAPH_FIELD_CALIBRATION_V0_2.md`.

Calibration is not another field scorer. It consumes frozen pre-action component values, evidence-backed observed outcomes and an explicit simpler baseline. It emits a proposal only and never mutates canonical weights automatically.

### Candidate future operators

- `MaintenanceOperator` — what should be repaired next?
- `EvidenceOperator` — where is proof weakest or stale?
- `RiskOperator` — where is risk accumulating?

These names are reserved only as design directions. They are not implemented by this protocol.

## 3. Shared lifecycle

Every operator follows the same outer lifecycle:

```text
intent
→ bound graph
→ collect observations/evidence
→ project domain field
→ rank/select candidate
→ expose trust/actionability state
→ preserve authority_granted=false
→ hand off to native authority-aware path
→ observe outcome separately
→ optional evidence-backed calibration proposal
→ future recomputation
```

The field may select a candidate. Selection is not permission.

## 4. Domain-specific fields stay domain-specific

A single coefficient vector across all operators is explicitly rejected.

Examples:

- recovery cares about semantic/value/causal fit and current CML applicability;
- maintenance cares about divergence, staleness, blast radius and blockedness;
- evidence routing may care about provenance gaps, freshness and verifier independence.

Unification occurs at the operator contract and trust boundary, not by pretending these signals are interchangeable.

## 5. Common result envelope

The executable reference normalizes supported operator outputs to:

```json
{
  "schema": "resonance.graph-field-operator.result.v0.1",
  "operator_kind": "orientation | recovery",
  "source_contract": "...",
  "selection": {
    "id": "... | null",
    "score": 0.0,
    "state": "..."
  },
  "handoff": {
    "ready_for_separate_authority_check": false
  },
  "mode": "ADVISORY_ONLY",
  "authority_granted": false
}
```

The envelope is a semantic adapter. It does not attest that the source result is authentic, current, independently verified, or authorized.

## 6. Recovery mapping

CML Focus–Field v0.2 maps as follows:

| CML state | Unified state | Authority-check handoff |
|---|---|---|
| `defocus` | `NO_SELECTION` | false |
| `reanchored_exploratory` | `EXPLORATORY_SELECTION` | false |
| `reanchored` + `trusted_continuation=true` | `TRUSTED_REENTRY_CANDIDATE` | true |

`ready_for_separate_authority_check=true` means only that the recovery candidate passed the source operator's current continuation gates. It does **not** mean authority was granted.

Any contradictory combination fails closed during normalization.

## 7. Orientation mapping

A valid GFD orientation result maps its top-ranked node to `ORIENTATION_CANDIDATE`.

The candidate may be handed to a separate authority-aware workflow for inspection or action planning, but the normalized envelope keeps:

```text
mode = ADVISORY_ONLY
authority_granted = false
```

## 8. Calibration boundary

Calibration preserves three distinct records:

```text
pre-action field snapshot
observed outcome
calibration proposal
```

Later outcomes do not rewrite the historical pre-action field score.

`field_score` is a routing score, not a probability of success. The calibrator therefore compares evidence-backed observed utility with a declared simpler baseline under a frozen utility definition instead of using `outcome - field_score` as a fake prediction error.

Every calibration result remains:

```text
mode = ADVISORY_ONLY
authority_granted = false
apply_recommended = false
```

Any proposed weights must be evaluated on held-out observations before they can even become a candidate configuration.

## 9. Focus semantics

Focus remains an allocation/observation operator, not a truth source.

```text
focus → observation → evidence → recompute field
```

Never:

```text
focus → stronger score → therefore true
```

Calibration inherits the same rule: attention volume is not outcome evidence.

## 10. Human / SELF boundary

For human-facing operators, intrinsic human worth is outside the optimization target.

> **Failure updates the model of action, not the worth of the actor.**

Values may constrain or orient a field, but a numerical field must not become a score of human value, lovability or dignity.

## 11. Compatibility boundary

The first compatibility target is CML Focus–Field v0.2 as reconciled by FCRP-SELF-006 on CML main.

RESONANCE consumes only a serialized result shape in the executable adapter. It does not import CML packages or reproduce CML applicability/information-quality gates. This prevents a second authority or verification implementation from emerging in the routing layer.

## 12. Falsification

The operator family earns its complexity only if specialization plus a common contract improves real routing/recovery outcomes over simpler baselines.

Track per operator:

- wrong-selection rate;
- useful result per unit cost;
- blocked-work avoidance;
- recovery/reorientation latency;
- downstream rework;
- stale evidence catches;
- authority-boundary violations (must remain zero).

Calibration proposals must be tested on held-out observations. If a proposal fails to outperform current weights out-of-sample, discard it.

If a specialized field does not beat its simpler baseline, remove or reduce that operator rather than protecting the family abstraction.
