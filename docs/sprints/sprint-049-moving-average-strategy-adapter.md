# Sprint 49 — Moving-Average Strategy Adapter

## Objective

Adapt the existing moving-average crossover pipeline to the Strategy contract.

## Product Goal

The current strategy should become a first-class structural implementation that
future strategy integrations can follow without changing established results.

## Implementation Scope

- Add `MovingAverageCrossoverStrategy` with the existing strategy name.
- Accept a price DataFrame and the existing parameter mapping.
- Require the existing `Close` input column.
- Delegate directly to `moving_average_crossover_pipeline`.
- Preserve current defaults for capital, transaction cost, and slippage.
- Validate and return the existing pipeline result unchanged.

## Behavior Preservation

The adapter does not implement indicators, signals, positions, returns, costs,
or equity. It adds, removes, sorts, and transforms nothing in the pipeline result.

## Out of Scope

- New strategies, resolvers, registries, config wiring, or CLI changes.
- Artifact, metric, optimization, ranking, or parameter-search changes.
- Portfolio construction, databases, dashboards, plugins, or trading systems.

## Acceptance Criteria

- The adapter is importable and structurally satisfies `Strategy`.
- Its name is `moving_average_crossover`.
- Its columns, index, and values match the existing pipeline.
- Missing `Close` input raises `ValueError`.
- Its output passes strategy result validation.
