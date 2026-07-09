# Sprint 122 — Decision Manifest and References Foundation

## Status

Complete.

## Goal

Add local strategy decision reference and manifest contracts under the existing decision-governance package.

Sprint 122 groups existing strategy decision summaries and records through explicit local references. It is an in-memory contract layer only, not persistence, file I/O, reporting, approval, or workflow execution.

## Delivered

- Added `StrategyDecisionReference`.
- Added `StrategyDecisionManifest`.
- Added `STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION`.
- Added `STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION`.
- Added `SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES`.
- Added `create_strategy_decision_reference(...)`.
- Added `create_strategy_decision_manifest(...)`.
- Added `create_strategy_decision_reference_from_summary(...)`.
- Added `create_strategy_decision_reference_from_record(...)`.
- Exported the public API from `el_psy_quant.decision_governance`.
- Added deterministic JSON-compatible `to_dict()` output.
- Added validation for:
  - supported decision reference types
  - non-empty reference IDs
  - non-empty manifest IDs
  - at least one summary or record reference
  - summary references in the summary bucket only
  - record references in the record bucket only
  - immutable reference sequences
  - optional manifest metadata
  - optional timestamp normalization through `pandas.Timestamp`
- Added tests for valid references, valid manifests, helper constructors, invalid buckets, invalid sequences, immutability, JSON compatibility, package exports, and guardrails.

## Supported Reference Types

Sprint 122 supports only:

```text
strategy_decision_summary
strategy_decision_record
```

References are local identifiers only. They do not load, read, validate, or parse external artifacts.

## Manifest Shape

The manifest payload includes:

```text
schema_version
manifest_id
summary_references
record_references
created_by
created_timestamp
description
```

Nested references are exported through `StrategyDecisionReference.to_dict()`.

## Scope Guardrails

Sprint 122 does not add:

- file writing or reading
- database behavior
- persistence services
- artifact loading or parsing
- reports, dashboards, or plotting
- workflow execution
- automatic approval or rejection
- automatic promotion
- scoring, ranking, or recommendations
- broker, live, or capital deployment behavior
- live-readiness or real-money-readiness claims

## Next Step

```text
Sprint 123 — Milestone 22 Documentation Refresh
```

Sprint 123 should close Milestone 22 with documentation updates only and preserve the decision-governance guardrails.
