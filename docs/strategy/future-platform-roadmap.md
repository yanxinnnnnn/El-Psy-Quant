# Future Platform Roadmap — CTO Plan

## Purpose

This document captures the long-term technical direction for El-Psy-Quant after Milestone 9 planning.

The project should not rush into live trading or a zoo of strategies. A professional quantitative research platform becomes valuable when it can support this chain reliably:

```text
data can be trusted
  -> experiments can be reproduced
  -> results can be compared
  -> strategies can be extended
  -> portfolios can be constructed
  -> risk can be explained
  -> execution assumptions can be controlled
```

The near-term goal is not to find a magic strategy. The goal is to build a system that is hard to fool.

## Planning Principles

1. Quality gates before more surface area.
2. Experiment comparison before strategy proliferation.
3. Strategy interfaces before strategy quantity.
4. Data integrity before portfolio construction.
5. Portfolio construction before portfolio risk attribution.
6. Execution timing discipline before paper trading.
7. Paper trading before any real-money trading.

## Recommended Milestone Sequence

```text
Milestone 9  — Project Quality Foundation
Milestone 10 — Experiment Artifact & Comparison Foundation
Milestone 11 — Strategy Interface Foundation
Milestone 12 — Data Integrity & Universe Foundation
Milestone 13 — Portfolio Construction Foundation
Milestone 14 — Portfolio Risk & Attribution Foundation
Milestone 15 — Backtest Execution Realism Foundation
Milestone 16 — Paper Trading Foundation
```

## Milestone 9 — Project Quality Foundation

### Goal

Add automated quality gates and repository hygiene before the project adds more research behavior.

### Why This Comes Next

The project now has enough code and documentation that local claims are not enough. PR review should not rely only on someone saying:

```text
tests passed locally
```

GitHub should verify the basic checks automatically.

### Planned Sprints

```text
S37 — Milestone 9 Planning
S38 — GitHub Actions CI Foundation
S39 — Repository Hygiene Guardrails
S40 — Local Quality Check Entrypoint
S41 — Milestone 9 Documentation Refresh
```

### Exit Criteria

Pull requests can be checked consistently with automated CI signals.

### Guardrails

- No deployment automation.
- No release automation.
- No package publishing.
- No large CI matrix.
- No coverage threshold yet.

## Milestone 10 — Experiment Artifact & Comparison Foundation

### Goal

Make experiment results easier to inspect, compare, and revisit.

Milestone 8 created:

```text
config -> CLI -> output folder
```

Milestone 10 should make the output folder more useful without jumping to a database.

### Planned Direction

```text
S42 — Standard Experiment Artifact Schema
S43 — Run Metadata Enhancement
S44 — Run Comparison Helper
S45 — Milestone 10 Documentation Refresh
```

### Expected Capabilities

A run directory should become more informative:

```text
outputs/<experiment>/<run-id>/
  config.yaml
  metadata.json
  results/
    summary.csv
    metrics.json
  logs/
```

The project should be able to answer:

```text
What changed between these two runs?
Which parameters changed?
How did the main metrics change?
```

### Guardrails

- No database.
- No MLflow.
- No W&B.
- No cloud artifact tracking.
- No heavy experiment tracking server.

### CTO Judgment

Use the file system well before adding a database. Databases added too early turn simple research workflows into migration work.

## Milestone 11 — Strategy Interface Foundation

### Goal

Turn moving-average crossover from the only strategy into the first strategy.

### Why This Matters

Adding many strategies without a stable interface will break config, CLI, artifacts, and tests. The project needs a small strategy contract before strategy count grows.

### Planned Direction

```text
S46 — Strategy Protocol / Interface
S47 — Strategy Registry
S48 — Configurable Strategy Dispatch
S49 — First Additional Baseline Strategy
S50 — Milestone 11 Documentation Refresh
```

### Expected Capabilities

A new strategy should be added without rewriting the CLI or output workflow.

A future config could look like:

```yaml
experiment:
  name: momentum-test
  strategy: momentum

parameters:
  lookback_window: 60
```

### Guardrails

- No strategy zoo.
- No complex plugin framework.
- No machine learning strategy layer yet.
- No production trading claims.

### CTO Judgment

A professional platform should make strategies easy to add, but hard to add sloppily.

## Milestone 12 — Data Integrity & Universe Foundation

### Goal

Move from loading CSV files to understanding whether the data is fit for research.

### Why This Matters

Bad data can create fake alpha. Before portfolio construction, the project needs better data quality visibility.

Common problems include:

```text
missing dates
duplicate dates
short histories
symbol coverage gaps
uneven calendars
invalid price columns
```

### Planned Direction

```text
S51 — Data Quality Report
S52 — Multi-Symbol Date Alignment
S53 — Symbol Universe Config
S54 — Calendar / Missing Data Policy
S55 — Milestone 12 Documentation Refresh
```

### Expected Capabilities

The project should produce a quality report like:

```text
symbol | start_date | end_date | rows | missing_dates | duplicate_dates | status
```

