# El-Psy-Quant Roadmap

## Purpose

This roadmap turns the sprint-by-sprint project plan into a clear milestone timeline.

It is a rolling plan, not a contract. The order can change if the project learns something important, but the guiding principle stays the same:

```text
Build a reproducible research platform before chasing strategy complexity.
```

For the longer-term founder-level CTO platform plan, see:

```text
docs/strategy/future-platform-roadmap.md
```

## Timeline Overview

```mermaid
flowchart LR
    M1["Milestone 1<br/>Research Pipeline Foundation<br/>Sprints 1-7 ✅"] --> M2["Milestone 2<br/>Performance & Local Data Foundation<br/>Sprints 8-12 ✅"]
    M2 --> M3["Milestone 3<br/>Data Reproducibility & Research Workflow<br/>Sprints 13-16 ✅"]
    M3 --> M4["Milestone 4<br/>Research Experimentation Foundation<br/>Sprints 17-20 ✅"]
    M4 --> M5["Milestone 5<br/>Strategy Realism Foundation<br/>Sprints 21-24 ✅"]
    M5 --> M6["Milestone 6<br/>Risk & Benchmark Foundation<br/>Sprints 25-28 ✅"]
    M6 --> M7["Milestone 7<br/>Multi-Asset Research Foundation<br/>Sprints 29-32 ✅"]
    M7 --> M8["Milestone 8<br/>Research Operations Foundation<br/>Sprints 33-36 ✅"]
    M8 --> M9["Milestone 9<br/>Project Quality Foundation<br/>Sprints 37-41 ✅"]
    M9 --> M10["Milestone 10<br/>Experiment Artifact & Comparison Foundation<br/>Sprints 42-46 ✅"]
    M10 --> M11["Milestone 11<br/>Strategy Interface Foundation<br/>Sprints 47-52 ✅"]
    M11 --> M12["Milestone 12<br/>Data Integrity & Universe Foundation<br/>Sprints 53-57 ✅"]
    M12 --> M13["Milestone 13<br/>Portfolio Construction Foundation<br/>Sprints 58-63 ✅"]
    M13 --> M14["Milestone 14<br/>Portfolio Risk & Attribution Foundation<br/>Sprints 64-69 ✅"]
    M14 --> M15["Milestone 15<br/>Backtest Execution Realism Foundation<br/>Sprints 70-76 ✅"]
    M15 --> M16["Milestone 16<br/>Paper Trading Foundation<br/>Sprints 77-83 ✅"]
    M16 --> M17["Milestone 17<br/>Paper Trading Persistence & Audit Foundation<br/>Sprints 84-89 ✅"]
    M17 --> M18["Milestone 18<br/>Paper Trading Workflow Integration Foundation<br/>Sprints 90-95 ✅"]
    M18 --> M19["Milestone 19<br/>Configured Paper Workflow Wiring Foundation<br/>Sprints 96-102 ✅"]
    M19 --> M20["Milestone 20<br/>Research-to-Paper Promotion Foundation<br/>Sprints 103-109 ✅"]
    M20 --> M21["Milestone 21<br/>Paper Run Comparison and Review Foundation<br/>Sprints 110-116 ✅"]
    M21 --> M22["Milestone 22<br/>Decision Governance Foundation<br/>Sprints 117-123 ✅"]
    M22 --> M23["Milestone 23<br/>Report Artifact Foundation<br/>Sprints 124-129 ✅"]
    M23 --> M24["Milestone 24<br/>Strategy Review Workflow Foundation<br/>Sprints 130-136 🟡"]
```

## Milestone Table

