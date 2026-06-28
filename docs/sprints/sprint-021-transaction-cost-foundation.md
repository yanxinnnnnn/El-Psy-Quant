# Sprint 21 — Transaction Cost Foundation

## Objective

Add a small explicit transaction cost model to the moving-average crossover research workflow.

Milestone 4 made experiments repeatable and comparable. Milestone 5 should start making the backtest less toy-like. Sprint 21 adds the first realism layer: a simple cost drag whenever the strategy changes position.

This sprint should not build broker-specific fee schedules, slippage, order execution, trade records, or a full accounting engine.

## Product Goal

As the founder, I want backtest returns to optionally include a simple transaction cost when positions change, so parameter experiments are not evaluated in a frictionless fantasy world.

The target behavior is:

```text
position changes
  -> transaction cost series
  -> gross strategy return - transaction cost
  -> net strategy return
  -> cost-adjusted equity curve
```

## Technical Direction

Add a small cost helper under the portfolio package and wire it into existing research flows:

```text
src/
└── el_psy_quant/
    ├── portfolio/
    │   ├── __init__.py
    │   ├── costs.py
    │   ├── equity.py
    │   ├── positions.py
    │   └── returns.py
    └── backtesting/
        ├── experiments.py
        ├── pipelines.py
        └── workflows.py

tests/
├── test_portfolio_costs.py
├── test_backtesting_pipelines.py
├── test_backtesting_workflows.py
└── test_backtesting_experiments.py
```

Keep this simple and explicit.

## Implementation Scope

### 1. Add Transaction Cost Helper

Implement:

```python
def transaction_cost(position: pd.Series, cost_rate: float) -> pd.Series:
    ...
```

The function should:

- Accept a long-only position series containing only `0` and `1`.
- Accept `cost_rate` as a non-negative decimal return drag per unit of turnover.
- Reject negative `cost_rate` with `ValueError`.
- Reject NaN position values with `ValueError`.
- Reject position values other than `0` or `1` with `ValueError`.
- Return a float `pd.Series` with the same index as `position`.

Cost formula:

```python
turnover = position.astype(float).diff().abs()
turnover.iloc[0] = abs(position.iloc[0])
cost = turnover * cost_rate
```

Meaning:

- `0 -> 1` creates turnover `1` and charges one cost unit.
- `1 -> 0` creates turnover `1` and charges one cost unit.
- `0 -> 0` creates turnover `0`.
- `1 -> 1` creates turnover `0`.
- If the first row starts already long, the first row charges a cost.

Export the function from:

```python
el_psy_quant.portfolio
```

### 2. Wire Costs Into Pipeline

Update:

```python
def moving_average_crossover_pipeline(
    close: pd.Series,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
) -> pd.DataFrame:
    ...
```

The function should:

- Preserve existing behavior when `transaction_cost_rate=0.0`.
- Calculate gross strategy return using existing `strategy_return`.
- Calculate transaction costs using `transaction_cost(position, transaction_cost_rate)`.
- Calculate:

```python
net_strategy_return = gross_strategy_return - transaction_cost
```

- Calculate equity using `net_strategy_return`.
- Return the existing output columns plus:

```text
transaction_cost
net_strategy_return
```

Expected result columns:

```text
close
fast_sma
slow_sma
signal
position
asset_return
strategy_return
transaction_cost
net_strategy_return
equity
```

Where:

- `strategy_return` means gross strategy return before transaction costs.
- `transaction_cost` means the per-period cost drag.
- `net_strategy_return` means return after transaction costs.
- `equity` is based on `net_strategy_return`.

### 3. Pass Cost Rate Through Existing Workflows

Update:

```python
def moving_average_crossover_from_csv(
    path: str | Path,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    ...
```

Update:

```python
def moving_average_crossover_parameter_sweep(
    path: str | Path,
    fast_windows: Iterable[int],
    slow_windows: Iterable[int],
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
) -> pd.DataFrame:
    ...
```

Both functions should pass `transaction_cost_rate` into `moving_average_crossover_pipeline`.

Do not add transaction-cost-specific columns to the parameter sweep summary table in this sprint. The summary already uses the pipeline equity curve, so final equity and total return should naturally reflect costs.

## Tests

Add or update tests covering:

### Portfolio Cost Tests

- `transaction_cost` returns zero cost for constant flat position.
- It charges on `0 -> 1`.
- It charges on `1 -> 0`.
- It charges on the first row if the first position is already `1`.
- It preserves the input index.
- Zero `cost_rate` returns all zeros.
- Negative `cost_rate` raises `ValueError`.
- NaN positions raise `ValueError`.
- Invalid position values raise `ValueError`.
- Function is exported from `el_psy_quant.portfolio`.

### Pipeline Tests

- Default `transaction_cost_rate=0.0` produces zero `transaction_cost`.
- Result includes `transaction_cost` and `net_strategy_return` columns.
- With positive `transaction_cost_rate`, `net_strategy_return == strategy_return - transaction_cost`.
- Equity is calculated from `net_strategy_return`.
- Negative `transaction_cost_rate` propagates `ValueError`.

### Workflow / Experiment Tests

- `moving_average_crossover_from_csv` accepts `transaction_cost_rate` and returns cost-adjusted results.
- `moving_average_crossover_parameter_sweep` accepts `transaction_cost_rate` and produces summaries based on cost-adjusted equity.
- Existing behavior remains valid when cost rate is omitted.

Use deterministic in-memory series and temporary CSV files. No live network calls.

## README Update

Add a short example showing:

```python
result = moving_average_crossover_pipeline(
    close,
    fast_window=20,
    slow_window=50,
    initial_capital=1_000.0,
    transaction_cost_rate=0.001,
)
```

Briefly state:

- Transaction costs are charged when position changes.
- `strategy_return` is gross return.
- `net_strategy_return` is after costs.
- `equity` is based on `net_strategy_return`.

Keep it short. Do not turn README into a finance textbook.

## Out of Scope

- No slippage.
- No trade records.
- No broker-specific fee schedules.
- No minimum commissions.
- No tax model.
- No bid/ask spread model.
- No order execution simulation.
- No order book simulation.
- No position sizing beyond 0/1 long-only state.
- No short selling.
- No leverage.
- No multi-asset costs.
- No benchmark comparison.
- No CLI.
- No charts.
- No dashboards.
- No file export.
- No live download changes.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import transaction_cost"` works.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_pipeline"` works.
- README documents the transaction cost option briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 21 scope.
3. Do not introduce slippage, trade records, broker-specific fee schedules, minimum commissions, tax models, bid/ask spread models, order execution simulation, order book simulation, position sizing, short selling, leverage, multi-asset costs, benchmark comparison, CLI commands, charts, dashboards, file exports, live download changes, cloud features, or broker integration.
4. Keep transaction cost logic explicit and easy to inspect.
5. Keep tests deterministic and network-free.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether transaction cost timing is explicit and intuitive.
- Whether gross return, cost, net return, and equity are clearly separated.
- Whether existing no-cost behavior remains stable.
- Whether Codex avoided building a full execution/accounting system.
