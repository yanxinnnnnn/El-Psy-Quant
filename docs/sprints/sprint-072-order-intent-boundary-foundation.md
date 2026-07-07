# Sprint 72 — Order Intent Boundary Foundation

## Objective

Add a deterministic order-intent boundary on top of explicit execution
assumptions.

## Delivered Scope

Sprint 72 adds `OrderIntent` and `validate_order_intent(...)` in
`el_psy_quant.execution`.

An order intent records what a strategy wants to do:

- when the intent occurs
- which symbol it targets
- whether it wants to buy or sell
- the requested positive quantity
- the execution assumptions attached to the intent

## Intent Versus Fill

An order intent is not a fill.

It does not decide:

- whether the order filled
- what price was used
- which bar supplied the price
- whether liquidity was available
- what execution-adjusted trade summary should be produced

Those decisions belong to later Milestone 15 sprints.

## Accepted Sides

Supported sides:

- `buy`
- `sell`

Side values are trimmed and lowercased. Unsupported sides raise `ValueError`.

## Symbol And Quantity Assumptions

Symbols are normalized through the existing local symbol boundary, so leading
and trailing whitespace is stripped and symbols are uppercased.

Quantities must be positive real numbers. Boolean, zero, negative, missing,
infinite, or non-numeric quantities are rejected.

## Timestamp Serialization

Timestamps are normalized to `pandas.Timestamp` when possible.

`OrderIntent.to_dict()` serializes timestamps with `Timestamp.isoformat()` so
the JSON-compatible representation is deterministic.

## Execution Assumptions Relationship

Each order intent carries an `ExecutionAssumptions` object.

If assumptions are omitted, the conservative default execution assumptions are
used:

```text
next_bar + open + raise
```

## Out of Scope

- Fill models or fill price lookup.
- Execution-adjusted trade summaries.
- Execution realism artifacts.
- YAML, CLI, manifest, metrics, or configured-run schema changes.
- Broker, exchange, paper-trading, or live-trading integration.
- Order routing or market data streaming.
- Dynamic portfolio rebalancing or optimization.
- Strategy, resolver, or plugin-framework changes.