| Milestone | Sprint Range | Status | Theme | Exit Criteria |
|---|---:|---|---|---|
| Milestone 1 — Research Pipeline Foundation | Sprints 1-7 | Complete | Build the first minimal moving-average crossover research pipeline. | Close prices can produce signals, positions, returns, and an equity curve. |
| Milestone 2 — Performance & Local Data Foundation | Sprints 8-12 | Complete | Add evaluation metrics and deterministic local CSV input. | The project can summarize backtests and run research from local CSV data. |
| Milestone 3 — Data Reproducibility & Research Workflow | Sprints 13-16 | Complete | Add local cache, Yahoo-to-cache workflow, and CSV-to-pipeline helper. | Local market data workflows can be persisted and reused. |
| Milestone 4 — Research Experimentation Foundation | Sprints 17-20 | Complete | Make experiments repeatable and comparable. | Parameter runs can be executed and summarized without claiming false alpha. |
| Milestone 5 — Strategy Realism Foundation | Sprints 21-24 | Complete | Add realistic frictions and trade-level visibility. | Backtests include basic costs, slippage, and trade records. |
| Milestone 6 — Risk & Benchmark Foundation | Sprints 25-28 | Complete | Improve evaluation discipline. | Results can be compared against benchmarks and basic risk-adjusted metrics. |
| Milestone 7 — Multi-Asset Research Foundation | Sprints 29-32 | Complete | Move from single-symbol to multi-symbol research. | The platform can load, run, and summarize independent multi-symbol research workflows. |
| Milestone 8 — Research Operations Foundation | Sprints 33-36 | Complete | Make repeated research workflows easier to run and inspect. | Experiments can be configured, executed, and stored more consistently. |
| Milestone 9 — Project Quality Foundation | Sprints 37-41 | Complete | Add automated quality gates and repository hygiene. | Pull requests can be checked consistently. |
| Milestone 10 — Experiment Artifact & Comparison Foundation | Sprints 42-46 | Complete | Make experiment outputs easier to inspect, persist, and compare. | Runs can produce and compare stable artifacts. |
| Milestone 11 — Strategy Interface Foundation | Sprints 47-52 | Complete | Define cleaner strategy boundaries before adding more strategies. | Strategies plug into configured workflows through a stable interface. |
| Milestone 12 — Data Integrity & Universe Foundation | Sprints 53-57 | Complete | Improve data validation, symbol-universe discipline, and input assumptions. | Configured runs validate symbol and price inputs before strategy execution. |
| Milestone 13 — Portfolio Construction Foundation | Sprints 58-63 | Complete | Define portfolio-level construction before attribution and execution realism. | Portfolio inputs, equal-weight returns, configurable static weights, and summary artifacts are explicit. |
| Milestone 14 — Portfolio Risk & Attribution Foundation | Sprints 64-69 | Complete | Explain portfolio-level behavior after construction is explicit. | Portfolio risk, drawdown, contribution, and attribution summaries are available. |
| Milestone 15 — Backtest Execution Realism Foundation | Sprints 70-76 | Complete | Make backtest execution assumptions explicit and reviewable. | Order intent, assumed fills, execution summaries, and realism artifacts are available. |
| Milestone 16 — Paper Trading Foundation | Sprints 77-83 | Complete | Define local paper-trading state and records before external execution. | Paper account state, orders, fills, session summaries, and artifacts are available. |
| Milestone 17 — Paper Trading Persistence & Audit Foundation | Sprints 84-89 | Complete | Make local paper outputs durable and audit-friendly. | Paper artifacts can be saved, loaded, validated, and summarized locally. |
| Milestone 18 — Paper Trading Workflow Integration Foundation | Sprints 90-95 | Complete | Turn paper-trading building blocks into an explicit workflow boundary. | A paper run request can produce, persist, and summarize a local paper artifact. |
| Milestone 19 — Configured Paper Workflow Wiring Foundation | Sprints 96-102 | Complete | Wire the explicit paper workflow into configured local runs. | Configured paper inputs can produce, persist, and reference paper outputs locally. |
| Milestone 20 — Research-to-Paper Promotion Foundation | Sprints 103-109 | Complete | Define explicit promotion governance between research evidence and paper candidates. | Evidence, candidates, promotion records, and manifests are human-controlled. |
| Milestone 21 — Paper Run Comparison and Review Foundation | Sprints 110-116 | Complete | Define explicit comparison and review governance for multiple paper runs. | Paper runs can be referenced, grouped, summarized, reviewed, and listed locally. |
| Milestone 22 — Decision Governance Foundation | Sprints 117-123 | Complete | Define strategy-level decision governance above promotion and paper-review evidence. | Decision evidence, summaries, records, manifests, and references are explicit. |
| Milestone 23 — Report Artifact Foundation | Sprints 124-129 | Complete | Package completed governance records into deterministic review artifacts. | Report sources, sections, summaries, references, and manifests are explicit without report-generation runtime behavior. |
| Milestone 24 — Strategy Review Workflow Foundation | Sprints 130-136 | In Progress | Define human-controlled lifecycle state and transition governance above completed M20–M23 records. | Evidence references, state snapshots, proposals, transition records, manifests, and guardrails are explicit without runtime lifecycle execution. |

