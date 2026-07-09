# Sprint 124 — Milestone 23 Planning

## Status

Complete after this documentation PR is merged.

## Objective

Plan **Milestone 23 — Report Artifact Foundation** after Milestone 22 closed.

Sprint 124 defines the next conservative platform layer after decision governance: deterministic report artifacts built on top of completed governance records.

This is a planning and documentation sprint. It does not add runtime behavior.

## Founder-Level Direction

El-Psy-Quant should keep moving from isolated governance records toward reviewable report artifacts, but it should not jump to dashboards, broad report engines, broker readiness, live-readiness claims, capital deployment, databases, hosted services, SaaS behavior, or automatic decisions.

The long-term product direction remains:

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The platform capability curve is now:

```text
idea
  -> data
  -> research
  -> backtest
  -> portfolio
  -> execution assumptions
  -> paper trading
  -> persistence
  -> audit
  -> configured workflow
  -> promotion governance
  -> paper comparison
  -> review decision
  -> decision governance
  -> report artifacts
  -> controlled live readiness
```

The near-term goal is not dashboards, broad reporting UI, broker behavior, live trading, runtime automation, capital deployment, or strategy expansion. The next goal is to define deterministic report artifacts that can package completed governance records for human review.

## Completed Context

Milestone 20 completed research-to-paper promotion governance:

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

Milestone 21 completed paper run comparison and review governance:

```text
paper run reference contract
  -> paper run comparison input contract
  -> paper run comparison summary
  -> paper run review decision record
  -> review manifest and comparison references
```

Milestone 22 completed strategy-level decision governance:

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
```

Together, these milestones can identify evidence, compare paper runs, record human review decisions, and capture strategy-level decisions. They do not yet define a deterministic report artifact that packages those completed records for founder review.

## Milestone 23 Decision

Milestone 23 should be:

```text
Report Artifact Foundation
```

## Why This Is The Right Next Step

The project now has:

- promotion source references
- paper promotion candidates
- promotion evidence summaries
- human-controlled promotion records
- promotion manifests and candidate references
- paper run references
- paper run comparison inputs
- paper run comparison summaries
- human-controlled review decision records
- review manifests and comparison references
- decision evidence references
- strategy decision inputs
- strategy decision summaries
- human-controlled strategy decision records
- strategy decision manifests and references

The missing layer is a deterministic report artifact boundary.

Without this milestone, the project has two bad options:

1. treat decision manifests as reports, which blurs reference contracts with review packages
2. jump to dashboards, broad report generation, or hosted reporting before report artifact semantics are stable

Both are premature.

The right next step is to define a small report-artifact boundary that can answer:

- what report is being declared
- which governance records are referenced
- what sections are included
- what facts, assumptions, warnings, or missing evidence are caller-supplied
- who or what prepared the report metadata
- which local references make the report auditable

This is report artifact governance, not report generation automation.

## Alternatives Considered

### Dashboard Foundation

Rejected for now.

Dashboards become useful after report artifact contracts are stable. A visual layer before report semantics would make the platform look more mature than it is.

### Broad Report Generation

Rejected for now.

The project should first define report artifacts as deterministic contracts. Rendering markdown, HTML, PDF, notebooks, or hosted reports can wait.

### Automatic Evidence Discovery

Rejected for now.

Milestone 23 should use explicit references supplied by callers. It should not scan directories, discover records automatically, load artifacts, parse files, or infer report inputs.

### Metric Scoring Or Ranking

Rejected.

A report artifact can include caller-supplied facts and warnings, but it must not calculate scores, rank strategies, select winners, or recommend capital allocation.

### Broker Or Live Readiness

Rejected for now.

Broker-facing work and live-readiness claims require stronger report, risk, and operational boundaries than the project currently has.

### Database Or Hosted Reporting

Rejected for now.

Milestone 23 should stay local and contract-driven. Persistence services, databases, hosted dashboards, team workspaces, and SaaS behavior are later productization concerns.

## Planned Milestone 23 Chain

```text
report source reference contract
  -> report section contract
  -> report artifact summary
  -> report manifest and references
  -> report artifact closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S124 | Complete after planning PR merge | Plan Milestone 23. | Report artifact scope, sequence, and guardrails. | No implementation during planning. |
