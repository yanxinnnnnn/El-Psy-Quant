# Sprint 23 — Trade Record Foundation

## Objective

Add a basic trade record extraction helper for the moving-average crossover research workflow.

Sprint 21 added transaction costs. Sprint 22 added slippage. Sprint 23 should make the strategy's actual position changes easier to inspect by producing a simple trade record table.

This sprint is about visibility, not accounting. Do not build PnL attribution, broker statements, order execution simulation, or a full trade lifecycle engine.

## Product Goal

As the founder, I want to extract basic buy/sell records from a pipeline result, so I can inspect when the strategy entered or exited a position and what the close price was at that point.

The target behavior is:

```text
pipeline result
  -> position changes
  -> basic trade record table
```

## Technical Direction

Add a small trade helper under the portfolio package and a convenience wrapper under the backtesting package:

```text
src/
└── el_psy_quant/
    ├── portfolio/
    │   ├── __init__.py
    │   ├── costs.py
    │   ├── equity.py
    │   ├── positions.py
    │   ├── returns.py
    │   ├── slippage.py
    │   └── trades.py
    └── backtesting/
        ├── __init__.py
        ├── experiments.py
        ├── pipelines.py
        ├── trades.py
        └── workflows.py

tests/
├── test_portfolio_trades.py
└── test_backtesting_trades.py
```

Keep this simple and explicit.

## Implementation Scope

### 1. Add Portfolio Trade Record Helper

Implement:

```python
def long_only_trade_records(position: pd.Series, close: pd.Series) -> pd.DataFrame:
    ...
```

The function should:

- Accept a long-only position series containing only `0` and `1`.
- Accept a close-price series.
- Require `position` and `close` indexes to be equal.
- Reject NaN position values with `ValueError`.
- Reject position values other than `0` or `1` with `ValueError`.
- Reject NaN close prices with `ValueError`.
- Return a `pd.DataFrame` with one row per position change.
- Preserve the original index values as the trade record index.

Position change logic:

```python
previous_position = position.shift(1, fill_value=0)
position_change = position - previous_position
```

Actions:

- `position_change == 1` means `BUY`.
- `position_change == -1` means `SELL`.
- `position_change == 0` means no trade row.

Required output columns:

```text
action
position_before
position_after
close
```

Column meanings:

- `action`: string, either `BUY` or `SELL`.
- `position_before`: previous position value, integer `0` or `1`.
- `position_after`: current position value, integer `0` or `1`.
- `close`: close price at the trade index.

If there are no trades, return an empty DataFrame with the required columns.

Export the function from:

```python
el_psy_quant.portfolio
```

### 2. Add Backtesting Trade Record Convenience Helper

Implement:

```python
def moving_average_crossover_trade_records(result: pd.DataFrame) -> pd.DataFrame:
    ...
```

The function should:

- Accept a DataFrame returned by `moving_average_crossover_pipeline`.
- Require the columns:
  - `position`
  - `close`
- Use `long_only_trade_records(result["position"], result["close"])`.
- If the pipeline result contains any of these columns, include them in the returned trade record table for the trade rows:
  - `transaction_cost`
  - `slippage`
  - `net_strategy_return`
  - `equity`
- Reject missing required columns with `ValueError`.
- Return a `pd.DataFrame` indexed by the trade dates / original index values.

Required base output columns:

```text
action
position_before
position_after
close
```

Optional extra columns, when present in the pipeline result:

```text
transaction_cost
slippage
net_strategy_return
equity
```

Export the function from:

```python
el_psy_quant.backtesting
```

## Example Usage

```python
from el_psy_quant.backtesting import (
    moving_average_crossover_pipeline,
    moving_average_crossover_trade_records,
)

result = moving_average_crossover_pipeline(
    close,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
    transaction_cost_rate=0.001,
    slippage_rate=0.0005,
)

trades = moving_average_crossover_trade_records(result)
print(trades)
```

## Tests

Add tests covering:

### Portfolio Trade Tests

- `long_only_trade_records` returns `BUY` on `0 -> 1`.
- It returns `SELL` on `1 -> 0`.
- It treats first-row `1` as a `BUY` from initial flat position.
- It returns no row for unchanged positions.
- It preserves the original trade indexes.
- It returns an empty DataFrame with stable columns when there are no trades.
- It rejects unequal indexes.
- It rejects NaN positions.
- It rejects invalid position values.
- It rejects NaN close prices.
- Function is exported from `el_psy_quant.portfolio`.

### Backtesting Trade Tests

- `moving_average_crossover_trade_records` accepts a real pipeline result.
- It returns the base trade record columns.
- It includes optional pipeline columns when present:
  - `transaction_cost`
  - `slippage`
  - `net_strategy_return`
  - `equity`
- It rejects missing `position` column.
- It rejects missing `close` column.
- Function is exported from `el_psy_quant.backtesting`.

Use deterministic in-memory series. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.backtesting import moving_average_crossover_trade_records

trades = moving_average_crossover_trade_records(result)
```

Briefly state:

- Trade records are extracted from position changes.
- They are for inspection, not broker-grade accounting.

Keep it short. Do not turn README into a trading ledger specification.

## Out of Scope

- No realized PnL per trade.
- No trade duration.
- No entry/exit pairing.
- No order IDs.
- No order lifecycle.
- No partial fills.
- No position sizing beyond 0/1 long-only state.
- No short selling.
- No leverage.
- No broker statements.
- No accounting ledger.
- No tax lots.
- No slippage model changes.
- No transaction cost model changes.
- No pipeline behavior changes beyond trade extraction helpers.
- No CLI.
- No charts.
- No dashboards.
- No file export.
- No live download changes.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import long_only_trade_records"` works.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_trade_records"` works.
- README documents the trade record helper briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 23 scope.
3. Do not introduce realized PnL per trade, trade duration, entry/exit pairing, order IDs, order lifecycle, partial fills, position sizing, short selling, leverage, broker statements, accounting ledgers, tax lots, slippage model changes, transaction cost model changes, CLI commands, charts, dashboards, file exports, live download changes, cloud features, or broker integration.
4. Keep trade extraction logic explicit and easy to inspect.
5. Keep tests deterministic and network-free.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether trade rows correspond clearly to position changes.
- Whether the output is inspectable and not over-engineered.
- Whether optional pipeline columns are attached only when present.
- Whether Codex avoided building a full trading ledger or accounting system.
