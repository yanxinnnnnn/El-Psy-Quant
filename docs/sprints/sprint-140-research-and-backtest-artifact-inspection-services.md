# Sprint 140 — Research and Backtest Artifact Inspection Services

## Status

Complete.

## Objective

Add a thin, secure, read-only application service and versioned API for inspecting existing configured research-run manifests and saved metrics.

## Configuration and Endpoints

The local root is server configuration only:

```text
EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT
```

An explicit `create_app(research_artifact_root=...)` override takes precedence. Application construction stores the value without filesystem discovery; the root is checked only when a research endpoint is called.

```text
GET /api/v1/research-runs
GET /api/v1/research-runs/{experiment_slug}/{run_id}
```

The list inspects direct experiment/run children and reads fixed `manifest.json` files only. Detail reads the selected fixed manifest and its single safely contained `artifacts.metrics` JSON file.

## Security and Artifact Boundary

Experiment slugs and run IDs use exact restricted vocabularies and are never normalized into paths. Symlinked experiment/run directories, manifests, metrics files, and symlink components are excluded or rejected. Absolute references, `..`, Windows-drive forms, backslashes, and resolved paths outside the selected run are rejected. API errors are sanitized and never expose the configured root or absolute paths.

Only manifest schema version 1 and metrics schema version 1 are supported. Product read models expose explicit validated fields and immutable tuples. Unknown artifact fields do not leak. Saved metrics are not recomputed, reinterpreted, aggregated, compared, or ranked.

The service does not read `config.yaml`, `metadata.json`, `summary.csv`, logs, or raw outputs. It adds no artifact downloads, governance inspection, paper actions, lifecycle actions, persistence, repositories, jobs, UI, broker, QMT, live, or real-money behavior.

## Next Step

```text
Sprint 141 — Governance, Report, and Lifecycle Evidence Inspection Services
```
