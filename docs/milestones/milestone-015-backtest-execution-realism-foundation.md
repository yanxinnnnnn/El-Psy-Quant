# Milestone 15 — Backtest Execution Realism Foundation

## Status

Planned.

## Product Goal

Make backtests less idealized by making execution assumptions explicit, deterministic, and reviewable.

Milestone 14 made portfolio behavior explainable. Milestone 15 should now explain how research signals or trades become assumed fills in a backtest before the project moves toward paper trading.

## Why This Comes Now

Milestone 14 closed this chain:

```text
portfolio_return -> risk metrics
portfolio_equity -> drawdown inspection
aligned_returns + static_weights -> symbol contribution
risk + drawdown + contribution -> attribution summary artifact
```

Execution realism should come after portfolio behavior is explainable. Fill timing, fill prices, and trade assumptions can change results materially. Those assumptions should be isolated and documented before they are allowed to influence more advanced workflows.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S70 | Complete | Plan Milestone 15. | Execution realism scope and sprint sequence. | No implementation during planning. |
| S71 | Planned | Define execution assumptions. | Small documented execution assumption boundary. | No broker integration. |
| S72 | Planned | Add order intent boundary. | Deterministic order-intent representation from existing research outputs. | No live orders. |
| S73 | Planned | Add fill price model. | Local deterministic fill model under explicit timing assumptions. | No market microstructure simulation. |
| S74 | Planned | Add execution-adjusted trade summary. | Reviewable summary of fills and execution assumptions. | No portfolio rebalancing engine. |
| S75 | Planned | Add execution realism artifact. | Standalone artifact tying assumptions to results. | No broad configured-run expansion. |
| S76 | Planned | Close milestone. | Milestone 15 documentation refresh. | No scope expansion. |

## Planned Work

### Execution Assumptions

The first implementation sprint should define the smallest useful execution-assumption boundary.

The project should be able to record assumptions such as:

- when an order is assumed to execute
- which price field is assumed to fill
- whether fills happen on the same bar or next bar
- how missing or invalid fill prices are handled

This should be explicit configuration or data passed to helpers, not hidden behavior.

### Order Intent Boundary

The project should separate order intent from filled trades.

An order intent records what the strategy wanted to do. A fill records what the backtest assumes actually happened. This distinction keeps execution assumptions reviewable.

The initial boundary should remain deterministic and local.

### Fill Price Model

The fill model should be small and deterministic.

It should answer:

- what timestamp was used for the fill
- what price was used for the fill
- why that price was valid
- what assumption produced the fill

It should not pretend to simulate an exchange or market microstructure.

### Execution-Adjusted Trade Summary

Once fills exist, the project should summarize them in a reviewable form.

The summary should help a reviewer compare intended trades, assumed fills, and resulting costs or returns where scoped.

### Execution Realism Artifact

Execution assumptions and their resulting summaries should become portable through a small standalone artifact.

The artifact should follow the existing project pattern: deterministic, local, JSON-compatible, and easy to inspect.

## Assumptions

Milestone 15 keeps the assumptions conservative:

- backtest inputs already exist before execution assumptions are applied
- order intent is separate from assumed fills
- fill timing is explicit
- fill price selection is explicit
- all behavior is deterministic and local
- no external broker, exchange, or streaming dependency is introduced

## Guardrails

Milestone 15 should avoid:

- broker integration
- paper trading behavior
- live trading behavior
- exchange APIs
- order routing
- market data streaming
- market microstructure simulation
- dynamic portfolio rebalancing
- optimization
- dashboards or databases
- broad configured-run integration unless explicitly scoped later
- YAML or CLI expansion unless the helper boundary is already stable
- strategy proliferation
- plugin frameworks or dynamic loading

## Exit Criteria

Milestone 15 is complete when:

- execution assumptions are documented and represented explicitly
- order intent is separated from assumed fills
- deterministic fill price behavior exists under explicit timing assumptions
- execution-adjusted trade summaries are reviewable
- execution realism outputs can be summarized in a standalone artifact
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 15 prepares the project for Milestone 16 — Paper Trading Foundation.

Paper trading should wait until backtest execution assumptions are explicit. Otherwise, paper trading can look like progress while hiding a mismatch between research assumptions and actual trading behavior.

## Current Next Step

```text
Sprint 71 — Execution Assumptions Foundation
```

Start by defining the execution-assumption boundary before adding order intent or fill models.