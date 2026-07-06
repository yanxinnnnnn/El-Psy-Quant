# Sprint 62 — Portfolio Summary Artifact Foundation

## Objective

Add standalone portfolio summary and machine-readable artifact support.

## Product Goal

Portfolio return series should produce compact, inspectable summaries that
record construction inputs, evaluation assumptions, and existing metrics.

## Implementation Scope

- Validate standalone portfolio return Series inputs.
- Adapt returns locally to existing equity and backtest summary helpers.
- Normalize ordered construction symbols and optionally validate static weights.
- Build versioned, JSON-compatible portfolio summary artifacts.
- Write deterministic JSON to caller-supplied local paths.

## Artifact Discipline

The artifact records existing portfolio construction and metric results only.
Omitted weights remain `null`; equal weights are not inferred or serialized.

## Out of Scope

- Configured-run, YAML, manifest, metrics, output-layout, or CLI integration.
- Optimization, dynamic weights, rebalancing, cash, costs, or risk attribution.
- Databases, dashboards, plugins, benchmarks, or trading integration.

## Acceptance Criteria

- Portfolio returns produce existing summary metrics with optional annualization.
- Artifacts preserve normalized symbol and static-weight order.
- Artifacts are deterministic and JSON-serializable.
- The standalone writer creates directories and writes a trailing newline.
