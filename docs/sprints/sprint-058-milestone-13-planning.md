# Sprint 58 — Milestone 13 Planning

## Objective

Plan Milestone 13 — Portfolio Construction Foundation.

## Product Goal

Define how the project should move from independent per-symbol research results toward portfolio-level construction without rushing into risk attribution, execution realism, optimization, dashboards, or live trading.

## Planning Outcome

Milestone 13 should introduce portfolio construction through a conservative chain:

```text
aligned portfolio inputs -> equal-weight portfolio returns -> configurable weights -> portfolio summary artifact
```

The project already has validated configured symbols and local price inputs. The next risk is combining symbol results without explicit assumptions about dates, weights, capital, and aggregation.

## Planned Sprint Sequence

| Sprint | Goal | Guardrail |
|---:|---|---|
| S58 | Plan Milestone 13. | Documentation-only. |
| S59 | Add portfolio input alignment foundation. | No allocation logic yet. |
| S60 | Add equal-weight portfolio return foundation. | Keep assumptions simple and explicit. |
| S61 | Add configurable portfolio weights foundation. | No optimization engine. |
| S62 | Add portfolio summary artifact foundation. | Preserve configured-run artifact discipline. |
| S63 | Close Milestone 13. | Documentation refresh only. |

## Out of Scope

Sprint 58 does not implement portfolio behavior.

It deliberately avoids:

- product code changes
- date alignment implementation
- allocation logic
- rebalancing logic
- cash modeling
- portfolio transaction-cost changes
- portfolio risk attribution
- benchmark portfolio logic
- optimization or parameter search
- strategy changes
- resolver changes
- configured-run behavior changes
- artifact schema changes
- CLI changes
- database or dashboard work
- live or paper trading
- plugin or dynamic loading systems

## Acceptance Criteria

- Sprint 58 documentation exists.
- Milestone 13 planning documentation exists.
- Milestone 13 scope and sprint sequence are clear.
- Portfolio construction is distinguished from independent multi-symbol summaries.
- Roadmap points to Sprint 59.
- README points to Sprint 59.
- AGENTS current focus is updated without changing high-level mission text.
- No product behavior changes are introduced.
