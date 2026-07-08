# Sprint 96 — Milestone 19 Planning

## Objective

Plan Milestone 19 after Milestone 18 closed.

Sprint 96 is a planning sprint. It defines the next milestone direction, sprint sequence, boundaries, and long-term platform context without adding implementation behavior.

## Founder-Level Direction

El-Psy-Quant should keep moving from isolated local research capabilities toward reproducible operating workflows.

The long-term product direction remains:

```text
Build an AI-native quant research operating system that turns trading ideas into reproducible, auditable, risk-aware decisions before any real capital is deployed.
```

The platform capability curve is still:

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
  -> decision review
  -> controlled live readiness
```

The near-term goal is not broker integration, live trading, or dashboards. The next goal is to let a local configuration layer drive the paper workflow boundaries that Milestone 18 finished.

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

Milestone 18 completed the explicit local paper workflow boundary:

```text
paper run request contract
  -> paper run execution boundary
  -> paper run artifact persistence
  -> paper run result summary
```

Together, these milestones make one local paper run explicit, executable, persistable, and reviewable when all inputs are supplied directly.

## Milestone 19 Decision

Milestone 19 should be:

```text
Configured Paper Workflow Wiring Foundation
```

## Why This Is The Right Next Step

The project now has two major workflow layers that are still separate:

1. configured local research experiments driven by YAML and the existing local run layout
2. explicit local paper runs driven by `PaperRunRequest`

Those layers should be connected carefully before the project adds decision records, reports, broker readiness, or live execution.

The next conservative platform step is to define how a local configuration can:

- describe paper-run inputs explicitly
- validate those inputs before execution
- build a `PaperRunRequest`
- reuse the Milestone 18 workflow boundary
- save paper outputs in a predictable local configured-run location
- expose a compact result summary and artifact references

This is workflow wiring, not trading automation.

## Alternatives Considered

### Broker Readiness

Rejected for now.

Broker readiness is important later, but adding broker-facing concepts before configured local paper workflows are stable would create operational complexity too early.

### Live Or Simulated Live Execution

Rejected for now.

Milestone 19 should remain local and deterministic. It should not introduce market data streaming, scheduler behavior, order routing, account synchronization, or unattended execution.

### Reporting Or Dashboard Foundation

Rejected for now.

Reports and dashboards become useful after configured paper workflows produce stable artifacts. Building presentation layers first would make immature workflows look more finished than they are.

### Strategy Expansion

Rejected for now.

More strategies are not the bottleneck. The bottleneck is connecting existing workflow boundaries into a reproducible operating path.

### Automatic Research-To-Paper Promotion

Rejected for now.

Promotion from research output into paper trading needs explicit decision governance. Milestone 19 should not automatically convert strategy signals, backtest results, or portfolio outputs into paper orders.

### Database Or Artifact Service

Rejected for now.

The local filesystem remains sufficient. A database would add migration, deployment, and operational concerns before local configured paper workflows are stable.

## Planned Milestone 19 Chain

```text
paper workflow config contract
  -> configured paper request builder
  -> configured paper output layout
  -> configured paper workflow runner
  -> configured paper manifest and result references
  -> configured paper workflow closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S96 | Complete | Plan Milestone 19. | Configured paper workflow wiring scope, sequence, and guardrails. | No implementation during planning. |
| S97 | Planned | Define paper workflow config contract. | Minimal local config section for explicit paper-run inputs. | No execution or file writing yet. |
| S98 | Planned | Build configured paper request boundary. | Convert validated config inputs into `PaperRunRequest`. | No strategy-signal-to-order automation. |
| S99 | Planned | Define configured paper output layout. | Stable local paths for paper artifacts and result summaries under configured runs. | No database or artifact service. |
| S100 | Planned | Add configured paper workflow runner. | Execute and persist a configured paper run by reusing Milestone 18 boundaries. | No broker, live, scheduler, or streaming behavior. |
| S101 | Planned | Add configured paper manifest and result references. | Record paper artifact/result paths in configured-run metadata or manifest outputs. | No dashboard or broad report generation. |
| S102 | Planned | Close milestone. | Milestone 19 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 19 may include:

- a minimal `paper_run` or equivalent local config contract
- strict validation for explicit paper account, order, fill, run identity, and timestamp inputs
- a builder that turns validated local config into `PaperRunRequest`
- deterministic paper output paths under an explicit configured run layout
- configured paper workflow execution through existing Milestone 18 functions
- persisted paper artifacts through existing Milestone 17 file behavior
- compact configured paper result references
- documentation of assumptions, limits, and future integration boundaries

## Explicitly Out Of Scope

Milestone 19 must not introduce:

- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- scheduler behavior
- real account synchronization
- automatic research-to-paper promotion
- automatic strategy-signal-to-order conversion
- portfolio optimizer behavior
- strategy expansion
- new strategy plugin frameworks
- database behavior
- dashboard behavior
- broad report generation
- hosted services or SaaS behavior
- unattended execution
- real-money readiness claims

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

That means Milestone 19 should first define small typed boundaries and pure builders. Any CLI or configured-run surface should stay thin and should reuse those boundaries rather than embedding paper workflow logic directly in the command layer.

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

Milestone 18 started Phase 2 by creating a local paper workflow boundary.

Milestone 19 continues Phase 2 by wiring that boundary into configured local workflows.

## Next Step

```text
Sprint 97 — Paper Workflow Config Contract Foundation
```

Sprint 97 should define the smallest useful local configuration contract for an explicit paper run. It should not execute the workflow, write files, add broker behavior, or convert strategy signals into orders.
