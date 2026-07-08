# Milestone 21 — Paper Run Comparison and Review Foundation

## Status

In progress.

## Product Goal

Define a conservative, human-controlled comparison and review layer for multiple paper run outputs.

Milestone 21 should make paper runs comparable and reviewable without introducing dashboards, broad reporting, broker readiness, live-readiness claims, automatic capital deployment decisions, or runtime execution expansion.

## Strategic Context

Milestone 18 made one explicit local paper run executable, persistable, and summarizable:

```text
paper run request
  -> paper run execution
  -> paper artifact persistence
  -> paper run result summary
```

Milestone 19 connected paper runs to configured local workflow discipline:

```text
local config
  -> validated paper run request
  -> configured output layout
  -> paper workflow execution
  -> saved paper outputs and result references
```

Milestone 20 added the missing promotion-governance boundary:

```text
research evidence
  -> promotion candidate
  -> evidence summary
  -> explicit promotion record
  -> reviewable promotion references
```

Milestone 21 adds the next review boundary after paper outputs exist:

```text
multiple paper runs
  -> explicit comparison set
  -> comparison summary
  -> review decision record
  -> reviewable comparison references
```

This is decision review, not autonomous trading.

## Planned Chain

```text
paper run reference contract
  -> paper run comparison input contract
  -> paper run comparison summary
  -> paper run review decision record
  -> review manifest and comparison references
  -> paper run comparison and review closeout
```

## Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S110 | Complete | Plan Milestone 21. | Paper run comparison and review scope, sequence, and guardrails. | No implementation during planning. |
| S111 | Complete | Define paper run references. | Small typed references to existing paper run artifacts or result summaries. | No artifact loading or automatic discovery. |
| S112 | Complete | Define paper run comparison input contract. | Explicit comparison set containing paper run references, comparison purpose, and context. | No scoring engine or report generation. |
| S113 | Complete | Add paper run comparison summary. | Deterministic caller-supplied comparison facts, assumptions, warnings, and missing-evidence fields. | No dashboard, plotting, broad report, scoring, ranking, or artifact-loading behavior. |
| S114 | Planned | Add paper run review decision record. | Human-controlled review status, rationale, reviewer context, and timestamp tied to a comparison summary. | No automatic capital deployment or live-readiness claim. |
| S115 | Planned | Add review manifest and comparison references. | Local manifest/reference contracts for comparison summaries and review decisions. | No database, hosted service, or workflow execution. |
| S116 | Planned | Close milestone. | Milestone 21 documentation refresh. | No scope expansion. |

## Planned Capabilities

Milestone 21 should introduce small typed local boundaries for:

- paper run references
- paper run comparison inputs
- paper run comparison summaries
- paper run review decision records
- review manifests and comparison references

These contracts should make paper review explicit and inspectable while keeping the project local, deterministic, and human-controlled.

## Comparison Boundary Semantics

A paper run reference is only a pointer to an existing paper artifact or paper result summary. It does not load, parse, score, or validate the referenced artifact.

A paper run comparison input is only an explicit comparison set. It defines what is being compared and why; it does not discover runs automatically.

A paper run comparison summary is descriptive context. Comparison facts, assumptions, warnings, and missing-evidence fields are caller-supplied and do not form an automatic scoring engine.

A paper run review decision record is a human-controlled review artifact. It records status and rationale, but it is not live readiness, real-money readiness, broker approval, autonomous strategy approval, or a capital deployment decision.

A review manifest is an in-memory/local reference contract for inspection. It should not read from disk, write to disk, create reports, persist data, or run workflows unless a later sprint explicitly defines that behavior.

## Assumptions And Limits

- comparison remains explicit-input driven
- paper run artifacts remain immutable inputs
- paper run references do not imply artifact loading
- comparison summaries are descriptive, not autonomous scoring engines
- review decisions are human-controlled records
- review records do not approve live trading or real-money deployment
- configured paper workflow behavior remains unchanged
- promotion records remain separate from paper comparison records
- local typed contracts are enough for this milestone

## Explicitly Out Of Scope

Milestone 21 must not introduce:

- paper workflow execution changes
- configured paper workflow behavior changes
- automatic paper run discovery
- artifact loading/parsing/scoring beyond explicit contracts
- automatic research-to-paper promotion changes
- automatic strategy approval
- automatic strategy-signal-to-order conversion
- automatic construction of paper orders, fills, or `PaperRunRequest`
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
- automatic capital deployment decisions
- live-readiness claims
- real-money readiness claims

## Exit Criteria

Milestone 21 will be complete when:

- paper run references are explicit and typed
- comparison inputs can group multiple paper run references without discovering or loading runs automatically
- comparison evidence can be summarized deterministically with source facts, assumptions, warnings, and missing-evidence fields
- explicit review decision records capture comparison evidence, rationale, status, reviewer context, and timestamp
- review manifests and comparison references can be inspected locally
- documentation explains comparison assumptions, limits, and future decision boundaries
- dashboards, broad reporting, broker behavior, live behavior, runtime execution expansion, database behavior, automatic capital deployment decisions, and strategy expansion remain outside the milestone

## Next Step

```text
Sprint 114 — Paper Run Review Decision Record Foundation
```

Sprint 114 should add human-controlled paper run review decision records tied to comparison summaries without automatic approval, ranking, capital deployment, broker behavior, or readiness claims.
