# Milestone 12 — Data Integrity & Universe Foundation

## Status

Complete.

## Product Goal

Make local research inputs harder to misuse before the project adds more strategies or portfolio construction.

Milestone 11 established the strategy boundary. Milestone 12 strengthened the input boundary that feeds it.

## Outcome

Milestone 12 closed the configured input-validation chain:

```text
configured symbols -> local price data -> configured input validation -> strategy execution
```

The project now has explicit local boundaries for:

- daily price DataFrame structure
- research symbol universe normalization
- configured-run input validation before strategy execution

This does not make market data perfect. It makes bad local inputs harder to pass silently into strategy code.

## Sprint History

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S53 | Complete | Plan Milestone 12. | Data integrity and universe milestone scope. | No implementation during planning. |
| S54 | Complete | Validate local price data. | `validate_daily_prices(...)` and required OHLCV structure checks. | No live data or external validation. |
| S55 | Complete | Define symbol universe discipline. | `normalize_symbol(...)` and `build_symbol_universe(...)`. | No investable universe database. |
| S56 | Complete | Wire configured input validation. | Configured runs validate symbols and prices before strategy execution. | Preserve artifact schemas and CLI shape. |
| S57 | Complete | Close milestone. | Milestone 12 documentation refresh. | No scope expansion. |

## What Changed

### Price Data Validation

Milestone 12 added a reusable daily price validation boundary.

It checks that loaded local price data is structurally usable before it is trusted by higher-level workflows:

- input is a pandas DataFrame
- DataFrame is not empty
- required OHLCV columns exist
- index is a `DatetimeIndex`
- index has no missing dates
- index has no duplicate dates
- `Close` has no missing values
- `Close` is numeric

The helper validates structure only. It does not download, sort, fill, coerce, or repair data.

### Symbol Universe Boundary

Milestone 12 added a small local research symbol-universe boundary.

It makes symbol handling explicit:

- strip surrounding whitespace
- uppercase symbols
- reject blank symbols
- reject duplicates after normalization
- preserve configured order
- return an immutable tuple

This is a research input list, not an investable universe database, benchmark universe, security master, or live symbol service.

### Configured Run Input Validation

Configured experiments now explicitly validate loaded inputs before strategy resolution and `Strategy.run(...)`.

Invalid configured price data fails before strategy logic runs, with symbol-qualified error context. Valid configured runs preserve existing artifact contracts and output semantics.

## Current Architecture Path

A configured local experiment now follows this input path:

```text
YAML config
-> validated ExperimentConfig
-> normalized configured symbols
-> local CSV/cache price DataFrames
-> validate_daily_prices_by_symbol(...)
-> resolve_strategy(config.strategy)
-> Strategy.run(prices, parameters)
-> summary.csv / metrics.json / manifest.json
```

## Existing Artifact Contracts Preserved

Milestone 12 did not change the configured-run artifact layout:

```text
config.yaml
metadata.json
manifest.json
results/summary.csv
results/metrics.json
logs/
```

It also did not change schema versions, summary columns, strategy semantics, resolver behavior, or CLI shape.

## Deliberately Not Added

Milestone 12 deliberately avoided:

- new trading strategies
- strategy protocol changes
- resolver changes
- artifact schema changes
- CLI redesign
- portfolio construction
- investable universe database
- security master
- sector, exchange, country, or asset-class metadata
- live symbol lookup
- external data validation service
- databases or dashboards
- live or paper trading
- plugin frameworks
- dynamic imports
- parameter search or optimization

## Why This Matters

Before this milestone, local inputs could be normalized or checked in scattered places. After this milestone, the project has clearer input boundaries that can be reused as the platform grows.

That matters because portfolio construction is sensitive to hidden symbol and price-data assumptions. Milestone 12 reduces those assumptions before the project starts combining independent symbol results into portfolio-level logic.

## Relationship To Future Milestones

Milestone 12 prepares the project for Milestone 13 by improving input trust.

Milestone 13 can now plan portfolio construction on top of clearer assumptions about:

- which symbols are included
- whether symbol names are normalized consistently
- whether local price data is structurally valid
- whether configured runs fail before strategy execution when inputs are invalid

## Current Next Step

The next sprint should be:

```text
Sprint 58 — Milestone 13 Planning
```

Start by planning Portfolio Construction Foundation. Do not implement portfolio allocation before defining the portfolio boundary, capital assumptions, alignment rules, and out-of-scope constraints.
