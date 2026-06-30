# Sprint 33 — Experiment Config Foundation

## Objective

Add a small YAML-based local experiment configuration foundation for existing
moving-average crossover research workflows.

## Product Goal

Local experiments should be describable in a human-readable file so repeated
research can become configurable and reproducible before output layouts or CLI
wrappers are introduced.

## Implementation Scope

- Add typed experiment, data, strategy-parameter, and evaluation dataclasses.
- Load local YAML with PyYAML's safe loader.
- Support local CSV path mappings and local cache symbol lists.
- Normalize symbols while preserving input order.
- Validate the currently supported `moving_average_crossover` strategy fields.
- Document the YAML format and public loader.

## Validation

- Required sections and fields are explicit.
- CSV and cache inputs are local-only and mutually selected by `data.source`.
- Moving-average windows, capital, cost, slippage, and evaluation frequency are
  validated before later workflows consume the config.
- Tests use temporary local YAML files and make no network calls.

## Out of Scope

- TOML support.
- Strategy execution or parameter-sweep changes.
- CLI commands or output folder layouts.
- Databases, schedulers, dashboards, cloud features, or file exports.
- Live downloads, provider changes, benchmarks, or portfolio construction.

## Acceptance Criteria

- YAML configs load into typed dataclasses through `load_experiment_config`.
- Invalid documents, symbols, sources, and numeric parameters are rejected.
- `uv run pytest` and `uv run ruff check .` pass.
- README briefly documents the local YAML foundation and its limitations.
