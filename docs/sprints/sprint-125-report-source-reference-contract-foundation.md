# Sprint 125 — Report Source Reference Contract Foundation

## Status

Complete.

## Goal

Add the smallest useful report source reference contract under a new report-artifact package.

Sprint 125 defines typed pointers to completed governance records that future deterministic report artifacts may reference. A report source reference is only a pointer. It does not discover, load, parse, score, rank, summarize, render, or validate the referenced record.

## Delivered

- Added `el_psy_quant.report_artifacts`.
- Added `ReportSourceReference`.
- Added `REPORT_SOURCE_REFERENCE_SCHEMA_VERSION`.
- Added `SUPPORTED_REPORT_SOURCE_REFERENCE_TYPES`.
- Added `create_report_source_reference(...)`.
- Exported the public API from `el_psy_quant.report_artifacts`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - supported source reference types
  - non-empty reference IDs
  - optional label and description normalization
  - immutable source reference records
- Added tests for valid creation, supported type coverage, normalization, invalid inputs, deterministic export, JSON compatibility, package exports, immutability, and guardrails.

## Supported Source Types

Sprint 125 supports completed governance-layer references only:

```text
promotion_evidence_summary
promotion_record
promotion_manifest
paper_comparison_summary
paper_review_decision
paper_review_manifest
strategy_decision_summary
strategy_decision_record
strategy_decision_manifest
```

## Source Reference Shape

The source reference payload includes:

```text
schema_version
reference_type
reference_id
label
description
```

## Scope Guardrails

Sprint 125 does not add:

- report sections
- report artifact summaries
- report manifests
- report rendering
- dashboards
- broad report generation
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
Sprint 126 — Report Section Contract Foundation
```

Sprint 126 should add a small report section contract without rendering pipelines, dashboards, markdown/PDF generation, workflow execution, broker behavior, or readiness claims.
