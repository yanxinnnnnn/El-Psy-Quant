# Sprint 108 — Promotion Manifest and Candidate References Foundation

## Status

Complete.

## Goal

Add the smallest typed local reference contracts for inspecting promotion records and their paper promotion candidates together.

Sprint 108 builds on Sprint 107 explicit promotion records. It adds compact candidate references and a promotion manifest, but it does not load artifacts, write files, create reports, score evidence, approve strategies, or execute paper workflows.

## Delivered

- Added `PROMOTION_CANDIDATE_REFERENCE_SCHEMA_VERSION`.
- Added `PROMOTION_MANIFEST_SCHEMA_VERSION`.
- Added immutable `PromotionCandidateReference`.
- Added immutable `PromotionManifest`.
- Added `create_promotion_candidate_reference(...)`.
- Added `create_promotion_manifest(...)`.
- Reused explicit promotion record statuses for candidate references.
- Required non-empty promotion record and candidate reference sequences for manifests.
- Added deterministic, JSON-compatible `to_dict()` output for both contracts.
- Exported the manifest public API through `el_psy_quant.promotion`.
- Added focused tests for valid creation, validation failures, raw string sequence rejection, invalid item validation, timestamp export, deterministic export, immutability, input-copy behavior, and package exports.

## Candidate Reference Shape

```json
{
  "schema_version": 1,
  "record_id": "record-1",
  "candidate_id": "candidate-1",
  "status": "approved_for_paper",
  "reference": "promotion/record-1.json",
  "label": "Paper candidate",
  "description": "Local logical reference only."
}
```

The `status` value is copied from the explicit promotion record status vocabulary. It is not inferred.

## Manifest Shape

```json
{
  "schema_version": 1,
  "manifest_id": "manifest-1",
  "promotion_records": [
    {
      "schema_version": 1,
      "record_id": "record-1",
      "evidence_summary": {},
      "status": "approved_for_paper",
      "rationale": "Approved for paper-trading review only.",
      "reviewer": "reviewer-1",
      "created_timestamp": "2026-01-02T03:04:05"
    }
  ],
  "candidate_references": [
    {
      "schema_version": 1,
      "record_id": "record-1",
      "candidate_id": "candidate-1",
      "status": "approved_for_paper",
      "reference": "promotion/record-1.json",
      "label": "Paper candidate",
      "description": "Local logical reference only."
    }
  ],
  "created_timestamp": "2026-01-02T03:04:05",
  "description": "Local inspection manifest."
}
```

The manifest groups in-memory `PromotionRecord` objects and compact `PromotionCandidateReference` objects. It does not write itself to disk or read anything from disk.

## Boundary

This sprint does not add:

- filesystem artifact loading or parsing
- filesystem writing or persistence behavior
- database behavior
- dashboard behavior
- broad report generation
- automatic metric extraction
- artifact scoring
- autonomous strategy approval
- automatic research-to-paper promotion
- automatic status inference
- live-readiness claims
- real-money readiness claims
- automatic strategy-signal-to-order conversion
- construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from manifests or records
- broker, live, scheduler, or strategy expansion behavior
- CLI changes

## Next Step

Sprint 109 — Milestone 20 Documentation Refresh should close out the research-to-paper promotion foundation documentation without expanding runtime behavior.
