# Sprint 139 — Strategy Catalog and Detail Read Services

## Status

Complete.

## Objective

Add the first thin Milestone 26 application read service and versioned read-only API endpoints for built-in strategy list and detail views.

## Delivered

- immutable `StrategyParameterDefinition`, `StrategySummary`, and `StrategyDetail` read models
- deterministic `list_strategies()` and exact-name `get_strategy_detail()` services
- explicit `StrategyNotFoundError` behavior
- built-in metadata aligned exactly with `supported_strategy_names()`
- moving-average parameter order, required flags, and defaults derived from `MovingAverageCrossoverParameters`
- explicit Pydantic strategy list/detail response schemas
- `GET /api/v1/strategies`
- `GET /api/v1/strategies/{strategy_name}`
- stable Sprint 138 request IDs and 404 error envelopes for unknown names

## Catalog Boundary

The catalog contains built-in supported strategy definitions only and currently contains exactly `moving_average_crossover`. Catalog order follows `supported_strategy_names()` exactly. Names are exact: case and whitespace variants are not normalized.

Parameter metadata is descriptive only. Existing configuration and domain validation remain authoritative for positive values, window ordering, initial capital, transaction costs, and slippage constraints.

The catalog does not execute strategies, discover configured experiments, scan modules or files, load configuration, inspect research or backtest artifacts, access market data or networks, expose metrics or rankings, infer lifecycle state, run paper workflows, persist data, submit background jobs, or imply approval, profitability, broker/QMT/live readiness, or capital allocation.

## Next Step

```text
Sprint 140 — Research and Backtest Artifact Inspection Services
```
