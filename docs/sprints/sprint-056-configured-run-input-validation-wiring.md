# Sprint 56 — Configured Run Input Validation Wiring

## Objective

Validate configured symbol and price inputs before strategy execution.

## Product Goal

Configured experiments should fail early with clear symbol-qualified errors
rather than allowing malformed local inputs to reach strategy logic.

## Implementation Scope

- Validate loaded symbol keys through the local research universe boundary.
- Validate every loaded price DataFrame through the structural price boundary.
- Preserve configured order and add symbol context to price validation errors.
- Run validation before strategy resolution and `Strategy.run`.
- Reuse symbol-universe normalization in CSV and cache config parsing.

## Behavior Preservation

Valid configured runs retain the same strategy results, summaries, artifacts,
filenames, schema versions, CLI arguments, and run layout.

## Out of Scope

- Artifact, strategy, resolver, protocol, or summary changes.
- CLI redesign, portfolio construction, symbol metadata, or external services.
- Databases, dashboards, plugins, optimization, or trading systems.

## Acceptance Criteria

- Configured inputs are explicitly validated before strategy resolution.
- Invalid prices fail with symbol context and do not execute strategy logic.
- Config parsing shares the established symbol-universe rules.
- Valid configured artifact semantics remain stable.
