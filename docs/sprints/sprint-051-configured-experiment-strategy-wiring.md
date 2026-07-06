# Sprint 51 — Configured Experiment Strategy Wiring

## Objective

Route configured experiments through the strategy resolver and interface.

## Product Goal

Configured runs should depend on the established strategy boundary instead of
calling moving-average multi-symbol implementation details directly.

## Implementation Scope

- Resolve the validated configured strategy name exactly once per run.
- Build an explicit mapping of the five existing strategy parameters.
- Execute the resolved strategy independently for each configured symbol.
- Preserve input symbol order, summary generation, and every existing artifact.
- Keep existing configuration validation and CLI behavior unchanged.

## Behavior Preservation

The configured moving-average path produces the same pipeline results, summary
rows, metadata, manifest, metrics, filenames, and schema versions as before.

## Out of Scope

- New strategies, configuration fields, parameter models, or CLI commands.
- Artifact schema, optimization, ranking, portfolio, plugin, or trading changes.
- Rewrites of existing pipelines, multi-symbol helpers, or summary functions.

## Acceptance Criteria

- Configured runs resolve `config.strategy` through the resolver.
- Each symbol executes through `Strategy.run` with the existing parameters.
- Current moving-average results and artifacts remain stable.
- Unsupported strategy spellings remain rejected without loose matching.
