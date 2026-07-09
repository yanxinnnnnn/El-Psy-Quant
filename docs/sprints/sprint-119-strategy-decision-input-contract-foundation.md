# Sprint 119 — Strategy Decision Input Contract Foundation

## Status

Complete.

## Goal

Add the smallest explicit strategy decision input contract that groups caller-supplied decision evidence references for future strategy-level review.

This sprint builds on Sprint 118 `DecisionEvidenceReference` and remains input-only.

## Delivered

- Added `StrategyDecisionInput`.
- Added `STRATEGY_DECISION_INPUT_SCHEMA_VERSION`.
- Added `create_strategy_decision_input(...)`.
- Exported the input contract from `el_psy_quant.decision_governance`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty input IDs
  - non-empty decision purpose
  - non-empty evidence reference sequences
  - `DecisionEvidenceReference` item types
  - optional strategy ID, review context, and creator provenance
  - optional timestamp normalization
- Added tests for validation, normalization, timestamp export, immutability, deterministic export, package imports, and scope guardrails.

## Input Shape

The strategy decision input export includes:

```text
schema_version
input_id
evidence_references
decision_purpose
strategy_id
review_context
created_by
created_timestamp
```

Nested evidence references are exported through their existing `to_dict()` boundary.

## Scope Guardrails

Sprint 119 does not add:

- strategy decision summaries
- strategy decision records
- decision manifests
- decision status enums
- recommendation engines
- approval or rejection logic
- scoring or ranking
- artifact loading or parsing
- automatic evidence discovery
- workflow execution
- file I/O or database behavior
- dashboards, reports, or plotting
- broker or live behavior
- capital deployment
- readiness claims

The input is an explicit grouping of evidence references only. It is not a decision, recommendation, approval, promotion, report, workflow trigger, or readiness claim.

## Next Step

```text
Sprint 120 — Strategy Decision Summary Foundation
```

Sprint 120 should add caller-supplied strategy decision summaries without recommendation engines, metric calculation, scoring, dashboards, reports, workflow execution, broker behavior, or readiness claims.
