# Sprint 25 — Annualized Metrics Foundation

## Objective

Add annualized performance metrics with explicit period assumptions.

Milestone 5 made the backtest less fake by adding transaction costs, slippage, and trade records. Milestone 6 should improve evaluation discipline. Sprint 25 adds two foundational risk/performance metrics:

- CAGR
- annualized volatility

This sprint should not add Sharpe ratio, benchmark comparison, rolling metrics, charts, dashboards, or a generic analytics framework.

## Product Goal

As the founder, I want to evaluate strategy results with annualized return and annualized volatility, so I can compare results across different backtest lengths more responsibly.

The target behavior is:

```text
equity curve + periods_per_year
  -> CAGR

return series + periods_per_year
  -> annualized volatility
```

The frequency assumption must be explicit. Do not hide `252` inside the implementation without exposing it as an argument.

## Technical Direction

Extend the existing performance package:

```text
src/
└── el_psy_quant/
    └── performance/
        ├── __init__.py
        ├── metrics.py
        └── summary.py

tests/
├── test_performance_metrics.py
└── test_performance_summary.py
```

Keep these as pure functions.

## Implementation Scope

### 1. Add CAGR

Implement:

```python
def cagr(equity: pd.Series, periods_per_year: int | float) -> float:
    ...
```

The function should:

- Accept an equity curve as `pd.Series`.
- Accept `periods_per_year` as an explicit positive number.
- Reuse existing equity validation where reasonable.
- Reject empty equity with `ValueError`.
- Reject NaN equity with `ValueError`.
- Reject non-positive equity values with `ValueError`.
- Reject `periods_per_year <= 0` with `ValueError`.
- Require at least two equity points.
- Return CAGR as a decimal return.

Formula:

```python
years = (len(equity) - 1) / periods_per_year
cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
```

Example:

```text
100 -> 121 over 2 years = 10% CAGR
```

Use `len(equity) - 1` for elapsed periods. This avoids treating the starting point as a full return period.

### 2. Add Annualized Volatility

Implement:

```python
def annualized_volatility(returns: pd.Series, periods_per_year: int | float) -> float:
    ...
```

The function should:

- Accept a return series as `pd.Series`.
- Accept `periods_per_year` as an explicit positive number.
- Reject empty returns with `ValueError`.
- Reject NaN returns with `ValueError`.
- Reject `periods_per_year <= 0` with `ValueError`.
- Require at least two return observations.
- Return annualized volatility as a decimal.

Formula:

```python
returns.std(ddof=1) * periods_per_year ** 0.5
```

Use sample standard deviation with `ddof=1`.

### 3. Export Metrics

Export both functions from:

```python
el_psy_quant.performance
```

### 4. Optional Summary Extension

Update:

```python
def backtest_summary(...)
```

only if it can be done cleanly without breaking existing callers.

Preferred shape:

```python
def backtest_summary(
    result: pd.DataFrame,
    periods_per_year: int | float | None = None,
) -> dict[str, float]:
    ...
```

Behavior:

- Preserve the existing output when `periods_per_year is None`.
- When `periods_per_year` is provided, add:
  - `cagr`
  - `annualized_volatility`
- Use `result["equity"]` for CAGR.
- Prefer `result["net_strategy_return"]` for annualized volatility when present.
- Fall back to `result["strategy_return"]` when `net_strategy_return` is not present.

Do not make `periods_per_year` mandatory.

Do not change existing summary keys or break existing tests.

## Tests

Add or update tests covering:

### CAGR Tests

- Calculates expected CAGR for a simple two-year example.
- Uses `len(equity) - 1` as elapsed periods.
- Rejects empty equity.
- Rejects NaN equity.
- Rejects non-positive equity values.
- Rejects non-positive `periods_per_year`.
- Rejects fewer than two equity points.
- Function is exported from `el_psy_quant.performance`.

### Annualized Volatility Tests

- Calculates expected annualized volatility using sample standard deviation.
- Rejects empty returns.
- Rejects NaN returns.
- Rejects non-positive `periods_per_year`.
- Rejects fewer than two return observations.
- Function is exported from `el_psy_quant.performance`.

### Summary Tests, If Summary Is Extended

- Existing `backtest_summary(result)` output remains unchanged.
- `backtest_summary(result, periods_per_year=...)` includes `cagr` and `annualized_volatility`.
- Summary uses `net_strategy_return` for annualized volatility when available.
- Summary falls back to `strategy_return` when `net_strategy_return` is absent.
- Invalid `periods_per_year` propagates `ValueError`.

Use deterministic in-memory series/DataFrames. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.performance import annualized_volatility, cagr

annual_return = cagr(result["equity"], periods_per_year=252)
annual_vol = annualized_volatility(
    result["net_strategy_return"],
    periods_per_year=252,
)
```

Briefly state:

- `periods_per_year` must be supplied explicitly.
- For daily trading data, `252` is a common assumption but not universal.

Keep it short. Do not turn README into a risk textbook.

## Out of Scope

- No Sharpe ratio.
- No Sortino ratio.
- No Calmar ratio.
- No benchmark comparison.
- No rolling metrics.
- No monthly/yearly breakdown.
- No drawdown duration.
- No VaR/CVaR.
- No statistical significance tests.
- No charts.
- No dashboards.
- No CLI.
- No file export.
- No live download changes.
- No pipeline changes unless strictly needed for summary compatibility.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.performance import cagr, annualized_volatility"` works.
- README documents the annualized metrics briefly.
- Existing summary behavior remains backward compatible.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 25 scope.
3. Do not introduce Sharpe ratio, Sortino ratio, Calmar ratio, benchmark comparison, rolling metrics, monthly/yearly breakdown, drawdown duration, VaR/CVaR, statistical significance tests, charts, dashboards, CLI commands, file exports, live download changes, cloud features, or broker integration.
4. Keep frequency assumptions explicit through `periods_per_year`.
5. Preserve backward compatibility for `backtest_summary(result)`.
6. Keep tests deterministic and network-free.
7. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether annualization assumptions are explicit.
- Whether CAGR uses elapsed periods correctly.
- Whether volatility uses sample standard deviation.
- Whether summary behavior remains backward compatible.
- Whether Codex avoided jumping ahead to Sharpe or benchmark work.
