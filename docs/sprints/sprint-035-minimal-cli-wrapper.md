# Sprint 35 — Minimal CLI Wrapper

## Objective

Add a small standard-library command-line entrypoint for running one existing
local YAML-configured moving-average crossover experiment.

## Product Goal

Users should be able to compose the stable local config, data, backtesting,
summary, and output-layout functions without writing one-off Python glue.

## Implementation Scope

- Add an `argparse` `run` command and console-script entrypoint.
- Load validated YAML through the existing config module.
- Load local CSV or cache data through existing multi-symbol helpers.
- Compose existing crossover execution and cross-symbol summary helpers.
- Create the existing deterministic output layout.
- Write only copied config, basic metadata, and `results/summary.csv`.
- Print the run directory and return a process-friendly status code.

## Output Shape

```text
<output_root>/<experiment_name>/<run_id>/
  config.yaml
  metadata.json
  results/summary.csv
  logs/
```

## Out of Scope

- Additional CLI frameworks or interactive prompts.
- Live downloads, cloud storage, databases, schedulers, or dashboards.
- Reports or per-symbol full-result exports.
- New strategy, benchmark, optimization, or portfolio behavior.

## Acceptance Criteria

- Both the console script and `python -m el_psy_quant.cli` expose the command.
- Valid local configs create exactly the minimal required artifacts.
- Ordinary validation and local I/O failures return a concise non-zero error.
- Tests remain deterministic and network-free.
- `uv run pytest` and `uv run ruff check .` pass.
