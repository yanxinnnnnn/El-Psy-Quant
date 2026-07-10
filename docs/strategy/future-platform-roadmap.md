# Future Platform Roadmap — Founder-Level CTO Plan

## Purpose

This document captures the long-term company-level direction for El-Psy-Quant.

El-Psy-Quant should not become a loose collection of strategy scripts or a thin trading bot. The product direction is to build an AI-native quantitative research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before real capital is deployed.

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
  -> report artifact
  -> strategy review workflow
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
workflow
  > promotion governance
  > paper comparison
  > review decision
  > decision governance
  > report artifact
  > strategy review workflow
  > risk controls
  > broker sandbox
  > live
```

The wrong order would be:

```text
broker > dashboard > live > strategy zoo
```

That path would create complexity before the platform earns it.

## Phase 1 — Research & Artifact Foundation

Status: Complete through the core local paper workflow foundation.

This phase established:

- local data loading and validation
- reproducible research pipelines
- experiment artifacts and comparison
- strategy interfaces
- portfolio construction
- portfolio risk and attribution
- execution realism
- paper trading state and artifacts
- paper artifact persistence and audit
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

```text
local config
  -> validated paper run request
  -> configured output layout
  -> paper workflow execution
  -> saved paper outputs and result references
```

Guardrails preserved:

- no broker integration or live execution
- no market-data streaming or scheduler behavior
- no automatic research-to-paper promotion
- no automatic strategy-signal-to-order conversion
- no database, dashboard, broad report generation, or strategy expansion

### Milestone 20 — Research-to-Paper Promotion Foundation

Status: Complete.

```text
research evidence
  -> promotion source reference
  -> paper promotion candidate
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
```

Purpose:

Define what it means for research evidence to be nominated for paper-trading review while keeping approval human-controlled.

Guardrails preserved:

- no automatic promotion or autonomous strategy approval
- no paper workflow execution from promotion records
- no broker integration or live-readiness claims
- no database, dashboard, broad report generation, or strategy expansion

### Milestone 21 — Paper Run Comparison and Review Foundation

Status: Complete.

```text
multiple paper runs
  -> explicit comparison set
  -> comparison summary
  -> review decision record
  -> review manifest and comparison references
```

Purpose:

Make paper performance comparable and reviewable before dashboards, broad reporting, broker readiness, or live-readiness claims.

Guardrails preserved:

- no automatic paper-run discovery
- no artifact loading, parsing, scoring, metric comparison, or ranking
- no dashboard or broad report engine
- no persistence or database behavior from review contracts
- no broker integration, live execution, or automatic capital deployment decision

## Phase 3 — Decision Intelligence Foundation

Status: Milestones 22 and 23 complete. Milestone 24 planning is next.

This phase makes strategy decisions, review packages, and lifecycle governance explicit and reviewable.

### Milestone 22 — Decision Governance Foundation

Status: Complete.

```text
decision evidence reference contract
  -> strategy decision input contract
  -> strategy decision summary
  -> explicit strategy decision record
  -> decision manifest and references
  -> decision governance closeout
```

Delivered contracts:

- `DecisionEvidenceReference`
- `StrategyDecisionInput`
- `StrategyDecisionSummary`
- `StrategyDecisionRecord`
- `StrategyDecisionReference`
- `StrategyDecisionManifest`

Purpose:

Record why a strategy should continue, pause, be rejected, need more evidence, or remain under review without jumping to dashboards, broker behavior, live readiness, or capital deployment.

Guardrails preserved:

- no automatic decision making, approval, or promotion
- no automatic evidence discovery or artifact loading
- no metric calculation, scoring, ranking, or winner selection
- no dashboards or broad reports
- no broker readiness, live-readiness claims, capital allocation, or workflow execution changes
- no database, hosted service, or SaaS behavior

### Milestone 23 — Report Artifact Foundation

Status: Complete.

Completed chain:

```text
report source reference contract
  -> report section contract
  -> report artifact summary
  -> report artifact reference and manifest contracts
  -> report artifact closeout
```

Delivered contracts:

- `ReportSourceReference`
- `ReportSection`
- `ReportArtifactSummary`
- `ReportArtifactReference`
- `ReportArtifactManifest`

Purpose:

Package completed governance records into deterministic, reviewable report artifacts before dashboards or broad report engines.

Guardrails preserved:

- no automatic report generation
- no rendering, dashboards, markdown/HTML/PDF generation, or broad report engine
- no automatic evidence discovery or artifact loading
- no metric calculation, scoring, ranking, recommendation, or automatic decisions
- no file I/O, manifest reading/writing, persistence services, or database behavior from report-artifact contracts
- no workflow execution, broker/live behavior, capital deployment, or readiness claims

### Milestone 24 — Strategy Review Workflow Foundation

Status: Planned. Sprint 130 should plan this milestone before implementation begins.

Candidate workflow direction:

```text
candidate strategy
  -> research review
  -> paper review
  -> decision gate
  -> human-controlled lifecycle state
