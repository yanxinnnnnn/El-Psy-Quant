# Sprint 115 — Review Manifest and Comparison References Foundation

## Status

Complete.

## Goal

Add local in-memory paper review manifests and compact comparison/review references for manual inspection.

This sprint builds on Sprint 114 `PaperRunReviewDecision` and keeps the boundary immutable, deterministic, explicit, and local.

## Delivered

- Added `PaperReviewReference`.
- Added `PaperReviewManifest`.
- Added `PAPER_REVIEW_REFERENCE_SCHEMA_VERSION`.
- Added `PAPER_REVIEW_MANIFEST_SCHEMA_VERSION`.
- Added `SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES`.
- Added `create_paper_review_reference(...)`.
- Added `create_paper_review_manifest(...)`.
- Added pure convenience helpers for references from existing comparison summaries and review decisions.
- Exported the manifest/reference contracts from `el_psy_quant.paper_review`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added tests for validation, normalization, timestamp export, immutability, JSON compatibility, package exports, and scope guardrails.

## Supported Reference Types

```text
comparison_summary
review_decision
```

These references identify existing in-memory review-layer records by ID. They do not load, parse, write, persist, or discover anything.

## Manifest Shape

The manifest export includes:

```text
schema_version
manifest_id
comparison_references
decision_references
created_by
created_timestamp
description
```

The manifest must contain at least one comparison summary reference or review decision reference.

## Scope Guardrails

Sprint 115 does not add:

- file writing
- file reading
- filesystem scanning
- persistence
- database behavior
- dashboards
- reports
- workflow execution
- broker or live behavior
- approval automation
- capital allocation
- order routing
- live-readiness or real-money readiness claims

The manifest is an in-memory/local contract for manual inspection. It is not a database row, report, dashboard, workflow runner, approval record, or readiness certificate.

## Next Step

```text
Sprint 116 — Milestone 21 Documentation Refresh / Closeout
```

Sprint 116 should close Milestone 21 with documentation refresh only, preserving the paper run comparison and review guardrails.