A future universe config could look like:

```yaml
universe:
  name: us-large-cap-test
  symbols:
    - AAPL
    - MSFT
    - NVDA
```

### Guardrails

- No enterprise data platform.
- No real-time data pipeline.
- No market data database yet.
- No vendor integration expansion.

### CTO Judgment

Data quality should come before portfolio complexity. Otherwise the system will confidently backtest noise.

## Milestone 13 — Portfolio Construction Foundation

### Goal

Move from independent multi-symbol results to actual portfolio-level research.

### Why This Matters

Milestone 7 intentionally avoided portfolio construction. That was correct. Multi-symbol research is not automatically portfolio research.

Milestone 13 is where the project should finally build a simple portfolio layer.

### Planned Direction

```text
S56 — Portfolio Input Contract
S57 — Static Weight Portfolio
S58 — Rebalanced Equal-Weight Portfolio
S59 — Portfolio Equity Curve
S60 — Milestone 13 Documentation Refresh
```

### Expected Capabilities

The project should produce:

```text
portfolio daily return
portfolio equity curve
portfolio drawdown
portfolio turnover
portfolio weights
```

A future config could look like:

```yaml
portfolio:
  weighting: equal_weight
  rebalance: monthly
  initial_capital: 100000
```

### Guardrails

- No portfolio optimization yet.
- No Markowitz optimizer.
- No Black-Litterman.
- No risk parity.
- No production allocation engine.

### CTO Judgment

Start with static weights and equal weights. Get the accounting right before optimization enters the room wearing a lab coat.

## Milestone 14 — Portfolio Risk & Attribution Foundation

### Goal

Explain portfolio behavior instead of only reporting portfolio performance.

### Why This Matters

A portfolio equity curve is not enough. A research platform should help answer:

```text
Which symbols contributed to return?
Which symbols contributed to drawdown?
Where is exposure concentrated?
How much turnover did the strategy create?
How did the portfolio compare with a benchmark?
```

### Planned Direction

```text
S61 — Portfolio Risk Metrics
S62 — Symbol Contribution Attribution
S63 — Portfolio Benchmark Comparison
S64 — Turnover & Exposure Summary
S65 — Milestone 14 Documentation Refresh
```

### Expected Capabilities

The project should expose:

```text
portfolio_total_return
portfolio_max_drawdown
portfolio_volatility
portfolio_sharpe
symbol_return_contribution
symbol_drawdown_contribution
turnover
exposure
```

### Guardrails

- No production risk system.
- No real-time dashboard.
- No VaR mega-project.
- No factor model unless the simpler attribution layer is stable.

### CTO Judgment

Risk explanation should come before complex risk modeling.

## Milestone 15 — Backtest Execution Realism Foundation

### Goal

Make backtests more explicit about signal time, fill time, and fill price assumptions.

### Why This Matters

A strategy can look excellent if it accidentally trades with information it would not have had in reality. Execution timing discipline is one of the biggest differences between toy backtests and serious backtests.

### Planned Direction

```text
S66 — Signal Timestamp Discipline
S67 — Next-Bar Execution Model
S68 — Order Fill Assumption Layer
S69 — Execution Cost Model Extension
S70 — Milestone 15 Documentation Refresh
```

### Expected Capabilities

A future config could look like:

```yaml
execution:
  signal_price: close
  fill_price: next_open
  delay_bars: 1
```

The project should clearly distinguish:

```text
when the signal is known
when the order is placed
when the fill happens
which price is used for the fill
```

### Guardrails

- No broker integration.
- No real orders.
- No intraday execution engine.
- No high-frequency assumptions.

### CTO Judgment

Without execution timing discipline, backtests can lie beautifully.

## Milestone 16 — Paper Trading Foundation

### Goal

Add a simulated trading workflow only after research, portfolio, risk, and execution assumptions are stable.

### Why This Comes Later

Paper trading is not a shortcut. It should be a rehearsal environment for a system that already has solid research discipline.

### Planned Direction

```text
S71 — Paper Account Model
S72 — Paper Order Lifecycle
S73 — Paper Broker Adapter Interface
S74 — Daily Paper Run Workflow
S75 — Milestone 16 Documentation Refresh
```

### Expected Capabilities

The project should support a local simulated loop:

```text
generate signal
create paper order
simulate fill
update paper position
record paper portfolio state
```

### Guardrails

- No live trading.
- No real broker orders.
- No real money.
- No unattended trading.

### CTO Judgment

Paper trading is a training ground, not a license to trade real capital.

## Explicit Non-Priorities

The project should not prioritize these too early:

```text
many strategies for the sake of count
live broker integration
real-money trading
deep learning alpha
high-frequency trading
complex web dashboards
large databases
portfolio optimization before basic portfolio accounting
```

These can be useful later, but early versions would create complexity before the platform has earned it.

## One-Line Strategy

```text
Do not rush to find a magic strategy. Build a research system that is hard to fool.
```
