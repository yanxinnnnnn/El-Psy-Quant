# Sprint 105 — Paper Promotion Candidate Contract Foundation

## Status

Complete.

## Goal

Add the smallest typed contract for grouping one or more promotion source references into an explicit paper-trading candidate for manual review.

Sprint 105 builds on Sprint 104 source references. It represents a candidate, but it does not approve a strategy, construct paper run requests, create paper orders or fills, inspect artifacts, score evidence, or execute paper workflows.

## Delivered

- Added `PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION`.
- Added immutable `PaperPromotionCandidate`.
- Added `create_paper_promotion_candidate(...)`.
- Required explicit `candidate_id`, `title`, and one or more `PromotionSourceReference` objects.
- Added optional normalized `rationale`, `proposed_by`, and `created_timestamp` fields.
- Added deterministic, JSON-compatible `to_dict()` output with nested source reference exports.
- Exported the candidate public API through `el_psy_quant.promotion`.
- Added focused tests for valid creation, validation failures, optional field normalization, timestamp export, deterministic export, immutability, and package exports.

## Candidate Shape

```json
{
  "schema_version": 1,
  "candidate_id": "candidate-1",
  "title": "Review moving-average candidate",
  "rationale": "Stable research and paper evidence.",
  "proposed_by": "analyst",
  "created_timestamp": "2026-01-02T03:04:05",
  "source_references": [
    {
      "schema_version": 1,
      "source_type": "configured_run",
      "reference": "outputs/ma/run-1",
      "run_id": "run-1",
      "artifact_id": "manifest",
      "label": "Configured run",
      "description": null
    }
  ]
}
```

## Boundary

This sprint does not add:

- promotion evidence summaries
- explicit promotion records
- promotion manifest/reference wiring
- artifact loading, parsing, or scoring
- strategy approval logic
- automatic research-to-paper promotion
- automatic strategy-signal-to-order conversion
- construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from candidates
- broker, live, scheduler, database, dashboard, or broad reporting behavior
- strategy expansion
- CLI changes

## Next Step

Sprint 106 — Promotion Evidence Summary Foundation should add a compact deterministic evidence summary for a candidate, including assumptions, warnings, and source facts, without creating an automatic approval engine.
