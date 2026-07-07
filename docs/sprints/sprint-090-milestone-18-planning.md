# Sprint 90 — Milestone 18 Planning

## Objective

Plan Milestone 18 after Milestone 17 closed.

Sprint 90 is a planning sprint. It defines the next milestone direction, sprint sequence, boundaries, and long-term platform context without adding implementation behavior.

## Founder-Level Direction

El-Psy-Quant should not become a loose collection of strategy scripts.

The long-term company-level product direction is:

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The platform should evolve through this capability curve:

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
  -> decision review
  -> controlled live readiness
```

The near-term goal is still not live trading. The next goal is to turn existing paper-trading building blocks into an explicit local workflow.

## Completed Context

Milestone 16 completed the in-memory local paper-trading foundation:

```text
paper account state
  -> paper order ledger
  -> paper fill application
  -> paper trading session summary
  -> paper trading artifact
```

Milestone 17 completed local persistence and audit for paper-trading artifacts:

```text
paper artifact file contract
  -> local paper artifact writer
  -> local paper artifact reader and validation
  -> paper session audit summary
```

Together, these milestones make paper-trading sessions explicit, durable, reloadable, validated, and reviewable.

## Milestone 18 Decision

Milestone 18 should be:

```text
Paper Trading Workflow Integration Foundation
```

## Why This Is The Right Next Step

The project now has two sets of capabilities:

1. in-memory paper-trading session construction
2. local paper artifact persistence and audit

Those capabilities are useful, but still too manual and fragmented.

The next conservative platform step is to define one explicit local workflow boundary that can:

- accept a paper run request
- execute the existing paper-trading session construction path
- produce a paper trading artifact
- persist the artifact with the Milestone 17 writer
- return a compact run result summary

This integrates existing capabilities without jumping to broker integration, live execution, dashboards, databases, or broad report generation.

## Alternatives Considered

### Broker Readiness

Rejected for now.

Broker readiness is important later, but it would be premature before paper trading has a local workflow boundary and explicit promotion/review discipline.

### Reporting Or Dashboard Foundation

Rejected for now.

Reports and dashboards become useful after workflows stabilize. Building display layers before workflow integration risks creating polished output around immature process boundaries.

### Strategy Expansion

Rejected for now.

More strategies are not the bottleneck. The bottleneck is turning existing strategy outputs and paper-trading capabilities into reviewable operating workflows.

### Database Or Artifact Service

Rejected for now.

The local filesystem is still sufficient. A database would add migration and operational complexity before the project has earned it.

## Planned Milestone 18 Chain

```text
paper run request contract
  -> paper run execution boundary
  -> paper run artifact persistence
  -> paper run result summary
  -> paper workflow closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S90 | Complete | Plan Milestone 18. | Workflow integration scope, sequence, and long-term platform context. | No implementation during planning. |
| S91 | Planned | Define paper run request contract. | Small immutable request boundary for one local paper run. | No execution or file writing yet. |
| S92 | Planned | Add paper run execution boundary. | Build a paper trading artifact from an explicit request. | No CLI, broker, or configured-run integration. |
| S93 | Planned | Add paper run artifact persistence. | Persist a paper run artifact to an explicit local path using M17 writer. | No default output-root workflow. |
| S94 | Planned | Add paper run result summary. | Compact summary tying request, artifact identity, saved path, and audit facts. | No dashboard or report generation. |
| S95 | Planned | Close milestone. | Milestone 18 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 18 may include:

- a local paper run request contract
- deterministic paper run execution from explicit in-memory inputs
- paper trading artifact creation through existing M16 boundaries
- explicit local artifact persistence through existing M17 writer
- compact result summary for local workflow review
- documentation of assumptions and limits

## Explicitly Out Of Scope

Milestone 18 must not introduce:

- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- real account synchronization
- configured-run integration unless explicitly deferred to a later milestone
- CLI workflow expansion
- default output-root workflow unless explicitly planned later
- database behavior
- dashboard behavior
- broad report generation
- strategy expansion
- portfolio optimizer behavior
- plugin frameworks or dynamic loading

## Longer-Term Roadmap Alignment

The long-term platform direction is now captured in:

```text
docs/strategy/future-platform-roadmap.md
```

The broad phases are:

```text
Phase 1 — Research & Artifact Foundation
Phase 2 — Workflow Integration Foundation
Phase 3 — Decision Intelligence Foundation
Phase 4 — Broker Readiness & Execution Governance
Phase 5 — Controlled Live Pilot & Production Operations
```

Milestone 18 starts Phase 2.

## Next Step

```text
Sprint 91 — Paper Run Request Contract Foundation
```

Sprint 91 should define the smallest useful request object for one local paper run. It should not execute the workflow, write files, add CLI behavior, or connect to configured runs.
