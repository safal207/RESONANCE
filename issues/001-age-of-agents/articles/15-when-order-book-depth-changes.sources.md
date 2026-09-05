# Article 015 — source and claim ledger

Date: 2026-09-05 UTC.
Author: Aleksei Safonov.
Subject: the public RESONANCE Verify synthetic exchange-state demo.
Pinned subject commit: d6317c30833fed7d19edbcaf4f9f7467faa58519.
Core implementation base: ccd4f7417da5263a2f3d66abbd20e0bbd6cf93f6.

## Sources

All paths below are relative to https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/.

| ID | Source | Supported claim |
| --- | --- | --- |
| S1 | docs/QUANTILAN_EXCHANGE_STATE_DEMO.md | Assumptions, expected replay, scope and implementation boundary |
| S2 | examples/quantilan/fixture.json | Explicit prices, quantities, times, costs, policy and seven cases |
| S3 | examples/quantilan/expected-report.json | Initial result, final decisions, reasons and later diagnostics |
| S4 | src/resonance_arbitrage_graph/exchange_state_demo.py | Initial/boundary/arrival order; monotonic admission; fixture-only status gate |
| S5 | tests/test_exchange_state_demo.py | Twelve focused tests, including future-data isolation and replay mismatch |
| S6 | src/resonance_arbitrage_graph/engine.py | Unit-aware per-leg capacity, quote age, costs and verdict rules |
| S7 | src/resonance_arbitrage_graph/quotes.py | BUY capacity equals ask price multiplied by ask base quantity |

## Directly observed in this preparation

- Standard-library focused suite: 12 tests passed, zero failed, Python 3.12.13 on Linux.
- Fresh replay matched the full frozen JSON report.
- The self-contained distribution repeated the same result and 12 tests after extraction.
- Ten source/input/test/report files matched the Git blob IDs in the pinned public commit.
- Exact report payload SHA-256: 313084ae4464b057423496f800225015a4a2b565a0ae81be748aed02c0f5bad0.
- Canonical fixture SHA-256: bbbfecaeabbb70d68ab3b513e575edf2da5cac1ba86c3ae7fa20cf509f477dbc.

The checks were performed as part of the author's preparation. They are not an
independent external reproduction or a report of a Quantilan test run.

## Claim matrix

| Statement | Class | Boundary |
| --- | --- | --- |
| Initial modeled net edge is about +94.66 bps | Recomputed fixture result | Illustrative prices and fixed costs; not an executable fill or profit |
| Capacity 600 USDT is below the 1,000-USDT input | Arithmetic and engine result | First best-price level; no multi-level book |
| Depth-only change yields CAPACITY_EXCEEDED:0 | Recomputed fixture result | Price and modeled edge unchanged; 5-ms quote age remains within the 100-ms limit |
| Five selected adverse cases stop simulated admission | Recomputed fixture result | Hand-authored cases; no detection-rate estimate |
| Fresh unchanged control permits simulated admission | Recomputed fixture result | No live submission |
| Post-check drift remains unseen by the guard | Recomputed fixture result | 20-ms synthetic gap; arrival diagnostic is not input to the earlier decision |
| Status HALTED stops admission | Wrapper result | Synthetic fixture-only gate; the existing core engine does not ingest venue status |
| Rechecking may be useful at an integration boundary | Engineering inference | Effectiveness in a real system is unmeasured |

## Non-claims

No private correspondence is reproduced. No Quantilan runtime, strategy,
exchange, credentials or live orders were tested. No endorsement, adoption,
paid engagement, production failure, profitability, saved money, atomic
exchange-state binding, liquidity reservation, runtime latency measurement,
multi-level fill, queue, partial-fill or system-wide security claim is made.

The publication does not upgrade a deterministic replay or a hash into source
authenticity, completeness, execution authority or independent review.
Claim status: UNASSESSED_REPLAY_SOURCE. Fill model: NONE_ADMISSION_ONLY.
