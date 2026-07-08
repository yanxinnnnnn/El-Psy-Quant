# Milestone 20 — Research-to-Paper Promotion Foundation

## Status

Complete.

## Product Goal

Define a conservative, human-controlled promotion boundary between research evidence and paper-trading candidates.

Milestone 20 makes it possible to record why a research, backtest, execution, portfolio, configured-run, or paper output is being considered for paper trading without automatically approving the strategy, constructing paper orders, executing a paper workflow, or making live-readiness claims.

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

Milestone 18 made one explicit local paper run executable, persistable, and summarizable:

```text
paper run request
  -> paper run execution
  -> paper artifact persistence
  -> paper run result summary
```

Milestone 19 connected that explicit workflow to local configuration and run-output discipline:

```text
local config
  -> validated paper run request
  -> configured output layout
  -> paper workflow execution
  -> saved paper outputs and result references
```

Milestone 20 adds the missing review boundary before a research result becomes a paper-trading candidate:

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit promotion record
  -> reviewable promotion references
```

This is decision governance, not autonomous trading.

## Delivered Chain

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
  -> research-to-paper promotion closeout
```

## Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S103 | Complete | Plan Milestone 20. | Research-to-paper promotion scope, sequence, and guardrails. | No implementation during planning. |
| S104 | Complete | Define promotion source references. | Small typed references to research, backtest, execution, portfolio, configured-run, paper artifact, or paper-result evidence. | No artifact loading, scoring, or promotion decision yet. |
| S105 | Complete | Define paper promotion candidate contract. | Explicit paper-trading candidate boundary linked to source references and manual review context. | No `PaperRunRequest` construction or paper workflow execution. |
| S106 | Complete | Add promotion evidence summary. | Compact deterministic evidence summary for a candidate, including assumptions, warnings, missing evidence, and source facts. | No automatic pass/fail approval engine. |
| S107 | Complete | Add explicit promotion record. | Human-controlled promotion record tying candidate, evidence, rationale, reviewer context, status, and timestamp together. | No autonomous strategy approval or live-readiness claim. |
| S108 | Complete | Add promotion manifest and candidate references. | Local manifest/reference contracts for promotion records and paper candidates. | No filesystem I/O, database, dashboard, or broad report generation. |
| S109 | Complete | Close milestone. | Milestone 20 documentation refresh. | No scope expansion. |

## Delivered Capabilities

Milestone 20 introduced small typed local boundaries for:

- `PromotionSourceReference`
- `PaperPromotionCandidate`
- `PromotionEvidenceSummary`
- `PromotionRecord`
- `PromotionCandidateReference`
- `PromotionManifest`

These contracts make the research-to-paper path explicit and reviewable while keeping it local, deterministic, and human-controlled.

## Promotion Boundary Semantics

A promotion source reference is only a pointer to existing evidence. It does not load, parse, score, or validate the referenced artifact.

A paper promotion candidate is only a proposed paper-review candidate. It is not approval, order construction, or workflow execution.

A promotion evidence summary is descriptive context. Source facts, assumptions, warnings, and missing-evidence fields are caller-supplied and do not form an automatic scoring engine.

A promotion record is a human-controlled record of status and rationale. The `approved_for_paper` status means approved for paper-trading review only; it is not live readiness, real-money readiness, broker approval, or autonomous strategy approval.

A promotion manifest is an in-memory/local reference contract for inspection. It does not read from disk, write to disk, create reports, persist data, or run workflows.

## Assumptions And Limits

- promotion remains manual or explicitly requested
- a candidate is not an approval
- a promotion record is not a live-readiness record
- evidence summaries are descriptive, not autonomous scoring engines
- source artifacts remain immutable inputs
- promotion records reference evidence instead of duplicating large artifacts
- paper workflow execution remains separate from promotion records
- configured paper workflow behavior remains unchanged
- local typed contracts are enough for this milestone

## Explicitly Out Of Scope

Milestone 20 did not introduce:

- automatic research-to-paper promotion
- automatic strategy approval
- automatic strategy-signal-to-order conversion
- automatic construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from promotion records or manifests
- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- scheduler behavior
- real account synchronization
- paper run comparison dashboards
- broad report generation
- database behavior
- hosted services or SaaS behavior
- strategy expansion
- live-readiness claims
- real-money readiness claims

## Exit Criteria

Milestone 20 is complete because:

- promotion source references are explicit and typed
- paper promotion candidates can be represented without executing paper workflows
- promotion evidence can be summarized deterministically with source facts, assumptions, warnings, and missing-evidence fields
- explicit promotion records capture candidate evidence, rationale, status, reviewer context, and timestamp
- promotion manifests and candidate references can be inspected locally
- documentation explains promotion assumptions, limits, and future decision boundaries
- automatic promotion, broker behavior, live behavior, broad reporting, dashboard behavior, database behavior, and strategy expansion remain outside the milestone

## Next Step

```text
Sprint 110 — Milestone 21 Planning
```

Milestone 21 should plan the next conservative layer after promotion governance. The expected direction is Paper Run Comparison and Review Foundation: compare multiple paper runs and define review decision records without dashboards, broad reporting, broker readiness, or live-readiness claims.
