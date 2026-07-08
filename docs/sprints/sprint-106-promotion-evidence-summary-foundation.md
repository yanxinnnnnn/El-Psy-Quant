# Sprint 106 — Promotion Evidence Summary Foundation

## Status

Complete.

## Goal

Add the smallest typed contract for attaching descriptive evidence context to a paper promotion candidate.

Sprint 106 builds on Sprint 105 paper promotion candidates. It summarizes explicitly supplied facts, assumptions, warnings, and missing evidence for manual review, but it does not load artifacts, extract metrics, score evidence, approve candidates, create promotion records, or execute paper workflows.

## Delivered

- Added `PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION`.
- Added immutable `PromotionEvidenceSummary`.
- Added `create_promotion_evidence_summary(...)`.
- Required an explicit `PaperPromotionCandidate`.
- Required one or more explicit `source_facts`.
- Added optional normalized `assumptions`, `warnings`, and `missing_evidence` fields.
- Added optional deterministic `created_timestamp` export.
- Added deterministic, JSON-compatible `to_dict()` output with nested candidate export.
- Exported the evidence summary public API through `el_psy_quant.promotion`.
- Added focused tests for valid creation, candidate validation, sequence validation, item validation, timestamp export, deterministic export, immutability, input-copy behavior, and package exports.

## Evidence Summary Shape

```json
{
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
        "reference": "outputs/ma/run-1",
        "run_id": "run-1",
        "artifact_id": "manifest",
        "label": "Configured run",
        "description": null
      }
    ]
  },
  "source_facts": [
    "Summary row exists",
    "Paper artifact is present"
  ],
  "assumptions": [
    "Costs are already represented in source results"
  ],
  "warnings": [
    "Manual review still required"
  ],
  "missing_evidence": [
    "No live-readiness review"
  ],
  "created_timestamp": "2026-01-02T03:04:05"
}
```

Source facts and optional evidence fields are caller-supplied text. Sprint 106 does not inspect referenced artifacts or infer any facts automatically.

## Boundary

This sprint does not add:

- explicit promotion records
- promotion manifest/reference wiring
- artifact loading or parsing
- automatic metric extraction
- artifact scoring
- strategy approval logic
- pass/fail approval engines
- automatic research-to-paper promotion
- automatic strategy-signal-to-order conversion
- construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from candidates or summaries
- broker, live, scheduler, database, dashboard, or broad reporting behavior
- strategy expansion
- CLI changes

## Next Step

Sprint 107 — Explicit Promotion Record Foundation should add a human-controlled promotion record tying candidate, evidence, rationale, status, reviewer or actor context, and source references together without claiming live readiness.
