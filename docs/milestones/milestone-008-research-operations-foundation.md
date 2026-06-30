# Milestone 8 — Research Operations Foundation

## Milestone Summary

Milestone 8 moved El-Psy-Quant from reusable research functions toward a small local research operations workflow.

Milestone 7 answered:

```text
Can we run the same local research workflow across multiple symbols and inspect the results side by side?
```

Milestone 8 answered:

```text
Can we describe, run, and store local experiments consistently without turning the project into a heavy framework?
```

The project can now load a local YAML experiment config, create a deterministic output directory, run the current local moving-average crossover workflow from the command line, and write a minimal set of local artifacts for inspection.

The milestone deliberately stayed local and boring. That was the point. A research platform becomes more useful when repeated experiments are easy to describe, repeat, and inspect before adding richer automation.

## Product Thinking

Milestone 8 followed this progression:

```text
YAML experiment config
  -> deterministic output layout
  -> minimal CLI wrapper
```

The key idea was to stop making every repeated experiment depend on one-off Python glue.

Before this milestone, the project already had useful research functions, but the workflow was still mostly code-driven. A user had to know which functions to call, where to place outputs, and how to repeat the same run later.

After this milestone, the local workflow has a clearer operational shape:

```text
experiment.yaml
  -> el-psy-quant run ...
  -> outputs/<experiment>/<run-id>/
       config.yaml
       metadata.json
       results/summary.csv
       logs/
```

This is not a production research system yet. It is the first local operations layer.

## Sprint History

### Sprint 33 — Experiment Config Foundation

Goal: add a small local experiment configuration format.

Delivered:

- `src/el_psy_quant/config.py`
- YAML-based experiment config loading.
- Typed config objects for:
  - experiment metadata
  - data input settings
  - moving-average crossover parameters
  - evaluation assumptions
- Support for local data sources:
  - `csv`
  - `cache`
- Validation for:
  - required sections
  - supported strategy
  - symbol normalization and duplicates
  - moving-average windows
  - capital, cost, and slippage assumptions
  - evaluation frequency

Why it mattered:

- Repeated experiments need a stable human-readable spec.
- YAML is easier to review than scattered function-call arguments.
- Config can be versioned with the repo.

What we deliberately avoided:

- Complex config frameworks.
- TOML support in this milestone.
- CLI behavior.
- Experiment execution.
- Output writing.

### Sprint 34 — Local Experiment Output Layout

Goal: define where local experiment artifacts should go.

Delivered:

- `src/el_psy_quant/outputs.py`
- `ExperimentOutputLayout`
- `create_experiment_output_layout(...)`
- Experiment-name slugification.
- Strict run-id validation.
- UTC timestamp run IDs when omitted.
- Deterministic local directory shape:

```text
<output_root>/<experiment-name>/<run-id>/
  config.yaml
  metadata.json
  results/
  logs/
```

Why it mattered:

- Future experiment artifacts need predictable locations.
- Path conventions should be centralized before artifacts multiply.
- The output layout should not depend on ad hoc user code.

What we deliberately avoided:

- Writing config or metadata contents.
- Writing result files.
- Databases.
- Cloud storage.
- Experiment runners.

### Sprint 35 — Minimal CLI Wrapper

Goal: add a thin terminal entrypoint for the current local configured workflow.

Delivered:

- `src/el_psy_quant/cli.py`
- Console script:

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

- Module execution support:

