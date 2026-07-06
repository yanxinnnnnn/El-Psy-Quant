# Milestone 11 — Strategy Interface Foundation

## Status

Complete.

Milestone 11 defined how strategies plug into the research system before the project adds more strategies.

## Product Outcome

Configured experiments now move through a small strategy boundary:

```text
Strategy protocol -> concrete strategy adapter -> exact-name resolver -> configured experiment execution
```

The existing moving-average crossover behavior is preserved, but the configured run path no longer needs to know the moving-average implementation details directly.

## Sprint History

| Sprint | Status | Main Deliverable | Guardrail |
|---:|---|---|---|
| S47 | Complete | Milestone 11 planning and scope. | No implementation during planning. |
| S48 | Complete | Minimal `Strategy` protocol and `validate_strategy_result`. | No new strategy. |
| S49 | Complete | `MovingAverageCrossoverStrategy` adapter around the existing pipeline. | Preserve current behavior. |
| S50 | Complete | Exact-name `resolve_strategy` and `supported_strategy_names`. | No plugin framework. |
| S51 | Complete | Configured experiments execute through the resolver and `Strategy.run`. | Preserve artifact outputs. |
| S52 | Complete | Milestone 11 documentation refresh. | No product behavior changes. |

## What Changed

### Strategy Contract

The project now exposes a small strategy contract:

```python
from el_psy_quant.strategies import Strategy, validate_strategy_result
```

A strategy must expose a `name` and a `run(prices, parameters)` method that returns a pandas DataFrame compatible with existing summaries.

The contract is intentionally small. It defines the shape of a strategy without forcing a deep inheritance hierarchy.

### Moving-Average Strategy Adapter

The existing moving-average crossover logic is now available as:

```python
from el_psy_quant.strategies import MovingAverageCrossoverStrategy
```

The adapter delegates to the existing moving-average crossover pipeline and returns the pipeline result unchanged.

### Strategy Resolver

The project now exposes exact-name strategy resolution:

```python
from el_psy_quant.strategies import resolve_strategy, supported_strategy_names
```

The current supported strategy name is:

```text
moving_average_crossover
```

Resolution is deterministic and exact. It does not use fuzzy matching, aliases, dynamic imports, plugins, or filesystem discovery.

### Configured Experiment Wiring

Configured local experiments now resolve `config.strategy` and execute strategy logic through `Strategy.run(...)` for each configured symbol.

The existing artifacts remain stable:

```text
config.yaml
metadata.json
manifest.json
results/summary.csv
results/metrics.json
logs/
```

The milestone changed the execution boundary, not the artifact contract.

## Current Architecture

A configured run now follows this path:

```text
YAML config
-> validated ExperimentConfig
-> local CSV/cache price data
-> resolve_strategy(config.strategy)
-> Strategy.run(prices, parameters) per symbol
-> summarize_multi_symbol_results
-> stable local artifacts
```

This keeps the CLI thin. The CLI still wraps stable functions; it does not become the architecture.

## What Future Strategies Need To Implement

A future strategy should provide:

- a stable `name`
- a `run(prices, parameters)` method
- a DataFrame result with the columns required by `validate_strategy_result`
- deterministic behavior suitable for local tests
- explicit parameter handling

A future strategy should not require changes to experiment artifacts just to be runnable.

## What Was Deliberately Not Added

Milestone 11 deliberately avoided:

- more trading strategies
- a plugin framework
- dynamic imports
- filesystem strategy discovery
- fuzzy matching or aliases
- parameter search
- optimization
- ranking or best-run selection
- portfolio construction
- databases or dashboards
- paper or live trading

This was the right tradeoff. The project needed a strategy seam before strategy proliferation.

## Why This Matters

Before this milestone, configured experiments were still tied directly to moving-average crossover implementation details.

After this milestone, the project has a stable strategy boundary. That makes future strategy work safer because new strategies can fit into a known shape without disturbing configured experiment artifacts or broad CLI behavior.

## Next Milestone Candidate

The next milestone should be:

```text
Milestone 12 — Data Integrity & Universe Foundation
```

The project should improve data validation, symbol universe discipline, and input assumptions before adding more strategies.

## Closeout Note

Milestone 11 is complete because the project can now move through this chain:

```text
strategy contract -> strategy implementation -> strategy resolver -> configured experiment execution
```

That is enough for the strategy interface foundation. Further work belongs in the next milestone, not in this one.
