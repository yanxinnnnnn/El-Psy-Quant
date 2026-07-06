# Sprint 43 — Experiment Run Manifest Foundation

## Objective

Add a small machine-readable manifest to each configured local experiment run.

## Product Goal

A saved run directory should explain what experiment ran, which assumptions
were used, and where its artifacts live without relying on machine-specific
absolute paths.

## Implementation Scope

- Reserve `manifest.json` in `ExperimentOutputLayout`.
- Write a versioned manifest from the configured experiment flow.
- Record experiment identity, strategy, run ID, data source, symbols,
  parameters, and evaluation assumptions.
- Record config, metadata, summary, and logs paths relative to the run directory.
- Keep the existing `metadata.json` artifact for compatibility.

## Manifest Discipline

The manifest is explicit JSON with `schema_version: 1`. It describes one run
and its local artifacts; it is not a registry, storage layer, or report.

## Out of Scope

- Databases, dashboards, cloud storage, or experiment registries.
- Comparison engines, reports, new metrics, or new strategies.
- Trading logic, portfolio behavior, or broad CLI changes.

## Acceptance Criteria

- Output layouts expose `manifest_path`.
- Configured runs write `manifest.json` with the required run assumptions.
- Every artifact path in the manifest is relative to the run directory.
- Existing metadata and result artifacts remain available.
