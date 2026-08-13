# RESONANCE Market Signal Readout v0.9

## Goal

Turn the already-verified five-field privacy analytics stream into a deterministic, reviewable market-signal readout **without adding visitor/session identity and without promoting attention signals into demand claims**.

The readout spine is:

```text
closed UTC interval
  → sampling-aware Analytics Engine aggregate
  → strict dimension validation
  → explicit synthetic-smoke exclusion
  → deterministic JSON + Markdown
  → human interpretation
  → downstream Market OS evidence only when a real workflow is submitted
```

## Data contract remains unchanged

v0.9 does not add browser fields or events. It consumes the existing v0.8 production dataset:

```text
blob1   event
blob2   path
blob3   language
blob4   content_kind
blob5   schema_version
double1 1
```

Allowed events remain:

- `meaningful_read`
- `hot_question_view`
- `workflow_intake_open`
- `verified_workflow_open`

No visitor ID, session ID, IP-derived field, referrer, User-Agent, device field, free text, email, name or client timestamp is introduced.

## Deterministic window contract

Every readout is tied to an explicit end-exclusive UTC window:

```text
[window_start, window_end)
```

Both timestamps use exact `YYYY-MM-DDTHH:mm:ssZ` form. The SQL is generated from these values and never uses a rolling `NOW() - interval` window for an evidence artifact.

Scheduled runs use the previous completed UTC day. Manual runs may provide an explicit start and end; both or neither must be supplied.

## Sampling-aware aggregate

Workers Analytics Engine may sample at high volume. Counts therefore use:

```sql
SUM(_sample_interval * double1)
```

The query groups only by the five stored measurement dimensions and sorts the result before transformation.

## Synthetic activation evidence is not readership

The v0.8 activation workflow wrote synthetic events under paths shaped like:

```text
/RESONANCE/__collector-smoke-<run_id>-<attempt>.html
```

v0.9 does not delete or hide those rows. The readout classifies them as synthetic, excludes them from market totals, and reports the excluded count separately.

This preserves the evidence history while preventing infrastructure verification from manufacturing readership.

## Aggregate ratios are not conversion rates

v0.9 may calculate ratios such as:

```text
hot_question_view / meaningful_read
workflow_intake_open / hot_question_view
verified_workflow_open / hot_question_view
```

These are **aggregate signal ratios within the same closed interval**. They are not user-level conversion rates because RESONANCE intentionally does not create visitor/session identity. They also do not establish that the numerator was caused by or came from the same people/page loads as the denominator.

## Demand boundary

The browser measurement chain stops at attention/action signals:

```text
meaningful_read
  → hot_question_view
  → workflow_intake_open / verified_workflow_open
```

A click is not a Product Signal.

Demand begins only after explicit evidence enters the Market OS path:

```text
workflow submission
  → diagnostic dialogue
  → Problem Card
  → Product Signal
  → client-specific pilot
  → evidence
```

## Outputs

Each live run emits immutable workflow artifacts containing:

- `market-signals.sql` — exact query bytes;
- `market-signals-raw.json` — provider response;
- `market-signals.json` — normalized machine-readable readout;
- `market-signals.md` — compact human summary.

The machine-readable schema is `resonance.market-signals.v0.9`.

## Evidence boundary

A passing v0.9 run can establish the aggregate event counts returned by Workers Analytics Engine for the specified closed interval, after explicit synthetic-smoke classification and strict dimension validation.

It cannot establish reader identity, unique visitors, sessions, comprehension, causal conversion, qualified demand, product-market fit, revenue or delivery completeness. Provider infrastructure and retention remain subject to the v0.8 Cloudflare boundary.
