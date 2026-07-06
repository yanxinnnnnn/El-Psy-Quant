# Sprint 47 — Milestone 11 Planning

## Objective

Plan Milestone 11 — Strategy Interface Foundation.

## Status

Complete.

## Why This Milestone Comes Now

Milestone 10 made configured experiment runs easier to inspect and compare through local artifacts:

```text
manifest.json -> results/metrics.json -> comparison DataFrame
```

The next bottleneck is not another metric or another report. The next bottleneck is strategy structure.

Today the project has one real strategy path: moving-average crossover. The strategy is useful as a test vehicle, but the workflow is still tightly coupled to that specific implementation. Before adding more strategies, the project needs a small contract that says what a strategy is, how it runs, and what output shape it must produce.

## Milestone Product Goal

Milestone 11 should make strategies explicit, testable, and replaceable while preserving the artifact discipline built in Milestone 10.

A future reviewer should be able to ask:

- which strategy implementation was selected
- which parameters it received
- whether it returned the expected pipeline output shape
- whether configured experiments can run through the strategy boundary
- whether artifacts still record enough information to inspect the run later

## Milestone 11 — Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S47 | Complete | Plan Milestone 11. | Strategy interface milestone scope and sprint sequence. | No implementation during planning. |
| S48 | Planned | Define strategy contract. | Minimal strategy interface / protocol and tests. | No new strategy. |
| S49 | Planned | Wrap existing crossover logic. | Moving-average crossover strategy implementation behind the interface. | Preserve current behavior. |
| S50 | Planned | Add strategy resolver. | Small resolver for supported strategy names. | No plugin framework. |
| S51 | Planned | Wire configured experiments through strategy boundary. | Configured run path uses resolver/interface while preserving artifacts. | No broad CLI redesign. |
| S52 | Planned | Close milestone. | Milestone 11 documentation refresh. | No scope expansion. |

## Recommended Shape

The strategy interface should stay boring.

A minimal implementation could include:

- a strategy name
- a run method that accepts local price data and parameter values
- a deterministic pandas DataFrame output compatible with existing summary logic

The exact API can be decided during Sprint 48, but it must not become a large strategy framework.

## Non-Goals

Milestone 11 should not add:

- many strategies
- strategy optimization
- ranking or best-run selection
- alpha discovery claims
- portfolio construction
- live trading
- paper trading
- database-backed strategy metadata
- dashboard-driven strategy selection
- a plugin marketplace or dynamic loading framework

## Design Discipline

The key rule is:

```text
Define the seam before adding more things behind the seam.
```

The project should make the existing moving-average crossover strategy use a clear boundary first. Only after that boundary is stable should the project add more strategy families.

## First Implementation Sprint

The next sprint should be:

```text
Sprint 48 — Strategy Interface Contract Foundation
```

Sprint 48 should add the smallest useful strategy contract and tests for that contract.

It should not wire the CLI yet unless the implementation proves that wiring is necessary. The first step is the boundary, not the migration.

## Validation

No tests were run for this sprint because it is documentation and planning only.
