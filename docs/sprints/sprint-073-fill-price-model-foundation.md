# Sprint 73 — Fill Price Model Foundation

## Objective

Add a local deterministic fill price model that converts an `OrderIntent` into
an assumed fill under explicit `ExecutionAssumptions`.

## Delivered Scope

Sprint 73 adds `AssumedFill` and `fill_order_intent(...)` in
`el_psy_quant.execution`.

The helper answers one local backtest question:

```text
Given an order intent and local OHLC bar data, which timestamp and price would
the backtest assume for the fill?
```

## Assumed Fill Versus Order Intent

An order intent records what a strategy wants to do.

An assumed fill records the deterministic local backtest assumption for when and
where that intent would fill.

This sprint does not claim real execution occurred. It does not model liquidity,
partial fills, order-book queue position, broker behavior, exchange matching, or
market microstructure.

## `same_bar` Behavior

When `ExecutionAssumptions.timing == "same_bar"`, the fill model uses the bar at
the order intent timestamp.

If that timestamp is unavailable in the local OHLC data, the helper raises
`ValueError`.

## `next_bar` Behavior

When `ExecutionAssumptions.timing == "next_bar"`, the fill model uses the first
bar strictly after the order intent timestamp.

If no later bar is available, the helper raises `ValueError`.

## Price Field Selection

The fill model uses the `price_field` recorded on the execution assumptions:

- `open` uses `Open`
- `high` uses `High`
- `low` uses `Low`
- `close` uses `Close`

The selected price column must exist and contain numeric values.

## Missing Price Behavior

Sprint 73 supports the existing conservative missing price policy:

```text
raise
```

Missing or non-finite fill prices raise `ValueError`.

## Representation

`AssumedFill.to_dict()` returns a deterministic JSON-compatible dictionary with
ISO-formatted timestamps, symbol, side, quantity, price, price field, and the
attached execution assumptions.

## Out of Scope

- Execution-adjusted trade summaries.
- Execution realism artifacts.
- YAML, CLI, manifest, metrics, or configured-run schema changes.
- Broker, exchange, paper-trading, or live-trading integration.
- Order routing or market data streaming.
- Market microstructure, liquidity, partial-fill, or order-book models.
- Dynamic portfolio rebalancing or optimization.
- Strategy, resolver, or plugin-framework changes.
