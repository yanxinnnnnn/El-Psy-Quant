# Milestone 18 — Paper Trading Workflow Integration Foundation

## Status

In progress.

## Product Goal

Turn the paper-trading building blocks from Milestones 16 and 17 into one explicit, deterministic, local workflow boundary.

Milestone 18 should make a local paper run request executable and reviewable without introducing broker integration, live execution, database behavior, dashboards, or broad report generation.

## Strategic Context

Milestone 16 made paper trading explicit in memory:

```text
paper account state
  -> paper order ledger
  -> paper fill application
  -> paper trading session summary
  -> paper trading artifact
```

Milestone 17 made paper trading outputs durable and audit-friendly:

```text
paper artifact file contract
  -> local paper artifact writer
  -> local paper artifact reader and validation
  -> paper session audit summary
```

Milestone 18 should integrate these capabilities into one local workflow:

```text
paper run request
  -> paper run execution
  -> paper artifact persistence
  -> paper run result summary
```

## Planned Chain

```text
paper run request contract
  -> paper run execution boundary
  -> paper run artifact persistence
  -> paper run result summary
  -> paper workflow closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S90 | Complete | Plan Milestone 18. | Workflow integration scope, sequence, and long-term platform context. | No implementation during planning. |
| S91 | Complete | Define paper run request contract. | Small immutable request boundary for one local paper run. | No execution or file writing yet. |
| S92 | Complete | Add paper run execution boundary. | Build a paper trading artifact from an explicit request. | No CLI, broker, or configured-run integration. |
| S93 | Complete | Add paper run artifact persistence. | Persist a paper run artifact to an explicit local path using the M17 writer. | No default output-root workflow. |
| S94 | Planned | Add paper run result summary. | Compact summary tying request, artifact identity, saved path, and audit facts. | No dashboard or report generation. |
| S95 | Planned | Close milestone. | Milestone 18 documentation refresh. | No scope expansion. |

## Expected Capabilities

By the end of Milestone 18, the project should support a conservative local paper workflow path:

1. define a paper run request contract
2. create a paper trading artifact from an explicit request
3. persist that artifact to an explicit local path
4. return a compact paper run result summary
5. document workflow assumptions, limits, and future integration boundaries

## Public Boundary Direction

Milestone 18 should likely introduce boundaries such as:

- `PaperRunRequest`
- `create_paper_run_request(...)`
- `run_paper_trading_request(...)`
- `persist_paper_run_artifact(...)`
- `PaperRunResultSummary`
- `create_paper_run_result_summary(...)`

The exact names can change during implementation sprints, but the scope should stay small and local.

## Assumptions And Limits

- workflow behavior is local and deterministic
- all inputs should be explicit
- file persistence should use explicit paths only
- existing M16 and M17 boundaries should be reused instead of duplicated
- configured-run integration remains outside this milestone
- CLI expansion remains outside this milestone
- broker integration remains outside this milestone
- live execution remains outside this milestone
- database, dashboard, and broad report generation remain outside this milestone
- strategy expansion remains outside this milestone
- portfolio optimizer behavior remains outside this milestone

## Exit Criteria

Milestone 18 will be complete when:

- a paper run request contract exists
- a local paper run can produce a paper trading artifact from explicit inputs
- a paper run artifact can be persisted through the existing M17 writer path
- a compact run-level result summary exists
- documentation explains assumptions, limits, and future workflow boundaries
- no broker, live trading, database, dashboard, report, configured-run, or CLI workflow behavior has been introduced

## Current Next Step

```text
Sprint 94 — Paper Run Result Summary Foundation
```

Sprint 94 should add a compact result summary tying the request, artifact identity, saved path, and audit facts together. It should not add dashboards, reports, configured-run integration, databases, or broker/live behavior.
