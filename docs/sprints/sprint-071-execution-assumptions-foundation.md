# Sprint 71 — Execution Assumptions Foundation

## Objective

Define the smallest useful execution-assumption boundary for local deterministic backtests.

## Planned Scope

Sprint 71 should introduce documented execution assumptions before order intent or fill models are added.

The expected boundary should make these choices explicit:

- execution timing assumption
- fill price source assumption
- same-bar or next-bar behavior
- invalid or missing fill price handling
- JSON-compatible assumption representation where scoped

## Out of Scope

- Broker, exchange, paper-trading, or live-trading integration.
- Order routing or market data streaming.
- Fill model implementation beyond the scoped assumption boundary.
- YAML, CLI, manifest, or configured-run schema changes unless explicitly scoped.

## Acceptance Criteria

To be defined in the Sprint 71 issue.