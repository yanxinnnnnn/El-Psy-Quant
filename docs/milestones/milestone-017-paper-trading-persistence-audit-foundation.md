# Milestone 17 — Paper Trading Persistence & Audit Foundation

## Status

Planned.

## Product Goal

Make local paper-trading outputs durable, reloadable, and audit-friendly before adding broker integration, runtime workflows, configured-run expansion, dashboards, or live execution behavior.

## Planned Chain

Milestone 17 will use this conservative chain:

```text
paper artifact file contract
  -> local paper artifact writer
  -> local paper artifact reader and validation
  -> paper session audit summary
  -> paper trading persistence closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S84 | Complete | Plan Milestone 17. | Paper trading persistence and audit scope and sprint sequence. | No implementation during planning. |
| S85 | Planned | Define paper artifact file contract. | Deterministic local file contract for saved paper trading artifacts. | No writer side effects yet. |
| S86 | Planned | Add local paper artifact writer. | Save a paper trading artifact to an explicit local path. | No CLI or configured-run integration. |
| S87 | Planned | Add paper artifact reader and validation. | Load saved paper artifacts and validate schema/version expectations. | No database or artifact service. |
| S88 | Planned | Add paper session audit summary. | Compact deterministic audit summary from saved paper artifacts. | No dashboard or report generation. |
| S89 | Planned | Close milestone. | Milestone 17 documentation refresh. | No scope expansion. |

## Why This Comes After Milestone 16

Milestone 16 made the paper-trading lifecycle explicit in memory:

```text
paper account state
  -> paper order ledger
  -> paper fill application
  -> paper trading session summary
  -> paper trading artifact
```

That foundation is useful, but not durable yet.

Before the project adds workflow automation, configured runs, broker readiness, dashboards, or live execution, paper-trading sessions should leave behind local artifacts that can be saved, loaded, checked, and summarized.

This keeps the platform honest. If a paper session cannot be inspected later, it should not become part of a broader runtime workflow.

## Expected Capabilities

By the end of Milestone 17, the project should support a conservative local persistence path for paper-trading outputs:

1. define the file-level contract for a saved paper-trading artifact
2. write an existing paper-trading artifact to an explicit local file path
3. read a saved paper-trading artifact back from disk
4. validate schema/version expectations during load
5. produce a compact audit summary from saved paper-trading artifact content
6. document assumptions, limits, and what remains out of scope

## Assumptions And Limits

- persistence is local filesystem persistence only
- saved content should remain deterministic and JSON-compatible
- read/write behavior should require explicit file paths
- schema/version expectations should be visible and testable
- audit summaries should be compact and review-oriented
- configured-run integration remains outside this milestone
- CLI expansion remains outside this milestone
- broker integration remains outside this milestone
- live execution remains outside this milestone
- database, dashboard, and report generation remain outside this milestone

## Exit Criteria

Milestone 17 will be complete when:

- a paper-trading artifact file contract is defined
- paper-trading artifacts can be saved to explicit local paths
- saved paper-trading artifacts can be loaded and validated
- saved sessions can produce a compact audit summary
- documentation explains assumptions, limits, and future workflow boundaries
- no broker, live trading, database, dashboard, or configured-run behavior has been introduced

## Current Next Step

```text
Sprint 85 — Paper Artifact File Contract Foundation
```

The next sprint should define the smallest useful file contract before adding local writer behavior.
