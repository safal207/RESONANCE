# Article #005 Selection Rule

## Status

**Mechanism implemented; evidence-dependent decision remains open.**

Article #005 must not be presented as market-selected until real external responses to Article #004 produce enough evidence to justify a recurring problem cluster.

## Inputs

Only reviewed, non-synthetic Problem Cards may influence the decision.

Synthetic demo nodes in `market/demand-graph.json` are excluded.

## Selection process

1. collect real workflow responses from Article #004;
2. convert meaningful responses into Problem Cards;
3. calculate Product Signal Score;
4. normalize equivalent failures expressed in different language;
5. cluster by failure mechanism, impact and missing capability;
6. rank clusters using both recurrence and severity;
7. choose the strongest defensible cluster;
8. write Article #005 around the problem and what the market taught us;
9. end #005 with a deeper question that advances discovery rather than repeating #004.

## Minimum evidence rule

Before calling #005 “chosen by the market”, require at least:

- **10 meaningful external workflow responses**, and
- **3 non-synthetic cases in the selected cluster**, from at least **2 independent contributors/organizations** when identity/context is available.

If these thresholds are not reached, keep Article #005 topic **OPEN** and report the evidence honestly.

## Ranking heuristic

For cluster `c`:

```text
priority(c) = recurrence × median_signal_strength × impact_weight × independence_factor
```

This is a prioritization heuristic, not a scientific statistic. Preserve the underlying cases so the ranking can be challenged.

## Candidate example — not evidence

If real responses eventually show `unknown commit / unsafe retry` as the strongest cluster, a candidate could be:

**The Unknown Commit Problem: When an AI Agent Doesn't Know Whether Its Action Happened**

Deeper question:

> When your agent enters an uncertain state, what currently decides whether it is safe to continue?

This example is illustrative and must not be counted as a market result.
