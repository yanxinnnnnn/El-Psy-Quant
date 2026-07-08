# Sprint 113 — Paper Run Comparison Summary Foundation

## Status

Complete.

## Goal

Add the smallest deterministic paper run comparison summary contract for caller-supplied paper run comparison facts.

This sprint builds on Sprint 112 `PaperRunComparisonInput` and keeps the boundary local, immutable, descriptive, and explicit-input driven.

## Delivered

- Added `PaperRunComparisonSummary`.
- Added `PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION`.
- Added `create_paper_run_comparison_summary(...)`.
- Exported the summary contract from `el_psy_quant.paper_review`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty summary IDs
  - `PaperRunComparisonInput` inputs
  - non-empty caller-supplied comparison facts
  - optional assumptions, warnings, and missing-evidence notes
  - optional reviewer context
  - optional timestamp normalization
- Added tests for validation, immutability, JSON compatibility, package exports, and scope guardrails.

## Summary Shape

The summary export includes:

```text
schema_version
summary_id
comparison_input
comparison_facts
assumptions
warnings
missing_evidence
created_by
created_timestamp
```

The nested comparison input is exported through its existing `to_dict()` boundary.

## Scope Guardrails

Sprint 113 does not add:

- automatic paper run discovery
- artifact loading or parsing
- metric calculation
- metric comparison
- scoring
- ranking
- winner selection
- review decisions
- report generation
- dashboards
- workflow execution
- broker or live behavior
- live-readiness or real-money readiness claims

The comparison summary is descriptive context supplied by the caller. It is not an approval, ranking, deployment decision, or scoring engine.

## Next Step

```text
Sprint 114 — Paper Run Review Decision Record Foundation
```

Sprint 114 should add human-controlled paper run review decision records tied to comparison summaries without automatic approval, ranking, capital deployment, broker behavior, or readiness claims.
