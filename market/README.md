# RESONANCE Market OS

This directory is the evidence layer for the RESONANCE **Article → Dialogue → Product** loop.

## Canonical loop

```text
PUBLISH
  ↓
TEACH
  ↓
ASK
  ↓
LISTEN
  ↓
DIAGNOSE
  ↓
GIVE VALUE
  ↓
SPECIFY
  ↓
PILOT
  ↓
PROVE
  ↓
PRODUCTIZE
  ↓
PUBLISH AGAIN
```

## North Star

**Verified Product Requests** — cases where a real market participant has described a concrete workflow/problem and validated that a proposed missing capability would materially solve it.

Views, likes and followers remain distribution metrics. They are not demand evidence.

## Demand Log

Each meaningful response should become a Problem Card conforming to `problem-card.schema.json`.

Minimum useful fields:

- source article, language and channel;
- actor/action/trigger;
- concrete failure path;
- business or operational impact;
- current workaround and limitation;
- missing capability;
- desired invariant / acceptance condition;
- verification and evidence requirement;
- original client wording;
- Product Signal Score;
- next diagnostic question.

## Product Signal Score

| Signal | Points |
|---|---:|
| Concrete workflow | 2 |
| Concrete failure | 2 |
| Business impact | 2 |
| Current workaround | 1 |
| Missing capability | 1 |
| Acceptance condition | 1 |
| Willingness to test | 1 |

Interpretation:

- 0–2: reaction/comment
- 3–4: problem signal
- 5–6: qualified problem
- 7–8: product signal
- 9: pilot candidate
- 10: verified product request

## Golden rule

Do not pitch before both statements can be completed:

> The client cannot currently ______ because ______.

> The client considers the problem solved when ______ can be proven.

## Real vs synthetic evidence

`demand-graph.json` may contain illustrative synthetic nodes so the data model can be tested before market responses arrive. Synthetic entries **must** have `synthetic: true` and **must never** be counted in market metrics, product validation, article-selection evidence, or revenue claims.

The initial graph therefore reports `realSignalCount: 0`. That number changes only after actual external submissions are reviewed and recorded.

## Intake

The zero-backend intake is `.github/ISSUE_TEMPLATE/market-workflow.yml`. The public site can link directly to that issue form. Contributors are instructed to remove confidential information, credentials, secrets and identifying production details.
