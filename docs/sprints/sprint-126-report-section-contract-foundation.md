# Sprint 126 — Report Section Contract Foundation

## Status

Complete.

## Goal

Add a small report section contract under the existing report-artifact package.

Sprint 126 defines caller-supplied report sections that may explicitly include `ReportSourceReference` values. A report section is structure only. It does not discover, load, parse, score, render, validate, or otherwise inspect the referenced records.

## Delivered

- Added `ReportSection`.
- Added `REPORT_SECTION_SCHEMA_VERSION`.
- Added `create_report_section(...)`.
- Exported the public API from `el_psy_quant.report_artifacts`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty section IDs
  - non-empty titles
  - non-empty caller-supplied content
  - optional `section_type` and `notes` normalization
  - explicit `ReportSourceReference` source references
  - immutable source-reference sequences
- Added tests for valid sections with and without source references, normalization, invalid inputs, deterministic export, source-reference serialization, immutability, package exports, and guardrails.

## Section Shape

The section payload includes:

```text
schema_version
section_id
title
content
source_references
section_type
notes
```

Nested source references are exported through `ReportSourceReference.to_dict()`.

## Scope Guardrails

Sprint 126 does not add:

- report artifact summaries
- report manifests
- report rendering
- dashboards
- broad report generation
- markdown, HTML, PDF, notebook, or hosted report generation
- artifact loading or parsing
- automatic evidence discovery
- scoring, ranking, or recommendations
- automatic decision making
- workflow execution
- file I/O, persistence services, or database behavior
- broker, live, or capital deployment behavior
- live-readiness or real-money-readiness claims

## Next Step

```text
Sprint 127 — Report Artifact Summary Foundation
```

Sprint 127 should add a deterministic caller-supplied report artifact summary without automatic metric calculation, recommendation, ranking, dashboards, reports, workflow execution, broker behavior, or readiness claims.
