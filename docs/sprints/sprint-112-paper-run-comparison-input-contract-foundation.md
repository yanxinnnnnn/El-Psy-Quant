# Sprint 112 — Paper Run Comparison Input Contract Foundation

## Status

Complete.

## Goal

Add the smallest typed input contract for explicitly grouping paper run references for manual comparison review.

Sprint 112 builds on Sprint 111 paper run references. It defines what paper runs should be compared and why, but it does not discover runs automatically, load artifacts, compare metrics, score runs, generate summaries, create review decisions, render reports, execute paper workflows, or claim live or real-money readiness.

## Delivered

- Added `PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION`.
- Added immutable `PaperRunComparisonInput`.
- Added `create_paper_run_comparison_input(...)`.
- Required explicit `comparison_id`, non-empty `paper_run_references`, and `purpose`.
- Rejected a bare `PaperRunReference` where a sequence is required.
- Added optional normalized `review_context`, `requested_by`, and `created_timestamp` fields.
- Added deterministic, JSON-compatible `to_dict()` output with nested paper run reference exports.
- Exported the comparison input public API through `el_psy_quant.paper_review`.
- Added tests for valid creation, validation failures, normalization, timestamp behavior, deterministic export, immutability, package exports, and forbidden runtime behavior boundaries.

## Export Shape

```json
{
  "schema_version": 1,
  "comparison_id": "comparison-1",
  "paper_run_references": [
    {
      "schema_version": 1,
      "reference_type": "paper_result_summary",
      "reference": "outputs/run-1/paper/paper_run_result_summary.json",
      "run_id": "run-1",
      "artifact_id": "paper_result_summary",
      "label": "run-1 paper_result_summary",
      "description": null
    }
  ],
  "purpose": "Compare completed paper runs for manual review.",
  "review_context": "Milestone 21 review",
  "requested_by": "reviewer-1",
  "created_timestamp": "2026-01-02T03:04:05"
}
```

## Boundary

This sprint does not add:

- paper workflow execution changes
- configured paper workflow behavior changes
- automatic paper run discovery
- artifact loading, parsing, or scoring
- metric comparison
- comparison summary generation
- review decision records
- review manifests
- dashboard behavior
- plotting behavior
- broad report generation
- database behavior
- hosted services or SaaS behavior
- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- scheduler behavior
- real account synchronization
- automatic capital deployment decisions
- live-readiness claims
- real-money readiness claims
- strategy expansion

## Next Step

Sprint 113 — Paper Run Comparison Summary Foundation should add deterministic caller-supplied comparison facts, assumptions, warnings, and missing-evidence fields without dashboards, plotting, broad reports, scoring, or artifact loading.
