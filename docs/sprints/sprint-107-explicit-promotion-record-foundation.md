# Sprint 107 — Explicit Promotion Record Foundation

## Status

Complete.

## Goal

Add the smallest typed contract for recording a human-controlled research-to-paper promotion decision boundary.

Sprint 107 builds on Sprint 106 promotion evidence summaries. It records explicit reviewer rationale and status, but it does not infer status, approve live readiness, claim real-money readiness, create manifests, load artifacts, score evidence, or execute paper workflows.

## Delivered

- Added `PROMOTION_RECORD_SCHEMA_VERSION`.
- Added explicit `PROMOTION_RECORD_STATUSES`.
- Added immutable `PromotionRecord`.
- Added `create_promotion_record(...)`.
- Required an explicit `PromotionEvidenceSummary`.
- Required explicit `record_id`, `status`, and `rationale`.
- Added optional normalized `reviewer`.
- Added optional deterministic `created_timestamp` export.
- Added deterministic, JSON-compatible `to_dict()` output with nested evidence summary export.
- Exported the promotion record public API through `el_psy_quant.promotion`.
- Added focused tests for every allowed status, validation failures, reviewer normalization, timestamp export, deterministic export, immutability, and package exports.

## Allowed Statuses

```text
proposed
approved_for_paper
rejected
deferred
```

The `approved_for_paper` status means explicit human approval to consider or proceed with paper-trading review only. It is not a live-readiness claim, real-money readiness claim, broker approval, or automated strategy approval.

## Record Shape

```json
{
  "schema_version": 1,
  "record_id": "record-1",
  "evidence_summary": {
    "schema_version": 1,
    "candidate": {
      "schema_version": 1,
      "candidate_id": "candidate-1",
      "title": "Review moving-average candidate",
      "rationale": null,
      "proposed_by": null,
      "created_timestamp": null,
      "source_references": [
        {
          "schema_version": 1,
          "source_type": "configured_run",
          "reference": "outputs/run-1",
          "run_id": "run-1",
          "artifact_id": "manifest",
          "label": "Configured run",
          "description": null
        }
      ]
    },
    "source_facts": [
      "Summary row exists"
    ],
    "assumptions": [
      "Manual review is required"
    ],
    "warnings": [
      "Not a live-readiness claim"
    ],
    "missing_evidence": [],
    "created_timestamp": null
  },
  "status": "approved_for_paper",
  "rationale": "Approved for paper-trading review only.",
  "reviewer": "reviewer-1",
  "created_timestamp": "2026-01-02T03:04:05"
}
```

## Boundary

This sprint does not add:

- promotion manifest/reference wiring
- artifact loading or parsing
- automatic metric extraction
- artifact scoring
- autonomous strategy approval
- automatic research-to-paper promotion
- automatic status inference
- live-readiness claims
- real-money readiness claims
- automatic strategy-signal-to-order conversion
- construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from records
- broker, live, scheduler, database, dashboard, or broad reporting behavior
- strategy expansion
- CLI changes

## Next Step

Sprint 108 — Promotion Manifest and Candidate References Foundation should add local artifact/reference wiring for promotion records and paper candidates without introducing databases, dashboards, broad reporting, artifact scoring, or runtime execution.
