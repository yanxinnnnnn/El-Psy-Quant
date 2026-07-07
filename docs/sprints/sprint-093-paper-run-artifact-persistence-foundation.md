# Sprint 93 — Paper Run Artifact Persistence Foundation

## Status

Complete.

## Goal

Add the smallest explicit local persistence boundary for paper run artifacts.

Sprint 93 builds the third Milestone 18 link:

```text
paper run request contract -> paper run execution boundary -> paper run artifact persistence
```

The persistence boundary is intentionally narrow. It persists an existing in-memory `PaperTradingArtifact` to a caller-supplied path by reusing the Milestone 17 paper artifact writer and file contract.

## Delivered

- Added `persist_paper_run_artifact(...)` under the existing `paper` package.
- Reused `write_paper_trading_artifact_file(...)` instead of duplicating file-writing behavior.
- Preserved the existing paper artifact file contract and deterministic JSON output.
- Required callers to supply the destination path explicitly.
- Returned the written `Path`.
- Exported the public helper from `el_psy_quant.paper`.
- Added focused tests for successful persistence, file-contract payload content, explicit path behavior, invalid inputs, missing parent directories, input non-mutation, exports, and guardrails.

## Important Behavior

`persist_paper_run_artifact(...)` does not create or execute a paper run.

The caller must provide an existing `PaperTradingArtifact` and an explicit local destination path. Parent directory handling, UTF-8 JSON formatting, and strict payload generation remain delegated to the existing Milestone 17 writer/file-contract boundary.

## Guardrails

Sprint 93 intentionally does not add:

- default output roots
- run directory conventions
- artifact reading
- audit summaries
- paper run result summaries
- request execution
- fill application
- CLI or configured-run wiring
- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- database behavior
- dashboard behavior
- report generation

## Next Step

Sprint 94 — Paper Run Result Summary Foundation.

Sprint 94 should add a compact result summary tying the request, artifact identity, saved path, and audit facts together. It should not add dashboards, reports, configured-run integration, broker/live behavior, databases, or broad workflow automation.
