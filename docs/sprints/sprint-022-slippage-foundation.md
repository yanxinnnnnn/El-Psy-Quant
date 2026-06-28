# Sprint 22 — Slippage Foundation

## Objective

Add a small explicit slippage model to the moving-average crossover research workflow.

Sprint 21 added transaction costs when positions change. Sprint 22 should add the next realism layer: simple slippage drag when positions change.

This sprint should not build order execution simulation, bid/ask spread modeling, order book simulation, broker behavior, trade records, or a full accounting engine.

## Product Goal

As the founder, I want backtest returns to optionally include a simple slippage drag when positions change, so research results do not assume every position change happens at a perfect theoretical price.

The target behavior is:

```text
position changes
  -> transaction cost series
  -> slippage series
  -> gross strategy return - transaction cost - slippage
  -> net strategy return
  -> cost/slippage-adjusted equity curve
```

## Technical Direction

Add a small slippage helper under the portfolio package and wire it into existing research flows:

```text
src/
└── el_psy_quant/
    ├── portfolio/
    │   ├── __init__.py
    │   ├── costs.py
    │   ├── equity.py
    │   ├── positions.py
    │   ├── returns.py
    │   └── slippage.py
    └── backtesting/
        ├── experiments.py
        ├── pipelines.py
        └── workflows.py

tests/
├── test_portfolio_slippage.py
├── test_backtesting_pipelines.py
├── test_backtesting_workflows.py
└── test_backtesting_experiments.py
```

Keep this simple and explicit.

## Implementation Scope

### 1. Add Slippage Helper

Implement:

```python
def slippage_cost(position: pd.Series, slippage_rate: float) -> pd.Series:
    ...
```

The function should:

- Accept a long-only position series containing only `0` and `1`.
- Accept `slippage_rate` as a non-negative decimal return drag per unit of turnover.
- Reject negative `slippage_rate` with `ValueError`.
- Reject NaN position values with `ValueError`.
- Reject position values other than `0` or `1` with `ValueError`.
- Return a float `pd.Series` with the same index as `position`.

Slippage formula:

```python
turnover = position.astype(float).diff().abs()
turnover.iloc[0] = abs(position.iloc[0])
slippage = turnover * slippage_rate
```

Meaning:

- `0 -> 1` creates turnover `1` and charges one slippage unit.
- `1 -> 0` creates turnover `1` and charges one slippage unit.
- `0 -> 0` creates turnover `0`.
- `1 -> 1` creates turnover `0`.
- If the first row starts already long, the first row charges slippage.

Export the function from:

```python
el_psy_quant.portfolio
```

### 2. Wire Slippage Into Pipeline

Update:

```python
def moving_average_crossover_pipeline(
    close: pd.Series,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> pd.DataFrame:
    ...
```

The function should:

- Preserve existing behavior when `transaction_cost_rate=0.0` and `slippage_rate=0.0`.
- Calculate gross strategy return using existing `strategy_return`.
- Calculate transaction costs using `transaction_cost(position, transaction_cost_rate)`.
- Calculate slippage using `slippage_cost(position, slippage_rate)`.
- Calculate:

```python
net_strategy_return = gross_strategy_return - transaction_cost - slippage
```

- Calculate equity using `net_strategy_return`.
- Return the existing output columns plus:

```text
slippage
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
slippage
net_strategy_return
equity
```

Where:

- `strategy_return` means gross strategy return before transaction costs and slippage.
- `transaction_cost` means per-period transaction cost drag.
- `slippage` means per-period slippage drag.
- `net_strategy_return` means return after transaction costs and slippage.
- `equity` is based on `net_strategy_return`.

### 3. Pass Slippage Rate Through Existing Workflows

Update:

```python
def moving_average_crossover_from_csv(
    path: str | Path,
    fast_window: int,
    slow_window: int,
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
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
    slippage_rate: float = 0.0,
) -> pd.DataFrame:
    ...
```

Both functions should pass `slippage_rate` into `moving_average_crossover_pipeline`.

Do not add slippage-specific columns to the parameter sweep summary table in this sprint. The summary already uses the pipeline equity curve, so final equity and total return should naturally reflect slippage.

## Tests

Add or update tests covering:

### Portfolio Slippage Tests

- `slippage_cost` returns zero slippage for constant flat position.
- It charges on `0 -> 1`.
- It charges on `1 -> 0`.
- It charges on the first row if the first position is already `1`.
- It preserves the input index.
- Zero `slippage_rate` returns all zeros.
- Negative `slippage_rate` raises `ValueError`.
- NaN positions raise `ValueError`.
- Invalid position values raise `ValueError`.
- Function is exported from `el_psy_quant.portfolio`.

### Pipeline Tests

- Default `slippage_rate=0.0` produces zero `slippage`.
- Result includes the `slippage` column in stable order.
- With positive `slippage_rate`, `net_strategy_return == strategy_return - transaction_cost - slippage`.
- Equity is calculated from `net_strategy_return`.
- Negative `slippage_rate` propagates `ValueError`.
- Existing transaction cost behavior remains valid.

### Workflow / Experiment Tests

- `moving_average_crossover_from_csv` accepts `slippage_rate` and returns slippage-adjusted results.
- `moving_average_crossover_parameter_sweep` accepts `slippage_rate` and produces summaries based on slippage-adjusted equity.
- Existing behavior remains valid when slippage rate is omitted.

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
    slippage_rate=0.0005,
)
```

Briefly state:

- Transaction costs and slippage are charged when position changes.
- `strategy_return` is gross return.
- `net_strategy_return` is after transaction costs and slippage.
- `equity` is based on `net_strategy_return`.

Keep it short. Do not turn README into a market microstructure textbook.

## Out of Scope

- No trade records.
- No broker-specific fee schedules.
- No minimum commissions.
- No tax model.
- No bid/ask spread model.
- No order execution simulation.
- No order book simulation.
- No volume/ADV-aware slippage.
- No nonlinear market impact model.
- No position sizing beyond 0/1 long-only state.
- No short selling.
- No leverage.
- No multi-asset slippage.
- No benchmark comparison.
- No CLI.
- No charts.
- No dashboards.
- No file export.
- No live download changes.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.portfolio import slippage_cost"` works.
- `uv run python -c "from el_psy_quant.backtesting import moving_average_crossover_pipeline"` works.
- README documents the slippage option briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 22 scope.
3. Do not introduce trade records, broker-specific fee schedules, minimum commissions, tax models, bid/ask spread models, order execution simulation, order book simulation, volume-aware slippage, market impact models, position sizing, short selling, leverage, multi-asset slippage, benchmark comparison, CLI commands, charts, dashboards, file exports, live download changes, cloud features, or broker integration.
4. Keep slippage logic explicit and easy to inspect.
5. Keep tests deterministic and network-free.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether slippage timing is explicit and intuitive.
- Whether gross return, transaction cost, slippage, net return, and equity are clearly separated.
- Whether existing no-cost/no-slippage behavior remains stable.
- Whether Codex avoided building a full execution/accounting system.
