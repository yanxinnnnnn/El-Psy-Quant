# Sprint 65 — Portfolio Risk Metrics Foundation

## Objective

Add a small risk summary for an existing portfolio return series.

## Product Goal

Portfolio-level returns should expose their basic distribution and loss
frequency before the project adds drawdown inspection or attribution.

## Implementation Scope

- Validate non-empty numeric portfolio return Series with a DatetimeIndex.
- Report periods, arithmetic mean, min/max, and loss-frequency counts.
- Report sample volatility using pandas `Series.std(ddof=1)` for two or more
  observations; define one-observation volatility as `0.0` so every non-empty
  summary remains JSON-compatible.
- Optionally report existing annualized volatility with an explicit frequency.
- Return deterministic plain Python numbers without mutating input.

## Risk Scope

These metrics describe the portfolio return series itself. They do not inspect
drawdown windows, calculate symbol contributions, or attribute factors.

## Out of Scope

- Drawdown duration, recovery, underwater curves, or drawdown tables.
- Contribution, attribution artifacts, covariance, VaR, or stress testing.
- Optimization, rebalancing, configured-run, CLI, or execution integration.

## Acceptance Criteria

- Required distribution, count, volatility, and loss-rate metrics are present.
- Annualized volatility appears only with `periods_per_year`.
- Invalid or incomplete Series inputs fail clearly.
- Results are JSON-compatible and inputs are unchanged.
