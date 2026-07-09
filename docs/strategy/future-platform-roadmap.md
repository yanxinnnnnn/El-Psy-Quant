# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

This document captures the long-term company-level direction for El-Psy-Quant.

El-Psy-Quant should not become a loose collection of strategy scripts or a thin trading bot. The product direction is to build an AI-native quantitative research operating system that can turn trading ideas into reproducible, auditable, risk-aware decisions before real capital is deployed.

## Strategic North Star

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The platform should support this decision chain reliably:

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

The target is not a magic profitable strategy. The target is a trusted decision pipeline.

## Company-Level Capability Curve

The platform should move through these phases:

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Broker Readiness & Execution Governance
Phase 5 — Controlled Live Pilot & Production Operations
```

The priority order is:

```text
workflow > promotion governance > paper comparison > review decision > decision governance > reporting artifact > risk controls > broker sandbox > live
```

The wrong order would be:

```text
broker > dashboard > live > strategy zoo
```

That path would create complexity before the platform earns it.

## Phase 1 — Research & Artifact Foundation

Status: Complete through the core local paper workflow foundation.

This phase established the platform foundation:

- local data loading and validation
- reproducible research pipelines
- experiment artifacts
- strategy interface
- portfolio construction
- portfolio risk and attribution
- execution realism
- paper trading state
- paper trading artifacts
- paper artifact persistence
- paper artifact validation and audit summaries
- explicit local paper workflow boundaries

Completed milestone chain:

```text
M1-M8   basic research workflow and operations
M9      project quality foundation
M10     experiment artifact and comparison foundation
M11     strategy interface foundation
M12     data integrity and universe foundation
M13     portfolio construction foundation
M14     portfolio risk and attribution foundation
M15     backtest execution realism foundation
M16     paper trading foundation
M17     paper trading persistence and audit foundation
M18     paper trading workflow integration foundation
```

## Phase 2 — Workflow Integration Foundation

Status: Complete through Milestone 21.

This phase turned isolated capabilities into operating workflows and reviewable promotion/comparison paths.

### Milestone 19 — Configured Paper Workflow Wiring Foundation

Status: Complete.

Goal:

```text
local config
  -> validated paper run request
  -> configured output layout
  -> paper workflow execution
  -> saved paper outputs and result references
```

Purpose:

Allow local configured runs to drive the completed paper workflow after the explicit paper workflow boundary is stable.

Guardrails preserved:

- no broker integration
- no live execution
- no market data streaming
- no scheduler behavior
- no automatic research-to-paper promotion
- no automatic strategy-signal-to-order conversion
- no database
- no dashboard or broad report generation
- no strategy expansion

### Milestone 20 — Research-to-Paper Promotion Foundation

Status: Complete.

Goal:

```text
research artifact / execution artifact / configured-run artifact / paper output
  -> promotion source reference
  -> paper promotion candidate
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

Purpose:

Define what it means for research evidence to be nominated for paper-trading review.

Milestone 20 made the research-to-paper path explicit without automating approval, paper execution, broker behavior, or live-readiness claims.

Completed sprint chain:

```text
S103  Milestone 20 planning
S104  promotion source reference contract
S105  paper promotion candidate contract
S106  promotion evidence summary
S107  explicit promotion record
S108  promotion manifest and candidate references
S109  milestone closeout
```

Guardrails preserved:

- no automatic promotion
- no autonomous strategy approval
- no automatic strategy-signal-to-order conversion
- no automatic construction of paper orders, fills, or PaperRunRequest from research outputs
- no paper workflow execution from promotion records
- no broker integration
- no live readiness claims
- no database
- no dashboard or broad report generation
- no strategy expansion

### Milestone 21 — Paper Run Comparison and Review Foundation

Status: Complete.

Goal:

```text
multiple paper runs
  -> explicit comparison set
  -> comparison summary
  -> review decision record
  -> review manifest and comparison references
```

Purpose:

Move beyond one-off paper runs and make paper performance comparable and reviewable before dashboards, broad reporting, broker readiness, or live-readiness claims.

Completed sprint chain:

```text
S110  Milestone 21 planning
S111  paper run reference contract
S112  paper run comparison input contract
S113  paper run comparison summary
S114  paper run review decision record
S115  review manifest and comparison references
S116  milestone closeout
```

Delivered contracts:

- `PaperRunReference`
- `PaperRunComparisonInput`
- `PaperRunComparisonSummary`
- `PaperRunReviewDecision`
- `PaperReviewReference`
- `PaperReviewManifest`

Guardrails preserved:

- no automatic paper run discovery
- no artifact loading/parsing/scoring beyond explicit contracts
- no metric calculation/comparison/ranking
- no dashboard
- no broad report engine
- no file I/O or database behavior from review manifest contracts
- no hosted service or SaaS behavior
- no broker integration
- no live execution
- no runtime execution expansion
- no automatic capital deployment decision
- no live-readiness or real-money readiness claims
- no strategy expansion

## Phase 3 — Decision Intelligence Foundation

Recommended focus: Milestones 22-25.

This phase makes strategy decisions explicit and reviewable.

### Milestone 22 — Decision Governance Foundation

Recommended next step:

```text
Sprint 117 — Milestone 22 Planning
```

