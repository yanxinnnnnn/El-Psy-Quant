# Milestone 20 — Research-to-Paper Promotion Foundation

## Status

In progress.

## Product Goal

Define a conservative, human-controlled promotion boundary between research evidence and paper-trading candidates.

Milestone 20 should make it possible to record why a research, backtest, execution, portfolio, or configured-run output is being considered for paper trading without automatically approving the strategy, constructing paper orders, executing a paper workflow, or making live-readiness claims.

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

Milestone 20 should add the missing review boundary before a research result becomes a paper-trading candidate:

```text
research evidence
  -> promotion candidate
  -> explicit promotion record
  -> reviewable references
```

This is the first step toward decision governance, not the start of autonomous trading.

## Planned Chain

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
| S104 | Complete | Define promotion source references. | Small typed references to research, backtest, execution, portfolio, or configured-run artifacts used as promotion evidence. | No artifact loading, scoring, or promotion decision yet. |
| S105 | Planned | Define paper promotion candidate contract. | Explicit paper-trading candidate boundary linked to source references and manual review context. | No `PaperRunRequest` construction or paper workflow execution. |
| S106 | Planned | Add promotion evidence summary. | Compact deterministic evidence summary for a candidate, including assumptions, warnings, and source facts. | No automatic pass/fail approval engine. |
| S107 | Planned | Add explicit promotion record. | Human-controlled promotion record tying candidate, evidence, rationale, and status together. | No autonomous strategy approval or live-readiness claim. |
| S108 | Planned | Add promotion manifest and candidate references. | Local artifact/reference wiring for promotion records and paper candidates. | No database, dashboard, or broad report generation. |
| S109 | Planned | Close milestone. | Milestone 20 documentation refresh. | No scope expansion. |

## Planned Capabilities

Milestone 20 may introduce small typed local boundaries for:

- promotion source references
- paper promotion candidates
- promotion evidence summaries
- explicit promotion records
- promotion artifact or manifest references

The milestone should keep the promotion path local, deterministic, and review-driven.

## Included Capabilities

Milestone 20 may include:

1. reference contracts for local research, backtest, execution, portfolio, configured-run, or paper artifacts
2. a typed paper promotion candidate that links source evidence to proposed paper review intent
3. evidence summary fields for assumptions, warnings, missing evidence, and source facts
4. an explicit promotion record with rationale, status, reviewer or actor context, and source references
5. deterministic local references for promotion records and candidate artifacts
6. documentation of what promotion means and what it does not mean

## Assumptions And Limits

- promotion remains manual or explicitly requested
- a candidate is not an approval
- a promotion record is not a live-readiness record
- evidence summaries are descriptive, not autonomous scoring engines
- source artifacts should remain immutable inputs
- promotion records should reference evidence instead of duplicating large artifacts
- paper workflow execution remains separate from promotion records
- configured paper workflow behavior remains unchanged unless a later sprint explicitly scopes a narrow reference-only integration
- local filesystem artifacts remain sufficient

## Explicitly Out Of Scope

Milestone 20 must not introduce:

- automatic research-to-paper promotion
- automatic strategy approval
- automatic strategy-signal-to-order conversion
- automatic construction of paper orders, fills, or `PaperRunRequest` from research outputs
- configured paper workflow execution from promotion records
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

Milestone 20 will be complete when:

- promotion source references are explicit and typed
- paper promotion candidates can be represented without executing paper workflows
- promotion evidence can be summarized deterministically with assumptions and warnings
- explicit promotion records can capture candidate, evidence, rationale, status, and references
- promotion artifacts or references can be inspected locally
- documentation explains promotion assumptions, limits, and future decision boundaries
- automatic promotion, broker behavior, live behavior, broad reporting, dashboard behavior, and strategy expansion remain outside the milestone

## Current Next Step

```text
Sprint 105 — Paper Promotion Candidate Contract Foundation
```

Sprint 105 should define an explicit paper promotion candidate boundary linked to source references and manual review context without constructing `PaperRunRequest` objects or executing paper workflows.
