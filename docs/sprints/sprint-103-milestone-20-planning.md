# Sprint 103 — Milestone 20 Planning

## Objective

Plan Milestone 20 after Milestone 19 closed.

Sprint 103 is a planning sprint. It defines the next milestone direction, sprint sequence, boundaries, and long-term platform context without adding implementation behavior.

## Founder-Level Direction

El-Psy-Quant should keep moving from configured local workflows toward explicit decision governance.

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

The near-term goal is not broker integration, live trading, dashboards, or strategy expansion. The next goal is to make promotion from research evidence into paper-trading review explicit, human-controlled, and auditable.

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

Milestone 19 completed configured local paper workflow wiring:

```text
paper workflow config contract
  -> configured paper request builder
  -> configured paper output layout
  -> configured paper workflow runner
  -> configured paper manifest and result references
```

Together, these milestones make configured local paper workflows possible when explicit paper-run inputs are provided. They do not yet define how research evidence should be nominated for paper trading review.

## Milestone 20 Decision

Milestone 20 should be:

```text
Research-to-Paper Promotion Foundation
```

## Why This Is The Right Next Step

The project now has stable local research, backtest, execution-realism, portfolio, artifact, and configured paper workflow foundations. The missing layer is governance between research evidence and paper-trading action.

Without this milestone, the project has two bad choices:

1. manually jump from research outputs to paper runs with no structured record
2. over-automate research-to-paper conversion too early

Both are wrong.

The right next step is to define a conservative promotion boundary that can answer:

- what research or execution artifact is being considered
- what evidence is being used
- what paper-trading candidate is being proposed
- who or what explicitly recorded the promotion intent
- what assumptions, warnings, and limits are attached
- where the candidate and promotion record are referenced

This is decision governance, not trading automation.

## Alternatives Considered

### Broker Readiness

Rejected for now.

Broker readiness matters later, but adding broker-facing concepts before promotion governance would create execution complexity before the project knows how to review strategy evidence.

### Live Or Simulated Live Execution

Rejected for now.

Milestone 20 should remain local and deterministic. It should not introduce market data streaming, scheduler behavior, order routing, account synchronization, or unattended execution.

### Paper Run Comparison And Review

Deferred.

Paper run comparison is useful, but comparison should follow explicit promotion records. The project should first know why a paper run candidate exists before comparing many paper runs.

### Reporting Or Dashboard Foundation

Rejected for now.

Reports and dashboards become useful after promotion records and paper review artifacts are stable. Building presentation layers first would make immature governance look more mature than it is.

### Strategy Expansion

Rejected for now.

More strategies are not the bottleneck. The bottleneck is making the research-to-paper decision path explicit and reviewable.

### Automatic Research-To-Paper Promotion

Rejected.

Milestone 20 must not automatically approve strategies, convert research artifacts into paper orders, or execute paper workflows from research outputs. Promotion must be explicit and reviewable.

### Database Or Artifact Service

Rejected for now.

The local filesystem remains sufficient. A database would add migration, deployment, and operational concerns before local promotion records are stable.

## Planned Milestone 20 Chain

```text
promotion source reference contract
  -> paper promotion candidate contract
  -> promotion evidence summary
  -> explicit promotion record
  -> promotion manifest and candidate references
  -> research-to-paper promotion closeout
```

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S103 | Complete | Plan Milestone 20. | Research-to-paper promotion scope, sequence, and guardrails. | No implementation during planning. |
| S104 | Planned | Define promotion source references. | Small typed references to research, backtest, execution, portfolio, or configured-run artifacts used as promotion evidence. | No artifact loading, scoring, or promotion decision yet. |
| S105 | Planned | Define paper promotion candidate contract. | Explicit paper-trading candidate boundary linked to source references and manual review context. | No `PaperRunRequest` construction or paper workflow execution. |
| S106 | Planned | Add promotion evidence summary. | Compact deterministic evidence summary for a candidate, including assumptions, warnings, and source facts. | No automatic pass/fail approval engine. |
| S107 | Planned | Add explicit promotion record. | Human-controlled promotion record tying candidate, evidence, rationale, and status together. | No autonomous strategy approval or live-readiness claim. |
| S108 | Planned | Add promotion manifest and candidate references. | Local artifact/reference wiring for promotion records and paper candidates. | No database, dashboard, or broad report generation. |
| S109 | Planned | Close milestone. | Milestone 20 documentation refresh. | No scope expansion. |

## Included Capabilities

Milestone 20 may include:

- a minimal promotion source reference contract for existing local artifacts
- a paper promotion candidate object that is explicit, typed, and reviewable
- deterministic evidence summary data supplied from local artifact facts or explicit inputs
- clear assumptions, warnings, and missing-evidence fields
- an explicit promotion record with candidate identity, rationale, status, and source references
- local persistence or manifest references for promotion artifacts, if kept narrow
- documentation of promotion assumptions, limits, and future decision boundaries

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

## Design Notes For Implementation Sprints

Implementation sprints should preserve the existing architecture rule:

```text
CLI and operations should wrap stable functions, not drive architecture.
```

That means Milestone 20 should first define small typed contracts and deterministic builders. A promotion candidate is not an approval. A promotion record is not a live-trading decision. Evidence summaries should explain what is known and missing; they should not silently bless a strategy.

The safest shape is:

```text
source artifacts stay immutable
candidate records stay explicit
promotion records stay human-controlled
paper workflow execution stays separate
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

Milestone 19 completed the configured local workflow layer.

Milestone 20 starts the first explicit research-to-paper governance layer before paper comparison, reporting, broker readiness, or live-readiness claims.

## Next Step

```text
Sprint 104 — Promotion Source Reference Contract Foundation
```

Sprint 104 should define the smallest useful source reference contract for promotion evidence. It should not load artifacts deeply, score strategies, create paper requests, execute paper workflows, add broker behavior, or approve promotion automatically.