Goal direction:

```text
promotion records
  + paper comparison summaries
  + review decision records
  + review manifests
  -> explicit decision governance layer
```

Purpose:

Record why a strategy is continued, paused, rejected, promoted, or watched without jumping to dashboards, broad reports, broker behavior, live readiness, or capital deployment.

Milestone 22 should build on M20 promotion records and M21 paper comparison/review records. It should not skip ahead to live readiness.

### Milestone 23 — Report Artifact Foundation

Goal:

```text
run artifacts
  -> deterministic report artifact
```

Purpose:

Create structured report artifacts before dashboards.

Reports should summarize evidence, assumptions, risk warnings, and decision status. They should not become a visual dashboard layer yet.

### Milestone 24 — Strategy Review Workflow Foundation

Goal:

```text
candidate strategy
  -> research review
  -> paper review
  -> decision gate
```

Purpose:

Define strategy lifecycle states such as:

```text
draft
  -> research_candidate
  -> paper_candidate
  -> watchlist
  -> rejected
  -> live_candidate
```

### Milestone 25 — Portfolio-Level Decision Review Foundation

Goal:

```text
strategy candidates
  -> portfolio impact
  -> risk concentration
  -> decision recommendation
```

Purpose:

Evaluate strategies at portfolio level instead of only strategy level.

A strategy can be attractive alone and still be bad for the portfolio if it adds concentrated risk or duplicate exposure.

## Phase 4 — Broker Readiness & Execution Governance

Recommended focus: Milestones 26-30.

This phase approaches broker integration without rushing into real-money execution.

### Milestone 26 — Broker Abstraction Planning

Goal:

Define broker-facing concepts without connecting to a broker.

Questions to answer:

- order model
- account snapshot model
- fill event model
- broker error model
- retry and idempotency rules
- manual approval boundaries

### Milestone 27 — Simulated Broker Adapter Foundation

Goal:

```text
paper order
  -> simulated broker adapter
  -> simulated ack / fill / reject
```

Purpose:

Exercise broker-like behavior locally without external dependencies.

### Milestone 28 — Execution Risk Control Foundation

Goal:

Add pre-trade guardrails:

- max order size
- max position size
- max daily turnover
- max loss threshold
- symbol allowlist
- trading window
- manual approval requirement

Purpose:

Risk controls should exist before any real broker integration.

### Milestone 29 — Live Readiness Checklist Foundation

Goal:

```text
strategy evidence
  + paper performance
  + risk controls
  + operational checks
  + manual approval
  -> live readiness status
```

Purpose:

Define whether a strategy is eligible for live testing without executing live trades yet.

### Milestone 30 — Broker Sandbox Integration

Goal:

Connect to a broker sandbox or paper broker API.

Purpose:

Test external integration after local workflow, decision, and risk boundaries exist.

Guardrails:

- no real-money trading
- no unattended execution
- no auto-scaling of strategies

## Phase 5 — Controlled Live Pilot & Production Operations

Recommended focus: Milestones 31+.

This phase should only start after Phase 4 creates strong operational guardrails.

### Milestone 31 — Small-Capital Live Pilot Foundation

Goal:

Support extremely small, tightly controlled live execution.

Requirements:

- allowlisted strategy
- allowlisted symbols
- strict max exposure
- manual kill switch
- full audit trail
- no autonomous scaling

### Milestone 32 — Live Monitoring Foundation

Goal:

```text
live orders
  -> fills
  -> account state
  -> risk status
  -> alerts
```

Purpose:

Produce structured operational status artifacts before complex dashboards.

### Milestone 33 — Incident & Kill Switch Foundation

Goal:

Define how the system stops, records incidents, and recovers safely.

Questions:

- when should the system stop?
- who can stop it?
- how is the stop recorded?
- how does recovery work?
- how are repeated incidents prevented?

### Milestone 34 — Production Operations Foundation

Goal:

Document and support production operating discipline:

- runbooks
- status checks
- deployment records
- version records
- rollback rules
- operational review process

### Milestone 35+ — Productization Foundation

Possible future direction:

- multi-user workspace
- permissions
- hosted dashboard
- cloud deployment
- team collaboration
- SaaS productization

This should come after the core decision pipeline is proven.

## Core Assets To Build

### Research Memory

Every experiment, strategy, parameter set, data assumption, and result should be traceable.

### Promotion Governance

Every research-to-paper nomination should be explicit, evidence-backed, and human-controlled.

### Paper Comparison Memory

Every paper run comparison should be explicit, reproducible, and tied to stable paper run references.

### Decision Ledger

Every continue, pause, reject, promote-to-paper, and promote-to-live decision should be recorded with evidence.

### Risk Discipline

The platform should slow down bad decisions and speed up good reviews.

### Execution Readiness

Live trading should be the outcome of trusted workflow and governance, not the starting point.

## Explicit Non-Priorities

The project should not prioritize these too early:

```text
strategy count for its own sake
live broker integration
real-money trading
deep learning alpha
high-frequency trading
complex web dashboards
large databases
portfolio optimization before basic portfolio accounting
SaaS before the decision pipeline is proven
```

## One-Line Strategy

```text
Do not rush to find a magic strategy. Build a research and decision system that is hard to fool.
```