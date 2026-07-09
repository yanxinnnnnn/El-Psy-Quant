# Sprint 120 — Strategy Decision Summary Foundation

## Status

Complete.

## Goal

Add the smallest useful strategy decision summary contract under the existing decision-governance package.

Sprint 120 records caller-supplied facts, assumptions, warnings, and missing-evidence notes for a strategy-level decision input. It is descriptive context only.

## Delivered

- Added `StrategyDecisionSummary`.
- Added `STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION`.
- Added `create_strategy_decision_summary(...)`.
- Exported the public API from `el_psy_quant.decision_governance`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty `summary_id`
  - `StrategyDecisionInput` decision input
  - non-empty caller-supplied decision facts
  - optional assumptions, warnings, and missing-evidence sequences
  - optional reviewer metadata
  - optional timestamp normalization through `pandas.Timestamp`
- Added tests for valid creation, normalization, invalid inputs, immutability, JSON compatibility, package exports, and guardrails.

## Summary Shape

The summary payload includes:

```text
schema_version
summary_id
decision_input
decision_facts
assumptions
warnings
missing_evidence
created_by
created_timestamp
```

The nested `decision_input` is exported through `StrategyDecisionInput.to_dict()`.

## Scope Guardrails

Sprint 120 does not add:

- strategy decision records
- decision manifests
- decision status enums
- recommendation engines
- approval or rejection logic
- scoring, ranking, or winner selection
- artifact loading or parsing
- automatic evidence discovery
- workflow execution
- file I/O or database behavior
- dashboards, reports, or plotting
- broker, live, or capital deployment behavior
- live-readiness or real-money-readiness claims

## Next Step

```text
Sprint 121 — Explicit Strategy Decision Record Foundation
```

Sprint 121 should add human-controlled strategy decision records tied to strategy decision summaries without automatic approval, promotion, capital allocation, broker behavior, or readiness claims.
