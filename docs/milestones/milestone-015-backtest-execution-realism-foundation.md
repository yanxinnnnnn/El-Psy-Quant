# Milestone 15 — Backtest Execution Realism Foundation

## Status

Complete.

## Product Goal

Make backtests less idealized by making execution assumptions explicit, deterministic, and reviewable.

Milestone 14 made portfolio behavior explainable. Milestone 15 explains how research trade intent becomes assumed fills in a local backtest before the project moves toward paper trading.

## Why This Came After Portfolio Risk

Milestone 14 closed this chain:

```text
portfolio_return -> risk metrics
portfolio_equity -> drawdown inspection
aligned_returns + static_weights -> symbol contribution
risk + drawdown + contribution -> attribution summary artifact
```

Execution realism belongs after portfolio behavior is explainable. Fill timing, fill prices, and trade assumptions can change results materially, so they need their own isolated and documented boundary before paper trading or live execution is considered.

## Delivered Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S70 | Complete | Plan Milestone 15. | Execution realism scope and sprint sequence. | No implementation during planning. |
| S71 | Complete | Define execution assumptions. | Small documented execution assumption boundary. | No broker integration. |
| S72 | Complete | Add order intent boundary. | Deterministic order-intent representation. | No live orders. |
| S73 | Complete | Add fill price model. | Local deterministic fill model under explicit timing assumptions. | No market microstructure simulation. |
| S74 | Complete | Add execution-adjusted trade summary. | Reviewable summary of assumed fills. | No portfolio rebalancing engine. |
| S75 | Complete | Add execution realism artifact. | In-memory artifact tying assumptions to results. | No broad configured-run expansion. |
| S76 | Complete | Close milestone. | Milestone 15 documentation refresh. | No scope expansion. |

## Delivered Chain

Milestone 15 delivered this conservative chain:

```text
execution assumptions -> order intent boundary -> deterministic fill model -> execution-adjusted trade summary -> execution realism artifact
```

The concrete public boundaries are:

```text
ExecutionAssumptions
OrderIntent
AssumedFill
summarize_assumed_fills(...)
build_execution_realism_artifact(...)
```

## Delivered Work

### Execution Assumptions

`ExecutionAssumptions` records the smallest useful execution-assumption boundary:

- when an order is assumed to execute
- which OHLC price field is assumed to fill
- how missing fill prices are handled

The default remains conservative: next bar, open price, and raise on missing prices.

### Order Intent Boundary

`OrderIntent` separates what a strategy wants to do from what the backtest later assumes happened.

It records timestamp, symbol, side, quantity, and execution assumptions without creating fills or placing orders.

### Fill Price Model

`AssumedFill` and `fill_order_intent(...)` convert an order intent plus local OHLC price data into one deterministic assumed fill.

The fill model supports explicit same-bar and next-bar timing. It chooses the configured price field and fails loudly on unavailable, missing, non-numeric, or non-finite prices.

### Execution-Adjusted Trade Summary

`summarize_assumed_fills(...)` aggregates already-created assumed fills into deterministic JSON-compatible summary data.

It summarizes counts, symbols, buy/sell quantities, notionals, price-field usage, timing usage, and timestamp ranges. It does not calculate PnL, returns, positions, or cash balances.

### Execution Realism Artifact

`build_execution_realism_artifact(...)` ties assumptions, order intents, assumed fills, summary data, and conservative scope flags into an in-memory JSON-compatible artifact.

It does not write files or integrate with configured runs yet.

## Assumptions

Milestone 15 keeps these assumptions conservative:

- backtest inputs already exist before execution assumptions are applied
- order intent is separate from assumed fills
- assumed fills are separate from real broker fills
- fill timing is explicit
- fill price selection is explicit
- missing-price behavior is explicit
- all behavior is deterministic and local
- no external broker, exchange, streaming, paper-trading, or live-trading dependency is introduced

## Guardrails

Milestone 15 intentionally avoids:

- broker integration
- paper trading behavior
- live trading behavior
- exchange APIs
- order routing
- market data streaming
- market microstructure simulation
- partial-fill modeling
- dynamic portfolio rebalancing
- optimization
- dashboards or databases
- broad configured-run integration
- YAML or CLI expansion for execution realism
- PnL calculation
- position accounting
- cash accounting
- strategy proliferation
- plugin frameworks or dynamic loading

## Exit Criteria

Milestone 15 is complete because:

- execution assumptions are documented and represented explicitly
- order intent is separated from assumed fills
- deterministic fill price behavior exists under explicit timing assumptions
- execution-adjusted trade summaries are reviewable
- execution realism can be represented in a standalone in-memory artifact
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 15 prepares the project for Milestone 16 — Paper Trading Foundation planning.

Paper trading should wait until backtest execution assumptions are explicit. Otherwise, paper trading can look like progress while hiding a mismatch between research assumptions and later execution behavior.

## Current Next Step

```text
Milestone 16 — Paper Trading Foundation planning
```

Start by planning the paper-trading boundary without assuming broker integration or live execution is already safe.
