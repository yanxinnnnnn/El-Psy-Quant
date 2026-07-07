# Sprint 74 — Execution-Adjusted Trade Summary Foundation

## Objective

Add a small deterministic execution-adjusted trade summary for already-created
`AssumedFill` records.

## Delivered Scope

Sprint 74 adds `summarize_assumed_fills(...)` in `el_psy_quant.execution`.

The helper accepts a non-empty sequence of `AssumedFill` objects and returns a
JSON-compatible dictionary describing assumed execution activity.

## Summary Versus Assumed Fill

An `AssumedFill` records one deterministic local fill assumption for one order
intent.

The execution-adjusted trade summary aggregates already-created assumed fills.
It does not create fills, choose prices, calculate returns, update positions, or
track cash.

## Summarized Fields

The summary includes:

- total fill count
- order-preserving unique symbols
- buy and sell fill counts
- buy, sell, and gross quantities
- buy, sell, and gross notional
- order-preserving price-field counts
- order-preserving execution-timing counts
- first and last intent timestamps
- first and last fill timestamps

Timestamps are serialized as deterministic ISO strings.

## Why This Is Not An Artifact Yet

This sprint only defines the in-memory summary boundary.

Persisting execution realism artifacts should happen after the project has the
complete Milestone 15 execution chain available and can record assumptions,
intents, fills, and summaries together.

## Out of Scope

- Execution realism artifacts or artifact writers.
- Configured-run, YAML, CLI, manifest, or metrics schema changes.
- Strategy or resolver changes.
- Real-time execution behavior.
- Market microstructure, liquidity, or partial-fill models.
- Return, position, or cash accounting.
- Broker, exchange, paper-trading, or live-trading integration.
- Database, dashboard, plugin-framework, or dynamic-loading changes.
