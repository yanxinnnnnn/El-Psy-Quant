# Sprint 104 — Promotion Source Reference Contract Foundation

## Status

Complete.

## Goal

Add the smallest typed contract for referencing existing local or logical evidence that may later support research-to-paper promotion.

Sprint 104 starts Milestone 20 implementation with reference plumbing only. It does not load artifacts, score evidence, create promotion candidates, create promotion records, execute paper workflows, or approve anything automatically.

## Delivered

- Added the `el_psy_quant.promotion` package.
- Added `PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION`.
- Added explicit `SUPPORTED_PROMOTION_SOURCE_TYPES`.
- Added immutable `PromotionSourceReference`.
- Added `create_promotion_source_reference(...)`.
- Added deterministic, JSON-compatible `to_dict()` output.
- Added tests for valid creation, source type validation, required reference validation, optional field normalization, deterministic export, schema version, immutability, and public package exports.

## Supported Source Types

Sprint 104 supports these explicit source types:

```text
research_run
backtest_artifact
execution_artifact
portfolio_artifact
configured_run
paper_artifact
paper_result_summary
```

The contract does not infer source type from a path and does not inspect the referenced artifact.

## Export Shape

```json
{
  "schema_version": 1,
  "source_type": "configured_run",
  "reference": "outputs/ma/run-1",
  "run_id": "run-1",
  "artifact_id": "manifest",
  "label": "Candidate source",
  "description": "Configured run selected for manual review."
}
```

Optional blank strings normalize to `null`. Required fields remain strict.

## Boundary

This sprint does not add:

- paper promotion candidates
- promotion evidence summaries
- explicit promotion records
- promotion manifest/reference wiring
- artifact loading, parsing, or scoring
- strategy approval logic
- automatic research-to-paper promotion
- automatic strategy-signal-to-order conversion
- paper order, fill, or `PaperRunRequest` construction from research outputs
- paper workflow execution from source references
- broker, live, scheduler, database, dashboard, or broad reporting behavior
- strategy expansion
- CLI changes

## Next Step

Sprint 105 — Paper Promotion Candidate Contract Foundation should define an explicit candidate boundary linked to source references and manual review context without constructing `PaperRunRequest` objects or executing paper workflows.
