# Sprint 48 — Strategy Interface Contract Foundation

## Objective

Define the smallest useful structural contract for research strategies.

## Product Goal

Future strategies should share an explicit input and output boundary before the
project adds more implementations or configuration wiring.

## Implementation Scope

- Add a runtime-checkable `Strategy` protocol with a name and `run` method.
- Accept a price DataFrame and a mapping of strategy parameters.
- Return a pipeline result DataFrame compatible with existing summary logic.
- Validate only DataFrame type, non-empty results, `equity`, and
  `strategy_return`.
- Continue to allow optional `net_strategy_return` output.

## Contract Discipline

The contract defines structure, not strategy quality. It does not evaluate
performance, validate parameters, calculate metrics, or select strategies.

## Out of Scope

- New strategies or moving-average crossover migration.
- Strategy resolvers, registries, config wiring, or CLI changes.
- Optimization, ranking, artifact changes, plugins, or trading systems.

## Acceptance Criteria

- The strategy contract and validation helper are importable.
- Structural implementations satisfy the protocol.
- Valid result DataFrames pass shape validation.
- Empty, non-DataFrame, or incomplete results raise `ValueError`.
