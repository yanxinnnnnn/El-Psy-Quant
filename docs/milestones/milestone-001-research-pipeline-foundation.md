# Milestone 1 — Research Pipeline Foundation

## Milestone Summary

Milestone 1 established the first working research pipeline for El-Psy-Quant.

The project started as an empty AI-native quantitative research idea and reached a point where it can now run a deterministic, single-asset moving-average crossover research flow from close prices to an equity curve.

This milestone is not about proving profitability. It is about building a clean, testable, and extensible foundation for future quantitative research.

## Product Thinking

The project intentionally followed a bottom-up engineering path:

```text
Data
  -> Indicators
  -> Signals
  -> Positions
  -> Strategy Returns
  -> Equity Curve
  -> Minimal Pipeline
```

The important decision was to avoid jumping straight into a large backtesting framework.

Instead, each sprint added one small layer, with clear input/output contracts and tests. This keeps the system understandable, reviewable, and friendly to AI-assisted development.

## Sprint History

### Sprint 1 — Bootstrap & Market Data Foundation

Goal: create a modern Python project foundation and add the first market data provider.

Delivered:

- Standard Python package structure using `src/` layout.
- `pyproject.toml` with `uv`, `pytest`, and `ruff` workflow.
- `AGENTS.md` to guide Codex and other AI agents.
- `MarketDataProvider` protocol.
- `YahooFinanceProvider` implementation using `yfinance`.
- Basic import and provider tests.

Why it mattered:

- Established the repository as a real engineering project, not a random script folder.
- Created the first data-provider abstraction so future providers can be swapped in.
- Made Codex collaboration safer through explicit project rules.

### Sprint 2 — Indicators Foundation

Goal: add the first pure quantitative indicator functions.

Delivered:

- `simple_moving_average`
- `exponential_moving_average`
- `daily_return`
- Indicator tests covering numeric behavior, index preservation, invalid parameters, and NaN behavior.

Why it mattered:

- Turned raw prices into reusable research features.
- Kept indicators pure and network-free.
- Created the foundation for strategy signals.

### Sprint 3 — Signal Foundation

Goal: convert indicator relationships into explicit trading signal events.

Delivered:

- `crossover_signal(fast, slow)`.
- Signal convention:
  - `1` = bullish / buy event
  - `-1` = bearish / sell event
  - `0` = no event
- Tests for bullish crossover, bearish crossover, no repeated signal, index mismatch, NaN safety, and dtype.

Why it mattered:

- Established the critical distinction between signal events and position states.
- Avoided the common mistake of treating “fast line remains above slow line” as repeated daily buy signals.

### Sprint 4 — Position Foundation

Goal: convert signal events into long-only daily position states.

Delivered:

- `long_only_position(signal)`.
- Position convention:
  - `1` = long / holding the asset
  - `0` = flat / no position
- Validation for invalid signal values and NaN values.
- Tests for state transitions, repeated events, initial behavior, index preservation, and dtype.

Why it mattered:

- Introduced the state layer needed before return calculation.
- Kept the first portfolio model simple: long-only, no shorting, no leverage.

### Sprint 5 — Strategy Return Foundation

Goal: calculate daily strategy returns from daily positions and asset returns.

Delivered:

- `strategy_return(position, asset_return)`.
- Conservative timing rule:

```text
strategy_return[t] = position[t-1] * asset_return[t]
```

- Tests for previous-day position behavior, first-row NaN asset return, invalid positions, unexpected NaNs, index preservation, and dtype.

Why it mattered:

- Prevented look-ahead bias by avoiding same-day position/same-day return assumptions.
- Produced the first daily profit/loss series for a strategy.

### Sprint 6 — Equity Curve Foundation

Goal: compound daily strategy returns into a capital curve.

Delivered:

- `equity_curve(strategy_return, initial_capital=1.0)`.
- Compound return formula:

```text
equity = initial_capital * (1 + strategy_return).cumprod()
```

- Tests for compounding, custom initial capital, flat returns, negative returns, NaNs, invalid capital, empty input, index preservation, and dtype.

Why it mattered:

- Produced the first capital-growth view of a strategy.
- Avoided the common mistake of using simple cumulative sums for compounded returns.

### Sprint 7 — Minimal Backtest Pipeline

Goal: compose all previous layers into one end-to-end research pipeline.

Delivered:

- `moving_average_crossover_pipeline(close, fast_window, slow_window, initial_capital=1.0)`.
- Output DataFrame columns:
  - `close`
  - `fast_sma`
  - `slow_sma`
  - `signal`
  - `position`
  - `asset_return`
  - `strategy_return`
  - `equity`
- Tests for column order, index preservation, deterministic composition, invalid windows, NaN close prices, initial capital, first strategy return, and network isolation.

Why it mattered:

- Created the first complete research loop.
- Kept the pipeline transparent by returning all intermediate outputs.
- Confirmed that the project can now run from input prices to equity curve without live data or hidden side effects.

## Current Architecture After Milestone 1

```text
el_psy_quant/
  data/
    providers.py        # Market data provider abstraction and Yahoo Finance provider
  indicators/
    trend.py            # SMA, EMA, daily returns
  signals/
    crossover.py        # Crossover event signals
  portfolio/
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    equity.py           # Equity curves
  backtesting/
    pipelines.py        # Minimal MA crossover research pipeline
```

## Current Capabilities

The project can now:

- Fetch market data through `YahooFinanceProvider`.
- Calculate basic indicators from price series.
- Generate moving-average crossover events.
- Convert events into long-only position states.
- Calculate daily strategy returns using previous-day positions.
- Compound strategy returns into an equity curve.
- Run one deterministic end-to-end moving-average crossover research pipeline.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- A generic backtesting engine.
- Strategy classes.
- Performance reports.
- CAGR, Sharpe ratio, max drawdown, or volatility metrics.
- Transaction costs or slippage.
- Trade records.
- Cash accounting.
- Broker integration.
- Multi-asset portfolio support.
- Charting or dashboard features.

This was deliberate. The goal was to avoid building a large framework before the core primitives were clear.

## Engineering Principles Proven

Milestone 1 validated several project habits:

1. Build in small, reviewable sprints.
2. Keep functions pure where possible.
3. Test numeric behavior, not just whether code runs.
4. Avoid live network calls in tests.
5. Make timing assumptions explicit.
6. Prefer composition over premature frameworks.
7. Use AI to write code, but keep human review as the final gate.

## Next Milestone Plan — Performance & Research Evaluation

Milestone 2 should turn the current equity curve into basic research evaluation.

Suggested sprint plan:

### Sprint 8 — Basic Performance Metrics

Add pure metric functions:

- `total_return`
- `max_drawdown`
- possibly `annualized_return` / `cagr` if date handling is clear

Keep Sharpe ratio out unless the annualization assumptions are explicit.

### Sprint 9 — Backtest Summary Object

Create a small summary function that takes a pipeline result DataFrame and returns a simple dictionary or dataclass with key metrics.

Avoid a full report system.

### Sprint 10 — Example Research Script

Add a minimal local example that downloads data, runs the pipeline, and prints basic results.

This can become the first real demo of the platform.

### Sprint 11 — Local Data Cache or CSV Provider

Add a local, deterministic data input path so research can run without relying on Yahoo Finance every time.

This helps reproducibility and prepares for more serious testing.

## Milestone 2 Guiding Principle

Do not chase strategy profitability yet.

The next goal is to make strategy evaluation honest, reproducible, and easy to inspect.

Profit comes later. First, build the machine that tells the truth.