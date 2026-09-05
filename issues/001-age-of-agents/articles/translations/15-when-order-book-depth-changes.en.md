# The Order Book Changed. Permission Remained.

How a RESONANCE Verify recheck detects insufficient depth before simulated order submission—and why state changes after the last observation remain a separate risk.

A trading agent finds a route, estimates its costs and passes a check. A few dozen milliseconds later, it is ready to hand the order onward. The displayed price is unchanged. So is the modeled edge. But the available volume is no longer sufficient.

What does the original decision authorize: an action under the observed conditions, or any later action with similar parameters?

We examined this question in a small, open RESONANCE Verify example. Every price, state and timestamp is synthetic. The example checks an admission flag in memory; it does not connect to an exchange or create orders. It can be reproduced from the [pinned source code](https://github.com/safal207/resonance-arbitrage-graph/tree/d6317c30833fed7d19edbcaf4f9f7467faa58519).

## One order, two states

The illustrative route starts with 1,000 USDT and goes through BTC and ETH back to USDT. The model charges a 5-basis-point fee and 5 basis points of modeled slippage on each leg. The admission threshold is 30 basis points after these costs.

The initial check passes: the modeled net edge is about +94.66 basis points. The engine calls this `EXECUTE_SIM`: admission exclusively within the simulation.

On the first leg, the best ask is 80,000 USDT per BTC. Initially, 2 BTC is available at that price, giving the first price level a capacity of 160,000 USDT. The quantity then falls to 0.0075 BTC. Capacity becomes 600 USDT—less than the required 1,000.

| Fixture time | Observed state | Result |
| --- | --- | --- |
| 1,000 ms: initial check | First-leg capacity: 160,000 USDT | `EXECUTE_SIM` |
| 1,075 ms: next snapshot | Same price; capacity is now 600 USDT | New input data |
| 1,080 ms: recheck | 1,000 USDT required; 600 available | `REJECT`, `CAPACITY_EXCEEDED:0` |

This 80-ms interval is specified by the scenario. It is not a measured latency of a real trading system. At the decision point, the new snapshot is 5 ms old; the maximum permitted age is 100 ms.

## Freshness does not replace capacity

In the main scenario, both price and the cost model are held constant. The modeled net edge remains positive. The snapshot passes the age check. What changes is the available volume on the first leg, and insufficient capacity is precisely why the decision becomes a rejection.

This makes the result inspectable: we can separate the effect of volume from the effects of price and time. A freshness rule alone does not stop this case, because the new snapshot really is fresh.

When the old permission is reused, the example records admission in memory. With a new check, the engine rebuilds the route from the current snapshots and returns `CAPACITY_EXCEEDED:0`. Admission is withdrawn. Neither path makes an actual submission call to an exchange.

> Permission retains its meaning together with the conditions under which it was granted.

## A control must also be able to pass

An example that rejects everything says little about a check's usefulness. Alongside the changed order book, we therefore include a positive control: a fresh, unchanged snapshot preserves `EXECUTE_SIM`.

The complete fixture contains seven cases. Five deliberately selected adverse states remove admission. The seventh case exposes the limit of the approach.

| Case | Final verdict | Admission in memory |
| --- | --- | --- |
| Fresh, unchanged order book | `EXECUTE_SIM` | Yes |
| First-leg capacity falls to 600 USDT | `REJECT` | No |
| A price change removes the positive modeled net edge | `REJECT` | No |
| Modeled net edge remains positive but falls below the threshold | `OBSERVE` | No |
| Trading status in the fixture changes to `HALTED` | `REJECT` | No |
| Snapshot age exceeds the limit | `REJECT` | No |
| Depth changes after the last check | `EXECUTE_SIM` | Yes; later diagnosis returns `REJECT` |

The existing engine checks capacity, prices, costs and age. The `HALTED` condition is added by a separate wrapper specifically for this fixture: the core `evaluate_route` does not accept exchange status. The report preserves these two decision layers separately.

`OBSERVE` also withholds admission. Rechecking cannot turn a stricter original decision into permission: an initial `REJECT` or `OBSERVE` cannot become `EXECUTE_SIM` merely because a later snapshot improves.

## Another twenty milliseconds

In the final case, the recheck sees sufficient volume and retains admission at 1,080 ms. The volume then disappears. At the simulated arrival time, 1,100 ms, the same model returns `REJECT`.

This is an expected, unresolved case. The decision does not use future data. The arrival snapshot is analyzed afterward, solely as a diagnostic. A separate test verifies that changing arrival data does not change the earlier verdict.

A recheck works with the observation available to it. It does not reserve liquidity or bind its decision atomically to exchange state. An unobserved change can also happen between the last snapshot and the check itself.

The practical implication for integration is to specify separately which constraints the executor can check when accepting an order and which observable result completes the action. A fresh local snapshot does not automatically answer those questions.

## What the checks actually establish

All 12 demo tests passed for the inspected revision. They cover replay, exact decision reasons, the snapshot-age boundary, capacity units on the second leg, rejection of future snapshots, preservation of a stricter original decision and detection of report changes.

A repeat run reproduces the complete JSON result with the same SHA-256. The report binds the fixture, policy, cost parameters, states and bytes of seven implementation modules. This makes changes to the inputs or code detectable.

Five stopped synthetic cases do not provide a statistical detection-quality estimate. Twelve passing tests do not establish the behavior of a real exchange. Hashes establish that data matches; they do not authenticate market observations.

The result status is `UNASSESSED_REPLAY_SOURCE`. Its model is `NONE_ADMISSION_ONLY`: the check concerns admission in memory. It does not model fills across multiple price levels, queue position, partial fills, real profit or measured money saved. Quantilan systems were not tested; this publication relies on an open synthetic example and claims no endorsement by the team.

## Reproduce the result

Python 3.11 or newer is required. Verification was performed on Linux with Python 3.12.13. No Python package installation or network access is required during the run itself.

Obtain the repository and select the exact demo revision:

```bash
git clone https://github.com/safal207/resonance-arbitrage-graph.git
cd resonance-arbitrage-graph
git checkout d6317c30833fed7d19edbcaf4f9f7467faa58519
```

Check the saved report:

```bash
PYTHONPATH=src python3 -m resonance_arbitrage_graph.exchange_state_demo \
  --fixture examples/quantilan/fixture.json \
  --check examples/quantilan/expected-report.json
```

Expected output:

```text
Replay matches: 313084ae4464b057423496f800225015a4a2b565a0ae81be748aed02c0f5bad0
```

Run the 12 tests:

```bash
PYTHONPATH=src python3 -m unittest discover \
  -s tests -p test_exchange_state_demo.py -v
```

[Open the fixture and code on GitHub](https://github.com/safal207/resonance-arbitrage-graph/tree/d6317c30833fed7d19edbcaf4f9f7467faa58519).

## The next question for a real workflow

The demo provides a small, concrete starting point for an integration discussion: which state snapshot is available immediately before admission, and which constraints remain checkable when the executor accepts the order?

The next useful experiment is one public or synthetic example from another team with explicitly defined state fields and timestamps. It would let us compare the expected rejection, the actual reason and reproducibility. Neither access credentials nor a private strategy is needed for that experiment.

A historically correct decision becomes usable for the next action only within conditions that the system can actually check.

## Sources and verification boundary

1. [Demo description and limitations](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/docs/QUANTILAN_EXCHANGE_STATE_DEMO.md).
2. [Synthetic fixture](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/examples/quantilan/fixture.json).
3. [Complete expected report](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/examples/quantilan/expected-report.json).
4. [Decision comparison module](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/src/resonance_arbitrage_graph/exchange_state_demo.py).
5. [The twelve tests](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/tests/test_exchange_state_demo.py).
6. [Core route verification engine](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/src/resonance_arbitrage_graph/engine.py).

Author: Aleksei Safonov. Source-file verification and local reproduction: 5 September 2026. The result applies to the cited commit and this fixture; this publication does not claim an independent external run.