```

Candidate lifecycle vocabulary may include:

```text
draft
  -> research_candidate
  -> paper_candidate
  -> watchlist
  -> rejected
  -> live_candidate
```

These states are not approved implementation details yet. Sprint 130 must decide:

- which lifecycle states are actually needed
- which transitions are permitted
- what evidence each transition requires
- which transitions require explicit human approval
- how existing promotion, paper-review, decision, and report-artifact records are referenced
- whether the milestone is contract-only or includes a narrow local transition service
- what remains explicitly outside scope

Planning guardrails:

- no automatic strategy state transitions
- no autonomous approval, rejection, promotion, or capital allocation
- no workflow execution from governance records
- no broker integration, live execution, or real-money behavior
- no dashboard or hosted workflow product
- no database-backed orchestration or SaaS behavior
- no claim that `live_candidate` means live-ready or approved for capital deployment

### Milestone 25 — Portfolio-Level Decision Review Foundation

Status: Future.

```text
strategy candidates
  -> portfolio impact
  -> risk concentration
  -> decision recommendation
```

Purpose:

Evaluate strategies at portfolio level instead of only strategy level. A strategy can be attractive alone and still be unsuitable for the portfolio if it adds concentrated risk or duplicate exposure.

## Phase 4 — Broker Readiness & Execution Governance

Recommended focus: Milestones 26-30.

This phase approaches broker integration without rushing into real-money execution.

### Milestone 26 — Broker Abstraction Planning

Define broker-facing concepts without connecting to a broker:

- order model
- account snapshot model
- fill event model
- broker error model
- retry and idempotency rules
- manual approval boundaries

### Milestone 27 — Simulated Broker Adapter Foundation

```text
paper order
  -> simulated broker adapter
  -> simulated ack / fill / reject
```

Exercise broker-like behavior locally without external dependencies.

### Milestone 28 — Execution Risk Control Foundation

Add pre-trade guardrails:

- max order size
- max position size
- max daily turnover
- max loss threshold
- symbol allowlist
- trading window
- manual approval requirement

Risk controls should exist before real broker integration.

### Milestone 29 — Live Readiness Checklist Foundation

```text
strategy evidence
  + paper performance
  + risk controls
  + operational checks
  + manual approval
  -> live readiness status
```

Define eligibility for live testing without executing live trades.

### Milestone 30 — Broker Sandbox Integration

Connect to a broker sandbox or paper-broker API only after local workflow, decision, and risk boundaries are stable.

Phase 4 guardrails:

- no real-money trading
- no unattended execution
- no autonomous scaling of strategies

## Phase 5 — Controlled Live Pilot & Production Operations

Recommended focus: Milestones 31+.

This phase should only start after Phase 4 creates strong operational guardrails.

### Milestone 31 — Small-Capital Live Pilot Foundation

Support extremely small, tightly controlled live execution with:

- allowlisted strategy and symbols
- strict maximum exposure
- manual kill switch
- full audit trail
- no autonomous scaling

### Milestone 32 — Live Monitoring Foundation

```text
live orders
  -> fills
  -> account state
  -> risk status
  -> alerts
```

Produce structured operational status artifacts before complex dashboards.

### Milestone 33 — Incident & Kill Switch Foundation

Define how the system stops, records incidents, and recovers safely.

### Milestone 34 — Production Operations Foundation

Document and support:

- runbooks
- status checks
- deployment and version records
- rollback rules
- operational review processes

### Milestone 35+ — Productization Foundation

Possible later direction:

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

Every paper-run comparison should be explicit, reproducible, and tied to stable references.

### Decision Ledger

Every continue, pause, reject, promote-to-paper, and future promote-to-live decision should be recorded with evidence.

### Report Artifact Memory

Every review package should identify its source records, sections, assumptions, warnings, missing evidence, stable summary ID, and manifest references without implying automated reporting or readiness.

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

## Current Next Step

```text
Sprint 130 — Milestone 24 Planning
```

Sprint 130 should plan the Strategy Review Workflow Foundation. It should define scope, lifecycle semantics, transition boundaries, evidence requirements, human approval requirements, sprint sequence, and exclusions before implementation begins.

## One-Line Strategy

```text
Do not rush to find a magic strategy. Build a research and decision system that is hard to fool.
```
