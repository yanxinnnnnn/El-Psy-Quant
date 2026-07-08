# Sprint 110 — Milestone 21 Planning

## Status

Complete.

## Objective

Plan Milestone 21 after Milestone 20 closed.

Sprint 110 defines the next conservative platform layer after research-to-paper promotion governance: Paper Run Comparison and Review Foundation.

This is a planning and documentation sprint. It does not add runtime behavior.

## Founder-Level Direction

El-Psy-Quant should keep moving from local paper workflow and promotion governance toward explicit decision review.

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
  -> controlled live readiness
```

The near-term goal is not dashboards, broad reporting, broker readiness, live trading, runtime automation, or strategy expansion. The next goal is to compare multiple paper run outputs and record review decisions in a small, explicit, human-controlled way.

## Completed Context

Milestone 18 completed the explicit local paper workflow boundary:

```text
paper run request contract
  -> paper run execution boundary
  -> paper run artifact persistence
  -> paper run result summary
```

Milestone 19 connected that workflow to configured local runs:

```text
paper workflow config contract
  -> configured paper request builder
  -> configured paper output layout
  -> configured paper workflow runner
  -> configured paper manifest and result references
```

Milestone 20 completed research-to-paper promotion governance:

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

Together, these milestones can produce local paper outputs and promotion records, but they do not yet define how multiple paper runs should be compared or how a human review decision should be recorded.

## Milestone 21 Decision

Milestone 21 should be:

```text
Paper Run Comparison and Review Foundation
```

## Why This Is The Right Next Step

The project now has:

- explicit paper run requests and results
- configured paper workflow wiring
- promotion source references
- promotion candidates
- evidence summaries
- human-controlled promotion records
- promotion manifests and candidate references

The missing layer is structured paper-run comparison and review.

Without this milestone, the project has two bad options:

1. manually inspect paper outputs with no stable comparison contract
2. jump to dashboards, reports, or live-readiness language before the review model exists

Both are premature.

The right next step is to define a small comparison-and-review boundary that can answer:

- which paper runs are being compared
- what identity and context each paper run has
- what comparison facts are being summarized
- what warnings, assumptions, or missing evidence remain
- what human review decision was recorded
- where comparison and review records can be referenced

This is review governance, not capital deployment automation.

## Alternatives Considered

### Dashboard Foundation

Rejected for now.

Dashboards become useful after comparison and review records are stable. A visual layer before review semantics would make the platform look more mature than it is.

### Broad Report Generation

Rejected for now.

Reports should follow stable comparison and decision records. Milestone 21 should define the data contracts first, not a report engine.

### Broker Readiness

Rejected for now.

Broker-facing work should wait until research, paper workflow, promotion, comparison, and review decision records are explicit.

### Live Readiness Checklist

Rejected for now.

Live readiness claims require stronger review, risk, and operational boundaries than the project currently has.

### Automatic Paper Run Discovery

Rejected for now.

Milestone 21 should use explicit paper run references supplied by callers. It should not scan directories, discover runs automatically, or infer comparison sets.

### Automatic Capital Deployment Decisions

Rejected.

A comparison summary or review decision record must not approve live trading, allocate capital, or trigger any execution workflow.

### Strategy Expansion

Rejected for now.

More strategies are still not the bottleneck. The bottleneck is the decision system around existing research and paper outputs.

## Planned Milestone 21 Chain

```text
paper run reference contract
  -> paper run comparison input contract
  -> paper run comparison summary
  -> paper run review decision record
  -> review manifest and comparison references
  -> paper run comparison and review closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S110 | Complete | Plan Milestone 21. | Paper run comparison and review scope, sequence, and guardrails. | No implementation during planning. |
| S111 | Planned | Define paper run references. | Small typed references to existing paper run artifacts or result summaries. | No artifact loading or automatic discovery. |
| S112 | Planned | Define paper run comparison input contract. | Explicit comparison set containing paper run references, comparison purpose, and context. | No scoring engine or report generation. |
| S113 | Planned | Add paper run comparison summary. | Deterministic caller-supplied comparison facts, assumptions, warnings, and missing-evidence fields. | No dashboard, plotting, or broad report behavior. |
| S114 | Planned | Add paper run review decision record. | Human-controlled review status, rationale, reviewer context, and timestamp tied to a comparison summary. | No automatic capital deployment or live-readiness claim. |
| S115 | Planned | Add review manifest and comparison references. | Local manifest/reference contracts for comparison summaries and review decisions. | No database, hosted service, or workflow execution. |
| S116 | Planned | Close milestone. | Milestone 21 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 21 may include:

- a minimal paper run reference contract for existing paper artifacts or paper result summaries
- an explicit paper run comparison input object
- deterministic comparison summary data supplied by callers
- assumptions, warnings, and missing-evidence fields for comparison review
- a human-controlled paper run review decision record
- local manifest/reference contracts for comparison and review artifacts
- documentation of comparison assumptions, limits, and future decision boundaries

## Explicitly Out Of Scope

Milestone 21 must not introduce:

- paper workflow execution changes
- configured paper workflow behavior changes
- automatic paper run discovery
- artifact loading/parsing/scoring beyond explicit contracts
- automatic promotion changes
- autonomous strategy approval
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

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

That means Milestone 21 should first define small typed contracts and deterministic builders. A paper run reference is only a pointer. A comparison summary is not a scoring engine. A review decision record is a human-controlled review artifact, not a live-readiness claim.

The safest shape is:

```text
paper run artifacts stay immutable
comparison inputs stay explicit
comparison summaries stay descriptive
review decisions stay human-controlled
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

Milestone 21 starts the paper comparison and review layer before dashboards, broad reports, broker readiness, or live-readiness claims.

## Next Step

```text
Sprint 111 — Paper Run Reference Contract Foundation
```

Sprint 111 should define the smallest useful paper run reference contract for existing paper outputs. It should not load artifacts deeply, discover runs automatically, compare metrics, generate reports, execute paper workflows, add broker behavior, or claim readiness for live or real-money trading.
