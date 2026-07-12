# Sprint 141 — Governance, Report, and Lifecycle Evidence Inspection Services

## Status

Complete.

## Objective

Add a thin, secure, read-only application service and versioned API for inspecting saved top-level decision, report-artifact, and strategy-review workflow manifests.

## Configuration and Layout

The local root is server configuration only:

```text
EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT
```

An explicit `create_app(evidence_artifact_root=...)` override takes precedence. Application construction stores configuration without filesystem discovery. Endpoint calls inspect only:

```text
<evidence-root>/
  strategy-decisions/<artifact-key>.json
  report-artifacts/<artifact-key>.json
  strategy-review/<artifact-key>.json
```

Artifact keys contain only ASCII letters, digits, underscores, and hyphens. They are safe local file selectors and are separate from domain manifest IDs.

## Endpoints

```text
GET /api/v1/evidence-manifests
GET /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
```

The list validates every discoverable direct JSON file in deterministic type/key order. Detail returns an explicit type-specific response for one exact selection. Symlinked categories and discoverable files are rejected, nested files and non-JSON files are ignored, and canonical files remain contained under the configured category and root.

## Domain and Reference Boundary

Only saved JSON representations of `StrategyDecisionManifest`, `ReportArtifactManifest`, and `StrategyReviewWorkflowManifest` are supported. Existing public reference and manifest factories remain authoritative for grouped-reference types, minimum counts, string and timestamp normalization, order, and duplicate preservation. Unknown payload fields do not leak into product read models.

Compact references remain pointers only. The service does not open referenced summaries, records, snapshots, proposals, transition records, or report summaries. It does not validate chain completeness, infer current lifecycle state or approval, render reports, execute workflows or paper commands, write artifacts, persist data, create jobs, add UI behavior, call brokers or QMT, imply live readiness, or allocate capital.

## Next Step

```text
Sprint 142 — Paper Run Application Command Boundary
```
