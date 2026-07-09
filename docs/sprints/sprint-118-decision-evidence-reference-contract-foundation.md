# Sprint 118 — Decision Evidence Reference Contract Foundation

## Status

Complete.

## Goal

Add the smallest useful typed reference contract for existing promotion and paper-review evidence.

This sprint starts Milestone 22 by creating a decision-governance package that can point to completed evidence layers without loading, parsing, scoring, ranking, or deciding anything.

## Delivered

- Added `el_psy_quant.decision_governance`.
- Added `DecisionEvidenceReference`.
- Added `DECISION_EVIDENCE_REFERENCE_SCHEMA_VERSION`.
- Added `SUPPORTED_DECISION_EVIDENCE_REFERENCE_TYPES`.
- Added `create_decision_evidence_reference(...)`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added tests for validation, normalization, immutability, deterministic export, package imports, and scope guardrails.

## Supported Reference Types

```text
promotion_record
promotion_candidate_reference
promotion_manifest
paper_comparison_summary
paper_review_decision
paper_review_manifest
```

These reference types cover existing completed promotion and paper-review evidence layers only.

## Reference Shape

The reference export includes:

```text
schema_version
reference_type
reference_id
label
description
```

Required strings are trimmed and must not be empty. Optional strings are trimmed and blank optional strings normalize to `None`.

## Scope Guardrails

Sprint 118 does not add:

- strategy decision inputs
- strategy decision summaries
- strategy decision records
- decision manifests
- artifact loading or parsing
- metric calculation
- scoring or ranking
- automatic evidence discovery
- automatic decision making
- workflow execution
- file I/O or database behavior
- dashboards, reports, or plotting
- broker or live behavior
- capital deployment
- readiness claims

Decision evidence references are pointers only. They are not evidence discovery, evidence quality validation, scoring, recommendations, approvals, or readiness claims.

## Next Step

```text
Sprint 119 — Strategy Decision Input Contract Foundation
```

Sprint 119 should define an explicit strategy decision input contract that groups decision evidence references without automatic evidence discovery, scoring, decision making, workflow execution, broker behavior, or readiness claims.
