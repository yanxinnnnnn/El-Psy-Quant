# Sprint 117 — Milestone 22 Planning

## Status

Complete.

## Objective

Plan Milestone 22 after Milestone 21 closed.

Sprint 117 defines the next conservative platform layer after research-to-paper promotion governance and paper run comparison/review: Decision Governance Foundation.

This is a planning and documentation sprint. It does not add runtime behavior.

## Founder-Level Direction

El-Psy-Quant should keep moving from paper review toward explicit strategy-level decision governance.

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
  -> controlled live readiness
```

The near-term goal is not dashboards, broad reporting, broker readiness, live trading, runtime automation, capital deployment, or strategy expansion. The next goal is to record evidence-backed strategy decisions in a small, explicit, human-controlled way.

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

Together, these milestones can identify research-to-paper candidates and review paper run comparison evidence, but they do not yet define the higher-level strategy decision record that says what the founder or reviewer decided after considering that evidence.

## Milestone 22 Decision

Milestone 22 should be:

```text
Decision Governance Foundation
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

The missing layer is strategy-level decision governance.

Without this milestone, the project has two bad options:

1. treat promotion records or paper review decisions as final strategy decisions, which blurs responsibilities
2. jump to dashboards, reports, live-readiness, or broker work before the decision ledger exists

Both are premature.

The right next step is to define a small decision-governance boundary that can answer:

- what evidence is being considered
- which promotion records or paper-review decisions support the decision
- what strategy-level decision status was chosen
- what rationale was provided
- what assumptions, warnings, or missing evidence remain
- who reviewed the decision and when
- which local references make the decision auditable

This is decision governance, not autonomous approval.

## Alternatives Considered

### Dashboard Foundation

Rejected for now.

Dashboards become useful after decision records are stable. A visual layer before decision semantics would make the platform look more mature than it is.

### Broad Report Generation

Rejected for now.

Reports should follow stable decision records. Milestone 22 should define the data contracts first, not a report engine.

### Broker Readiness

Rejected for now.

Broker-facing work should wait until research, paper workflow, promotion, paper review, and strategy decision records are explicit.

### Live Readiness Checklist

Rejected for now.

Live readiness claims require stronger decision, risk, and operational boundaries than the project currently has.

### Automatic Decision Making

Rejected.

Milestone 22 must not infer, recommend, approve, reject, promote, or allocate capital automatically. Decision summaries and records remain caller-supplied and human-controlled.

### Automatic Evidence Discovery

Rejected for now.

Milestone 22 should use explicit evidence references supplied by callers. It should not scan directories, discover records automatically, or infer decision inputs.

### Automatic Capital Deployment Decisions

Rejected.

A strategy decision record must not approve live trading, allocate capital, or trigger any execution workflow.

### Strategy Expansion

Rejected for now.

More strategies are still not the bottleneck. The bottleneck is the decision system around existing research, promotion, and paper review outputs.

## Planned Milestone 22 Chain

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
  -> decision governance closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S117 | Complete | Plan Milestone 22. | Decision governance scope, sequence, and guardrails. | No implementation during planning. |
| S118 | Planned | Define decision evidence references. | Small typed references to existing promotion records, promotion manifests, paper comparison summaries, review decisions, and review manifests. | No evidence discovery, loading, parsing, scoring, or ranking. |
| S119 | Planned | Define strategy decision input contract. | Explicit input object grouping evidence references, decision purpose, review context, and reviewer metadata. | No automatic decision generation or lifecycle automation. |
| S120 | Planned | Add strategy decision summary. | Deterministic caller-supplied facts, assumptions, warnings, missing evidence, and decision context. | No recommendation engine, metric calculation, scoring, dashboards, or reports. |
| S121 | Planned | Add explicit strategy decision record. | Human-controlled decision status, rationale, reviewer context, and timestamp tied to a decision summary. | No automatic approval, promotion, capital allocation, broker behavior, or readiness claim. |
| S122 | Planned | Add decision manifest and references. | Local manifest/reference contracts for strategy decision summaries and records. | No file I/O, database, hosted service, dashboard, report, or workflow execution. |
| S123 | Planned | Close milestone. | Milestone 22 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 22 may include:

- a minimal decision evidence reference contract for existing promotion records, promotion manifests, paper comparison summaries, paper review decisions, and review manifests
- an explicit strategy decision input object
- deterministic decision summary data supplied by callers
- assumptions, warnings, and missing-evidence fields for decision review
- a human-controlled strategy decision record
- local manifest/reference contracts for decision summaries and records
- documentation of decision assumptions, limits, and future readiness boundaries

## Explicitly Out Of Scope

Milestone 22 must not introduce:

- dashboards
- broad report generation
- plotting behavior
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
- automatic approval
- automatic promotion
- automatic strategy lifecycle automation
- automatic decision making
- automatic evidence discovery
- artifact loading/parsing/scoring
- metric calculation, comparison, ranking, or winner selection
- workflow execution changes
- configured paper workflow behavior changes
- database behavior
- hosted services or SaaS behavior

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

That means Milestone 22 should first define small typed contracts and deterministic builders. A decision evidence reference is only a pointer. A decision summary is not a recommendation engine. A strategy decision record is a human-controlled governance artifact, not a live-readiness claim.

The safest shape is:

```text
promotion records stay separate
paper review decisions stay separate
decision inputs stay explicit
decision summaries stay descriptive
decision records stay human-controlled
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

Milestone 22 starts the strategy-level decision governance layer before dashboards, broad reports, broker readiness, live-readiness claims, or capital deployment decisions.

## Next Step

```text
Sprint 118 — Decision Evidence Reference Contract Foundation
```

Sprint 118 should define the smallest useful evidence reference contract for existing promotion and paper-review evidence. It should not discover evidence automatically, load artifacts, calculate metrics, score strategies, generate reports, execute workflows, add broker behavior, or claim readiness for live or real-money trading.
