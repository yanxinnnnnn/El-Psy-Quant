# Sprint 121 — Explicit Strategy Decision Record Foundation

## Status

Complete.

## Goal

Add the smallest useful human-controlled strategy decision record contract under the existing decision-governance package.

Sprint 121 records an explicit reviewer status and rationale for a caller-supplied `StrategyDecisionSummary`. It is a local immutable contract only, not an automated approval system.

## Delivered

- Added `StrategyDecisionRecord`.
- Added `STRATEGY_DECISION_RECORD_SCHEMA_VERSION`.
- Added `SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES`.
- Added `create_strategy_decision_record(...)`.
- Exported the public API from `el_psy_quant.decision_governance`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - non-empty `decision_id`
  - `StrategyDecisionSummary` decision summary
  - supported explicit decision statuses
  - non-empty reviewer rationale
  - optional reviewer metadata
  - optional timestamp normalization through `pandas.Timestamp`
  - optional notes and warnings sequences
- Added tests for valid creation, supported statuses, normalization, invalid inputs, immutability, JSON compatibility, package exports, and guardrails.

## Supported Statuses

Sprint 121 supports only these explicit human-controlled statuses:

```text
needs_more_evidence
approved_for_continued_paper_review
rejected_for_now
put_on_hold
```

These statuses describe local governance state only. They do not approve live trading, real-money deployment, broker behavior, or capital allocation.

## Record Shape

The record payload includes:

```text
schema_version
decision_id
decision_summary
decision_status
rationale
reviewed_by
reviewed_timestamp
notes
warnings
```

The nested `decision_summary` is exported through `StrategyDecisionSummary.to_dict()`.

## Scope Guardrails

Sprint 121 does not add:

- decision manifests
- decision references
- automatic approval or rejection
- automatic promotion
- strategy lifecycle automation
- recommendation engines
- rationale evaluation
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
Sprint 122 — Decision Manifest and References Foundation
```

Sprint 122 should add local decision manifest and reference contracts for strategy decision summaries and records without file I/O, database behavior, reports, workflow execution, broker behavior, or readiness claims.