## Completed Milestone 20 — Research-to-Paper Promotion Foundation

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

See:

```text
docs/milestones/milestone-020-research-to-paper-promotion-foundation.md
docs/sprints/sprint-103-milestone-20-planning.md
docs/sprints/sprint-109-milestone-20-documentation-refresh.md
```

## Completed Milestone 21 — Paper Run Comparison and Review Foundation

```text
paper run reference contract
  -> paper run comparison input contract
  -> paper run comparison summary
  -> paper run review decision record
  -> review manifest and comparison references
```

See:

```text
docs/milestones/milestone-021-paper-run-comparison-review-foundation.md
docs/sprints/sprint-110-milestone-21-planning.md
docs/sprints/sprint-116-milestone-21-documentation-refresh-closeout.md
```

## Completed Milestone 22 — Decision Governance Foundation

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
```

See:

```text
docs/milestones/milestone-022-decision-governance-foundation.md
docs/sprints/sprint-117-milestone-22-planning.md
docs/sprints/sprint-123-milestone-22-documentation-refresh-closeout.md
```

## Completed Milestone 23 — Report Artifact Foundation

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S124 | Complete | Plan Milestone 23. | Report artifact scope, sequence, and guardrails. | No implementation during planning. |
| S125 | Complete | Define report source references. | Typed references to completed governance records and manifests. | No artifact discovery, loading, parsing, scoring, or report generation. |
| S126 | Complete | Define report section contract. | Caller-supplied section content with explicit source references. | No rendering pipeline, dashboard, markdown/PDF generation, or workflow execution. |
| S127 | Complete | Add report artifact summary. | Caller-supplied summaries that group explicit sections. | No recommendation engine, metric calculation, scoring, ranking, dashboards, or reports. |
| S128 | Complete | Add report manifest and references. | Local references and manifests for report summaries. | No file I/O, database, hosted service, dashboard, report engine, or workflow execution. |
| S129 | Complete | Close milestone. | Documentation refresh and closeout. | No scope expansion. |

Completed chain:

```text
report source reference contract
  -> report section contract
  -> report artifact summary
  -> report artifact reference and manifest contracts
  -> report artifact closeout
