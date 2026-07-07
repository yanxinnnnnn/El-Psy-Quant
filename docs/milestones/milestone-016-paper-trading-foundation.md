# Milestone 16 — Paper Trading Foundation

## Status

Planned.

## Product Goal

Introduce a conservative paper-trading foundation after backtest execution assumptions are explicit and reviewable.

Milestone 16 should make paper trading inspectable before the project considers broker adapters, exchange APIs, or live execution.

## Why This Comes Now

Milestone 15 closed this chain:

```text
execution assumptions -> order intent boundary -> deterministic fill model -> execution-adjusted trade summary -> execution realism artifact
```

That chain made the research-side execution boundary explicit. Milestone 16 should now define a paper-trading boundary that can track simulated account state and paper execution activity without pretending to be a real broker.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S77 | Complete | Plan Milestone 16. | Paper trading scope and sprint sequence. | No implementation during planning. |
| S78 | Complete | Add paper account state. | Deterministic cash, positions, and equity snapshot boundary. | No broker account sync. |
| S79 | Planned | Add paper order ledger. | Local paper order records and status boundary. | No exchange routing. |
| S80 | Planned | Add paper fill application. | Apply assumed fills to paper account state. | No live market data. |
| S81 | Planned | Add paper trading session summary. | Reviewable paper session summary from orders, fills, and account snapshots. | No PnL analytics expansion. |
| S82 | Planned | Add paper trading artifact. | Standalone artifact for paper trading session state and assumptions. | No configured-run expansion. |
| S83 | Planned | Close milestone. | Milestone 16 documentation refresh. | No scope expansion. |

## Planned Chain

Milestone 16 should follow this conservative chain:

```text
paper account state -> paper order ledger -> paper fill application -> paper trading session summary -> paper trading artifact
```

## Planned Work

### Paper Account State

The first implementation sprint should define the smallest useful paper account state boundary.

The project should be able to represent:

- starting cash
- current cash
- positions by symbol
- current equity if prices are supplied explicitly
- account timestamp

This should be a local deterministic state object, not a broker account mirror.

### Paper Order Ledger

Paper orders should record what was submitted to the local paper-trading layer.

The ledger should distinguish:

- order intent from paper order record
- paper order record from assumed fill
- submitted, accepted, rejected, or filled state where scoped

This should not route orders to an exchange or broker.

### Paper Fill Application

Paper fill application should update paper account state using already explicit fill data.

It should answer:

- which fill was applied
- how cash changed
- how position quantity changed
- which timestamp the state reflects

This should not use live market data or real broker fills.

### Paper Trading Session Summary

Once account state, paper orders, and applied fills exist, the project should summarize a paper session in a reviewable form.

The summary should remain small and should not become a full analytics engine.

### Paper Trading Artifact

Paper trading assumptions and session outputs should become portable through a small standalone artifact.

The artifact should follow the existing project pattern: deterministic, local, JSON-compatible, and easy to inspect.

## Assumptions

Milestone 16 keeps the assumptions conservative:

- paper trading starts as local simulation, not broker integration
- paper account state is explicit and inspectable
- paper orders are local records, not routed exchange orders
- fills are applied from explicit inputs
- all behavior is deterministic and testable
- no external broker, exchange, or streaming dependency is introduced

## Guardrails

Milestone 16 should avoid:

- broker integration
- live trading behavior
- exchange APIs
- order routing
- market data streaming
- real account synchronization
- production deployment claims
- market microstructure simulation
- partial-fill complexity unless explicitly scoped later
- broad configured-run integration unless the helper boundary is already stable
- YAML or CLI expansion unless the paper boundary is already stable
- strategy proliferation
- plugin frameworks or dynamic loading

## Exit Criteria

Milestone 16 is complete when:

- paper account state is explicit and deterministic
- paper orders are recorded separately from order intents and fills
- assumed fills can be applied to paper state under clear rules
- paper trading session summaries are reviewable
- paper trading outputs can be represented in a standalone artifact
- documentation explains assumptions, limits, and what remains out of scope

## Relationship To Future Milestones

Milestone 16 prepares the project for later broker adapter and small-scale live trading work.

Broker integration should wait until paper trading state, order records, fill application, and artifacts are explicit. Otherwise, broker work can hide unresolved accounting and state-management assumptions.

## Current Next Step

```text
Sprint 79 — Paper Order Ledger Foundation
```

Continue by defining local paper order records and ledger behavior before adding fill application, session summaries, or artifacts.
