# Sprint 91 — Paper Run Request Contract Foundation

## Status

Complete.

## Goal

Define the smallest useful immutable request contract for one local paper run.

Sprint 91 starts Milestone 18 implementation by introducing an explicit request boundary that later workflow execution can consume. The request records only caller-supplied local inputs. It does not execute a workflow, create an artifact, write files, or connect to any runtime integration.

## Delivered

- Added `PaperRunRequest` under the existing `paper` package.
- Added `create_paper_run_request(...)` as the small public factory.
- Added `PAPER_RUN_REQUEST_SCHEMA_VERSION` as the request schema/version boundary.
- Validated explicit run inputs:
  - non-empty `run_id`
  - valid `created_timestamp`
  - explicit starting and ending `PaperAccountState`
  - explicit `PaperOrderLedger` or sequence of `PaperOrderRecord`
  - explicit sequence of `PaperFill`
- Exported deterministic JSON-compatible request data with `to_dict()`, including `schema_version`.
- Reused existing paper account, order, ledger, and fill boundaries instead of duplicating paper-trading behavior.
- Added focused tests for validation, immutability, JSON compatibility, input non-mutation, exports, and guardrails.

## Request Shape

The request contains:

- `schema_version`
- `run_id`
- `created_timestamp`
- `starting_account_state`
- `ending_account_state`
- `orders`
- `fills`

These fields are explicit inputs only. The request does not apply fills, infer order status, calculate session summaries, create `PaperTradingArtifact`, or persist anything.

## Guardrails

Sprint 91 intentionally does not add:

- paper workflow execution
- artifact creation from the request
- file writing or reading
- output directory conventions
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

Sprint 92 — Paper Run Execution Boundary Foundation.

Sprint 92 should consume the explicit `PaperRunRequest` and build the in-memory paper trading artifact path without adding CLI, broker, configured-run, database, dashboard, or live execution behavior.
