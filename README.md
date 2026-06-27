# El-Psy-Quant

An AI-native quantitative research and trading platform built in public.

## Mission

Build a production-ready quantitative research platform from zero to production,
using AI as an engineering teammate while keeping human judgment in control.

## Current Stage

**Sprint 1 — Bootstrap & Foundation**

We are not trying to find a magic profitable strategy on day one. The first goal
is to build a reliable platform that can repeatedly test, evaluate, and improve
trading ideas.

## Local setup

Install [uv](https://docs.astral.sh/uv/), then install the project and its
development dependencies:

```bash
uv sync
```

Run the project checks:

```bash
uv run pytest
uv run ruff check .
uv run python -c "import el_psy_quant"
```

## Market data

`YahooFinanceProvider` is the first market data provider. Calls to it access the
network, so applications should handle provider and connectivity errors.

```python
from el_psy_quant.data import YahooFinanceProvider

prices = YahooFinanceProvider().download_daily_prices("AAPL", period="1y")
print(prices.tail())
```

## Indicators

Indicator functions are pure pandas transformations and do not fetch data:

```python
from el_psy_quant.indicators import daily_return, simple_moving_average

close = prices["Close"]
sma_20 = simple_moving_average(close, window=20)
returns = daily_return(close)
```

## Signals

Signals represent crossover events rather than persistent positions:

```python
from el_psy_quant.signals import crossover_signal

fast = simple_moving_average(close, window=20)
slow = simple_moving_average(close, window=50)
signals = crossover_signal(fast, slow)
```

## Core Principles

- AI writes, humans decide.
- Ship every sprint.
- Build capabilities, not random scripts.
- Keep the repository as the single source of truth.
- Prefer simple, reviewable code over clever code.

## Planned Capabilities

- Market data ingestion
- Indicator calculation
- Strategy framework
- Backtesting engine
- Performance reports
- Paper trading
- Cloud automation

## Disclaimer

This project is for education, research, and software engineering practice.
Nothing in this repository is financial advice.
