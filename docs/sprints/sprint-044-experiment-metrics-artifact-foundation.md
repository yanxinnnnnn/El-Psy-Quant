# Sprint 44 — Experiment Metrics Artifact Foundation

## Objective

Add a machine-readable metrics artifact to each configured local experiment run.

## Product Goal

A saved run should expose its existing per-symbol summary metrics as JSON so
later tooling can consume them without parsing CSV or recomputing results.

## Implementation Scope

- Reserve `results/metrics.json` in `ExperimentOutputLayout`.
- Serialize metric records directly from the existing summary DataFrame.
- Record the run ID and run-relative `results/summary.csv` source path.
- Add the run-relative metrics path to the manifest artifact map.
- Keep `summary.csv`, `metadata.json`, and all existing artifacts stable.

## Artifact Shape

The metrics artifact uses `schema_version: 1` and contains `run_id`,
`source_artifact`, and the metric records already produced by
`summarize_multi_symbol_results`. It does not calculate or add metrics.

## Out of Scope

- New metrics, strategies, comparison engines, optimization, or ranking.
- Databases, dashboards, cloud storage, reports, or trading logic changes.
- Broad CLI changes.

## Acceptance Criteria

- Output layouts expose `metrics_path`.
- Configured runs write `results/metrics.json` from the existing summary.
- Metrics records match `summary.csv` and contain no absolute artifact paths.
- The manifest points to the run-relative metrics artifact.
