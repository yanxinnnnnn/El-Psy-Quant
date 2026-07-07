# Sprint 79 — Paper Order Ledger Foundation

## Objective

Define the minimum usable local paper order ledger boundary.

## Delivered Scope

Sprint 79 adds local paper order records and a deterministic paper order ledger
in `el_psy_quant.paper`.

The new public API includes:

- `PaperOrderRecord`
- `PaperOrderLedger`
- `create_paper_order_record(...)`
- `create_paper_order_ledger(...)`

## Paper Order Records

A paper order record captures local order state only:

- order ID
- timestamp
- normalized symbol
- side
- quantity
- status

Supported sides:

- `buy`
- `sell`

Supported statuses:

- `submitted`
- `accepted`
- `rejected`
- `filled`

The record is immutable after creation and exports JSON-compatible plain data.

## Paper Order Ledger

The paper order ledger stores immutable paper order records in caller-provided
order.

The ledger validates that order IDs are unique and exports deterministic
JSON-compatible data.

## Out of Scope

- Fill application.
- Applying orders to `PaperAccountState`.
- Cash or position mutation.
- Paper trading session summaries.
- Paper trading artifacts.
- Broker integration, exchange APIs, live trading, order routing, or market data streaming.
- Execution scheduling, order matching, partial fills, or slippage/commission changes.
- Configured-run, YAML, CLI, database, dashboard, or plugin behavior.