| S125 | Planned | Define report source references. | Small typed references to existing governance records and manifests. | No artifact discovery, loading, parsing, scoring, or report generation. |
| S126 | Planned | Define report section contract. | Explicit section metadata and caller-supplied section content boundaries. | No rendering pipeline, dashboard, markdown/PDF generation, or workflow execution. |
| S127 | Planned | Add report artifact summary. | Deterministic caller-supplied facts, assumptions, warnings, missing evidence, and report context. | No recommendation engine, metric calculation, scoring, ranking, dashboards, or reports. |
| S128 | Planned | Add report manifest and references. | Local manifest/reference contracts for report summaries and report artifacts. | No file I/O, database, hosted service, dashboard, report engine, or workflow execution. |
| S129 | Planned | Close milestone. | Milestone 23 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 23 may include:

- a minimal report source reference contract for existing promotion records, promotion manifests, paper comparison summaries, paper review decisions, review manifests, strategy decision summaries, strategy decision records, and decision manifests
- explicit report section objects
- deterministic report summary data supplied by callers
- assumptions, warnings, missing-evidence, and review-context fields for report review
- local manifest/reference contracts for report summaries and artifacts
- documentation of report assumptions, limits, and future dashboard boundaries

## Explicitly Out Of Scope

Milestone 23 must not introduce:

- runtime behavior
- automatic report generation
- report rendering pipelines
- dashboards
- broad reporting UI
- plotting behavior
- markdown, HTML, PDF, notebook, or hosted report generation
- automatic evidence discovery
- artifact loading/parsing/scoring
- metric calculation, comparison, ranking, or winner selection
- recommendation engines
- automatic decision making
- automatic approval
- automatic rejection
- automatic promotion
- automatic strategy lifecycle automation
- broker readiness
- live readiness
- real-money readiness claims
- capital deployment
- capital allocation
- order routing
- broker integration
- exchange APIs
- live execution
- market data streaming
- scheduler behavior
- real account synchronization
- strategy expansion
- workflow execution changes
- configured paper workflow behavior changes
- database behavior
- hosted services or SaaS behavior

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

That means Milestone 23 should first define small typed contracts and deterministic builders only. A report source reference is only a pointer. A report section is not rendering. A report artifact summary is not a recommendation engine. A report manifest is a local reference contract, not persistence or workflow execution.

The safest shape is:

```text
governance records stay separate
report inputs stay explicit
report sections stay caller-supplied
report summaries stay descriptive
report manifests stay local reference contracts
rendering and dashboards stay separate
execution workflows stay separate
```

## Implementation Sprint Issue Requirements

Future implementation sprint issues must include the Windows proxy prelude when Codex implementation is requested:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7892"
$env:HTTPS_PROXY="http://127.0.0.1:7892"
$env:ALL_PROXY="http://127.0.0.1:7892"

git config http.proxy http://127.0.0.1:7892
git config https.proxy http://127.0.0.1:7892
```

They must also state:

- Do not use `--global`
- Do not commit proxy config
- Do not modify project files for proxy setup

## Longer-Term Roadmap Alignment

The long-term platform direction is maintained in:

```text
docs/strategy/future-platform-roadmap.md
```

The broad phases remain:

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Broker Readiness & Execution Governance
Phase 5 — Controlled Live Pilot & Production Operations
```

Milestone 20 completed promotion governance.

Milestone 21 completed paper run comparison and review governance.

Milestone 22 completed strategy-level decision governance.

Milestone 23 starts the deterministic report-artifact layer before dashboards, broad report engines, broker readiness, live-readiness claims, or capital deployment decisions.

## Next Step

```text
Sprint 125 — Report Source Reference Contract Foundation
```

Sprint 125 should define the smallest useful reference contract for completed governance records. It should not discover evidence automatically, load artifacts, calculate metrics, score strategies, render reports, execute workflows, add broker behavior, or claim readiness for live or real-money trading.
