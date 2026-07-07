# Sprint 78 — Paper Account State Foundation

## Objective

Define the minimum usable local paper account state boundary.

## Delivered Scope

Sprint 78 adds `el_psy_quant.paper` with:

- `PaperAccountState`
- `create_paper_account_state(...)`

The state records:

- starting cash
- current cash
- positions
- timestamp

It exports deterministic, JSON-compatible plain data through `to_dict()`.

## Deterministic State

The paper account state is immutable after creation. Inputs are validated and
copied into internal normalized values so caller-provided mappings are not
mutated.

Positions are exported in stable normalized-symbol order.

Timestamps are validated through `pandas.Timestamp` and exported as ISO strings.

## Cash And Positions

Cash values must be finite, numeric, and non-negative.

Position symbols are normalized through the existing local symbol boundary.
Position quantities must be finite numeric values. Positive, zero, and negative
quantities are allowed because the state boundary only records state; it does
not apply fills or enforce trading rules yet.

## Optional Explicit-Price Equity Snapshot

`PaperAccountState.to_dict(prices=...)` can include a small equity snapshot when
prices are supplied explicitly by the caller.

This snapshot:

- uses only caller-provided prices
- does not fetch market data
- does not integrate with market data providers
- requires finite non-negative prices
- requires a price for every position symbol

## Out of Scope

- Paper order ledgers.
- Fill application.
- Paper trading session summaries.
- Paper trading artifacts.
- Broker integration or real account sync.
- Exchange APIs, order routing, market data streaming, paper/live trading.
- Configured-run, YAML, CLI, database, dashboard, or plugin changes.
