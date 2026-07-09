# Sprint 127 — Report Artifact Summary Foundation

## Status

Complete.

## Goal

Add a small report artifact summary contract under the existing report-artifact package.

Sprint 127 defines caller-supplied report artifact summaries that group explicit `ReportSection` values. A report artifact summary is descriptive structure only. It does not discover sources, load artifacts, calculate metrics, score, rank, recommend, render, or generate reports.

## Delivered

- Added `ReportArtifactSummary`.
- Added `REPORT_ARTIFACT_SUMMARY_SCHEMA_VERSION`.
- Added `create_report_artifact_summary(...)`.
- Exported the public API from `el_psy_quant.report_artifacts`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty report IDs
  - non-empty titles
  - non-empty explicit report sections
  - optional report metadata normalization
  - explicit `ReportSection` inputs
  - immutable section sequences
- Added tests for valid summaries with one or multiple sections, normalization, invalid inputs, deterministic export, nested section serialization, immutability, package exports, and guardrails.

## Summary Shape

The report artifact summary payload includes:

```text
schema_version
report_id
title
sections
summary
purpose
created_by
created_timestamp
notes
```

Nested sections are exported through `ReportSection.to_dict()`.

## Scope Guardrails

Sprint 127 does not add:

- report manifests
- report rendering
- dashboards
- broad report generation
- markdown, HTML, PDF, notebook, or hosted report generation
- artifact loading or parsing
- automatic evidence discovery
- metric calculation
- scoring, ranking, or recommendations
- automatic decision making
- workflow execution
- file I/O, persistence services, or database behavior
- broker, live, or capital deployment behavior
- live-readiness or real-money-readiness claims

## Next Step

```text
Sprint 128 — Report Manifest and References Foundation
```

Sprint 128 should add local report manifest and reference contracts without file I/O, database behavior, dashboards, report engines, workflow execution, broker behavior, or readiness claims.
