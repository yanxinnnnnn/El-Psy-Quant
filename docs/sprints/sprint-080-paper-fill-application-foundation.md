# Sprint 80 — Paper Fill Application Foundation

## Objective

Define the minimum usable local paper fill application boundary.

## Delivered Scope

Sprint 80 adds explicit paper fills and a helper for applying them to local
paper account state:

- `PaperFill`
- `create_paper_fill(...)`
- `apply_paper_fills(...)`

The helper accepts an existing `PaperAccountState` plus a non-empty sequence of
explicit `PaperFill` inputs and returns a new `PaperAccountState`.

## Fill Semantics

Fill application is intentionally small and deterministic:

- buy fills decrease cash by `quantity * price`
- buy fills increase the symbol position by `quantity`
- sell fills increase cash by `quantity * price`
- sell fills decrease the symbol position by `quantity`
- multiple fills are applied in caller-provided order
- the output account timestamp is the last explicit fill timestamp

## Critical Boundary

Sprint 80 is driven only by explicit fill inputs.

It does not infer fill behavior from `PaperOrderRecord.status`. A paper order
record with status `filled` is still only a static local order record unless an
explicit paper fill is supplied to the fill application helper.

## Determinism And Mutation

The source account state is not mutated.

Caller-provided fill sequences and fill objects are not mutated.

The returned account state uses the existing deterministic paper account export
boundary.

## Out of Scope

- Paper trading session summaries.
- Paper trading artifacts.
- Broker integration, exchange APIs, live trading, order routing, or market data streaming.
- Real account sync, order matching, execution scheduling, or partial-fill lifecycle management.
- Commission, slippage, portfolio, risk, or analytics expansion.
- Configured-run, YAML, CLI, database, dashboard, or plugin behavior.
