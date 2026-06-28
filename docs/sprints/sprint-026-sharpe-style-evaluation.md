# Sprint 26 — Sharpe-Style Evaluation

## Objective

Add a simple Sharpe-style performance metric with explicit annualization and risk-free-rate assumptions.

Sprint 25 added CAGR and annualized volatility. Sprint 26 should add a risk-adjusted return metric that uses those foundations without expanding into a full analytics framework.

This sprint should not add Sortino ratio, Calmar ratio, benchmark comparison, rolling metrics, charts, dashboards, or portfolio analytics.

## Product Goal

As the founder, I want to evaluate strategy results with a simple Sharpe-style ratio, so I can compare return against volatility instead of looking at return alone.

The target behavior is:

```text
return series + periods_per_year + annual_risk_free_rate
  -> annualized excess return
  -> annualized volatility
  -> Sharpe-style ratio
```

The frequency and risk-free-rate assumptions must be explicit.

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

Keep this as pure functions.

## Implementation Scope

### 1. Add Sharpe-Style Ratio

Implement:

```python
def sharpe_ratio(
    returns: pd.Series,
    periods_per_year: int | float,
    annual_risk_free_rate: float = 0.0,
) -> float:
    ...
```

The function should:

- Accept a return series as `pd.Series`.
- Accept `periods_per_year` as an explicit positive number.
- Accept `annual_risk_free_rate` as a decimal annual rate.
- Reject empty returns with `ValueError`.
- Reject NaN returns with `ValueError`.
- Reject `periods_per_year <= 0` with `ValueError`.
- Require at least two return observations.
- Use sample standard deviation for volatility.
- Reject zero annualized volatility with `ValueError`.
- Return a decimal ratio.

Formula:

```python
periodic_risk_free_rate = (1 + annual_risk_free_rate) ** (1 / periods_per_year) - 1
excess_returns = returns - periodic_risk_free_rate
annualized_excess_return = excess_returns.mean() * periods_per_year
annualized_vol = annualized_volatility(returns, periods_per_year)
sharpe = annualized_excess_return / annualized_vol
```

Notes:

- Use arithmetic mean excess return for this simple Sharpe-style metric.
- Use the existing `annualized_volatility` helper.
- Keep the risk-free-rate conversion explicit and documented in tests.
- `annual_risk_free_rate=0.0` should be the default.

### 2. Export Metric

Export `sharpe_ratio` from:

```python
el_psy_quant.performance
```

### 3. Optional Summary Extension

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
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    ...
```

Behavior:

- Preserve the existing output when `periods_per_year is None`.
- When `periods_per_year` is provided, continue adding:
  - `cagr`
  - `annualized_volatility`
- Also add:
  - `sharpe_ratio`
- Use `result["equity"]` for CAGR.
- Prefer `result["net_strategy_return"]` for volatility and Sharpe when present.
- Fall back to `result["strategy_return"]` when `net_strategy_return` is not present.
- Do not make `periods_per_year` mandatory.
- Do not change existing summary keys or break existing tests.

## Tests

Add or update tests covering:

### Sharpe Ratio Tests

- Calculates expected Sharpe ratio when `annual_risk_free_rate=0.0`.
- Calculates expected Sharpe ratio when `annual_risk_free_rate` is positive.
- Converts annual risk-free rate to periodic risk-free rate using:

```python
(1 + annual_risk_free_rate) ** (1 / periods_per_year) - 1
```

- Uses sample standard deviation through `annualized_volatility`.
- Rejects empty returns.
- Rejects NaN returns.
- Rejects non-positive `periods_per_year`.
- Rejects fewer than two return observations.
- Rejects zero annualized volatility.
- Function is exported from `el_psy_quant.performance`.

### Summary Tests, If Summary Is Extended

- Existing `backtest_summary(result)` output remains unchanged.
- `backtest_summary(result, periods_per_year=...)` includes `sharpe_ratio`.
- Summary uses `net_strategy_return` for Sharpe when available.
- Summary falls back to `strategy_return` when `net_strategy_return` is absent.
- `annual_risk_free_rate` affects summary Sharpe.
- Invalid `periods_per_year` propagates `ValueError`.
- Zero volatility propagates `ValueError` only when annualized metrics are requested.

Use deterministic in-memory series/DataFrames. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.performance import sharpe_ratio

sharpe = sharpe_ratio(
    result["net_strategy_return"],
    periods_per_year=252,
    annual_risk_free_rate=0.02,
)
```

Briefly state:

- Sharpe compares excess return against volatility.
- `periods_per_year` and `annual_risk_free_rate` must be explicit assumptions.
- Higher is generally better, but Sharpe is not proof of strategy quality.

Keep it short. Do not turn README into a risk textbook.

## Out of Scope

- No Sortino ratio.
- No Calmar ratio.
- No information ratio.
- No benchmark comparison.
- No rolling Sharpe.
- No monthly/yearly breakdown.
- No drawdown duration.
- No VaR/CVaR.
- No statistical significance tests.
- No charts.
- No dashboards.
- No CLI.
- No file export.
- No live download changes.
- No pipeline changes.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.performance import sharpe_ratio"` works.
- README documents the Sharpe-style metric briefly.
- Existing summary behavior remains backward compatible.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 26 scope.
3. Do not introduce Sortino ratio, Calmar ratio, information ratio, benchmark comparison, rolling Sharpe, monthly/yearly breakdown, drawdown duration, VaR/CVaR, statistical significance tests, charts, dashboards, CLI commands, file exports, live download changes, cloud features, or broker integration.
4. Keep frequency and risk-free-rate assumptions explicit.
5. Reuse `annualized_volatility`.
6. Preserve backward compatibility for `backtest_summary(result)`.
7. Keep tests deterministic and network-free.
8. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether risk-free-rate conversion is explicit.
- Whether Sharpe uses annualized excess return divided by annualized volatility.
- Whether zero volatility is rejected clearly.
- Whether summary behavior remains backward compatible.
- Whether Codex avoided jumping ahead to benchmark or other risk metrics.