```bash
python -m el_psy_quant.cli run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

- Local config loading through the config module.
- Local CSV/cache data loading through existing multi-symbol helpers.
- Moving-average crossover execution through existing backtesting helpers.
- Cross-symbol summary through the existing summary helper.
- Minimal artifacts:
  - copied `config.yaml`
  - basic `metadata.json`
  - `results/summary.csv`

Why it mattered:

- Users can now run one local configured experiment without writing Python glue.
- The CLI makes the config and output-layout work usable from the terminal.
- The command remains a wrapper around stable functions, not a new architecture core.

What we deliberately avoided:

- Extra CLI frameworks.
- Interactive prompts.
- Live downloads.
- Per-symbol full result exports.
- Report generation.
- New strategy behavior.

### Sprint 36 — Milestone 8 Documentation Refresh

Goal: close the milestone by documenting the research operations layer clearly.

Delivered:

- Milestone 8 summary documentation.
- Updated project-level documentation to describe the local operations workflow.
- Roadmap updates to mark Milestone 8 complete and prepare for the next planning step.

Why it mattered:

- A platform is not only code. It also needs a clear operating story.
- The repo should explain what the local workflow does and what it intentionally does not do.

## Current Architecture After Milestone 8

```text
el_psy_quant/
  cli.py         # Thin argparse entrypoint for local configured experiments
  config.py      # Load and validate local YAML experiment settings
  outputs.py     # Create deterministic local experiment directories and reserved paths
  data/
    cache.py            # Local CSV cache read/write helpers
    csv.py              # Local CSV daily price loader
    multi.py            # Local multi-symbol CSV/cache loading helpers
    providers.py        # Market data provider abstraction and Yahoo Finance provider
    workflows.py        # Explicit Yahoo-to-cache workflow with clearer failure handling
  indicators/
    trend.py            # SMA, EMA, daily returns
  signals/
    crossover.py        # Crossover event signals
  portfolio/
    costs.py            # Transaction cost drag from position turnover
    equity.py           # Equity curves
    positions.py        # Long-only position states
    returns.py          # Strategy returns
    slippage.py         # Slippage drag from position turnover
    trades.py           # Long-only trade record extraction
  backtesting/
    benchmarks.py       # Local buy-and-hold benchmark comparison
    experiments.py      # Parameter sweep and descriptive experiment overview helpers
    multi.py            # Multi-symbol strategy execution and summary helpers
    pipelines.py        # Minimal MA crossover research pipeline with costs/slippage
    trades.py           # Trade record helper for pipeline results
    workflows.py        # CSV-to-pipeline convenience workflow
  performance/
    metrics.py          # Total return, drawdown, annualized metrics, Sharpe-style ratio
    summary.py          # Compact backtest summary with optional annualized/risk metrics
```

## Current Supported Workflow

A local configured experiment now looks like this:

```yaml
experiment:
  name: ma-crossover-local
  strategy: moving_average_crossover

data:
  source: csv
  paths:
    AAPL: data/cache/AAPL.csv
    MSFT: data/cache/MSFT.csv

parameters:
  fast_window: 20
  slow_window: 50
  initial_capital: 1000.0
  transaction_cost_rate: 0.001
  slippage_rate: 0.0005

evaluation:
  periods_per_year: 252
  annual_risk_free_rate: 0.02
```

It can be run with:

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The run writes:

```text
outputs/ma-crossover-local/20260630T141500Z/
  config.yaml
  metadata.json
  results/summary.csv
  logs/
```

## Current Capabilities

The project can now:

- Load and validate local YAML experiment configs.
- Validate the currently supported `moving_average_crossover` strategy config.
- Load local CSV or cache data for multiple symbols from config.
- Create deterministic local output directories for experiment runs.
- Run one configured local moving-average crossover experiment from the CLI.
- Copy the original config into the run directory.
- Write basic run metadata.
- Write a cross-symbol summary CSV.
- Keep logs as a reserved directory for future use.
- Preserve existing local-only deterministic research workflows.

## What This Milestone Deliberately Avoided

The project intentionally did not build:

- Live data downloads from the CLI.
- New strategy logic.
- Strategy selection beyond moving-average crossover.
- Per-symbol full result exports.
- HTML, PDF, notebook, or dashboard reports.
- Databases.
- Schedulers.
- Cloud storage.
- Experiment tracking servers.
- Portfolio construction.
- Capital allocation.
- Rebalancing.
- Production trading.

This was deliberate. Milestone 8 focused on a local operations loop, not a full research platform backend.

## Research Discipline Reinforced

Milestone 8 reinforced one important rule:

```text
Operational convenience should wrap stable research functions, not replace them.
```

A CLI can make workflows easier to repeat, but it should not become the place where research logic hides. The command line is an entrypoint. The package remains the architecture.

## Engineering Principles Reinforced

Milestone 8 reinforced several habits:

1. Use human-readable config for repeated experiments.
2. Validate experiment assumptions before running work.
3. Keep outputs deterministic and inspectable.
4. Keep CLI code thin and boring.
5. Reuse stable internal functions instead of duplicating logic.
6. Write only the artifacts the milestone actually needs.
7. Keep local reproducibility ahead of live convenience.
8. Avoid databases, dashboards, and schedulers until the local workflow earns them.

## Next Milestone Direction

Milestone 8 closed the first local research operations loop.

The next milestone should be planned deliberately rather than guessed. Good candidates include:

- CI and project quality gates.
- Richer experiment artifacts.
- Better result comparison across runs.
- A broader strategy interface.
- Portfolio construction foundations.

The right next step is to choose the next platform direction without overloading the simple local workflow that now works.