```

See:

```text
docs/milestones/milestone-023-report-artifact-foundation.md
docs/sprints/sprint-124-milestone-23-planning.md
docs/sprints/sprint-129-milestone-023-documentation-refresh-and-closeout.md
```

## Milestone 24 — Strategy Review Workflow Foundation

Milestone 24 is contract-only and human-controlled.

Approved lifecycle vocabulary:

```text
research_review
paper_review
watchlist
on_hold
rejected
```

Planned sequence:

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S130 | Complete | Plan Milestone 24. | Scope, vocabulary, transitions, evidence rules, sequence, and guardrails. | Documentation only; no runtime behavior. |
| S131 | Complete | Define strategy review evidence references. | Typed pointers to completed M20–M23 governance records and manifests. | No discovery, loading, parsing, scoring, ranking, evaluation, or workflow execution. |
| S132 | Complete | Define lifecycle state snapshots. | Caller-supplied immutable declarations using the five approved lifecycle states. | No implicit initial state, mutable state store, persistence, state-machine service, or transition behavior. |
| S133 | Planned | Define lifecycle transition proposals. | Explicit from-state, target-state, rationale, evidence, and requester context. | A proposal does not change state or approve anything. |
| S134 | Planned | Add human-controlled lifecycle transition records. | Reviewer outcome, rationale, approval context, and resulting-state reference. | No automatic approval, transition execution, broker behavior, or readiness claim. |
| S135 | Planned | Add workflow manifests and references. | Local references and manifests for state snapshots, proposals, and transition records. | No file I/O, database, hosted orchestration, dashboard, or workflow engine. |
| S136 | Planned | Close milestone. | Documentation refresh and closeout. | No scope expansion. |

Planned chain:

```text
strategy review evidence reference contract
  -> strategy lifecycle state snapshot contract
  -> lifecycle transition proposal contract
  -> human-controlled lifecycle transition record
  -> strategy review workflow manifest and references
  -> strategy review workflow closeout
```

A lifecycle state is an explicit declaration, not stored mutable state. A proposal is not an action. A transition record is a human-controlled governance artifact, not an executor. `live_candidate`, live readiness, broker behavior, capital deployment, databases, hosted orchestration, and automatic transitions remain outside Milestone 24.

See:

```text
docs/milestones/milestone-024-strategy-review-workflow-foundation.md
docs/sprints/sprint-130-milestone-24-planning.md
```

## Future Platform Direction

Sprint 132 is complete. The next step is:

```text
Sprint 133 — Lifecycle Transition Proposal Foundation
```

Longer-term phases remain:

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Broker Readiness & Execution Governance
Phase 5 — Controlled Live Pilot & Production Operations
```

## Roadmap Principles

1. Local reproducibility beats live convenience.
2. Evaluation discipline comes before strategy complexity.
3. Parameter search is not alpha discovery.
4. Costs, slippage, and benchmarks should arrive before serious strategy claims.
5. Multi-asset research should come after the single-asset workflow is stable.
6. CLI and operations should wrap stable functions, not drive architecture.
7. Automated quality gates should verify claims before humans review deeper logic.
8. Every milestone should leave the repository easier to understand than before.
9. Experiments that cannot be inspected later are not research assets.
10. Strategy interfaces should come before strategy proliferation.
11. Data validation should protect the strategy boundary before more strategies are added.
12. Portfolio construction should define capital, alignment, and allocation assumptions before portfolio risk attribution.
13. Portfolio risk should be explainable before execution realism.
14. Execution assumptions should be explicit before paper trading.
15. Paper trading state should be explicit before broker integration.
16. Paper trading artifacts should be durable and audit-friendly before runtime workflows or broker integration.
17. Paper trading workflows should be explicit before configured-run integration or broker readiness.
18. Configured paper workflows should stay local and explicit before decision records, broker readiness, or live-readiness claims.
19. Promotion records should be explicit and human-controlled; they are not automatic approval engines.
20. Paper run comparison should stay explicit, local, and review-driven before dashboards, report engines, broker readiness, or capital deployment decisions.
21. Decision governance should sit above promotion and paper-review evidence before dashboards, broad reports, broker readiness, live-readiness claims, or capital deployment decisions.
22. Report artifacts should package completed governance records for review before dashboards, broad report engines, hosted reporting, broker readiness, live-readiness claims, or capital deployment decisions.
23. Strategy lifecycle workflow must remain human-controlled, explicit, and evidence-backed before broker readiness or live execution.
24. A lifecycle proposal is not an action, and a lifecycle record is not a runtime transition executor.

## Current Next Step

```text
Sprint 133 — Lifecycle Transition Proposal Foundation
```

Reason:

Sprint 132 added explicit caller-supplied immutable lifecycle state snapshots using the five approved states. Snapshots have no implicit initial state, are not mutable current state, and do not request, approve, reject, validate, or execute transitions. Sprint 133 should define explicit lifecycle transition proposals without transition validation or execution.
