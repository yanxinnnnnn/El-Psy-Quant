# Milestone 10 — Experiment Artifact & Comparison Foundation

## Status

Complete.

Milestone 10 followed two important foundations:

- Milestone 8 made configured local experiments runnable and easier to store.
- Milestone 9 made repository changes easier to trust through CI and review hygiene.

Milestone 10 turned local experiment outputs into inspectable research artifacts.

## Product Outcome

A configured local experiment run now leaves behind a small artifact chain:

```text
manifest.json -> results/metrics.json -> comparison DataFrame
```

That chain lets a reviewer answer:

- what experiment ran
- which strategy and assumptions were used
- where the run artifacts live
- which metrics were produced
- how saved runs compare at the existing metric level

This is still a local research workflow. It is not a database-backed experiment platform.

## Sprint History

| Sprint | Status | Main Deliverable | Guardrail |
|---:|---|---|---|
| S42 | Complete | Milestone 10 planning and scope. | No implementation during planning. |
| S43 | Complete | `manifest.json` for configured experiment runs. | No database, dashboard, or registry. |
| S44 | Complete | `results/metrics.json` derived from existing summary metrics. | No new metrics. |
| S45 | Complete | `compare_experiment_runs` helper for saved local run folders. | No optimization or ranking. |
| S46 | Complete | Milestone 10 documentation refresh. | No product code changes. |

## What Changed

### Run Manifest

Each configured experiment run now writes:

```text
manifest.json
```

The manifest records run identity, strategy, data source, parameters, evaluation assumptions, and run-relative artifact paths.

### Metrics Artifact

Each configured experiment run now writes:

```text
results/metrics.json
```

The metrics artifact serializes the existing per-symbol summary metrics into machine-readable JSON.

It does not calculate new metrics. It mirrors values already produced by the current summary path.

### Comparison Helper

The project now exposes:

```python
from el_psy_quant.comparison import compare_experiment_runs
```

The helper reads saved run folders, follows each manifest's metrics artifact path, and returns one deterministic pandas DataFrame.

It preserves input run order and per-run symbol order. It does not sort by performance, rank runs, select winners, or make strategy claims.

## Artifact Discipline

Milestone 10 deliberately avoided:

- databases
- dashboards
- cloud storage
- experiment registries
- new metrics
- metric recomputation
- strategy optimization
- performance ranking
- best-run selection
- trading decisions

This was the right tradeoff. The project needed artifact discipline before strategy proliferation.

## Current Research Flow

A local configured experiment can now produce:

```text
config.yaml
metadata.json
manifest.json
results/summary.csv
results/metrics.json
logs/
```

Saved run folders can then be compared from local artifacts without rerunning the backtest.

## Why This Matters

Before this milestone, local experiments could run and produce summaries, but the output was not yet a stable research asset.

After this milestone, each run has enough structure to be inspected and compared later. That makes future research safer because the project can compare existing evidence instead of relying on memory, screenshots, or manual CSV inspection.

## Next Milestone Candidate

The next milestone should be:

```text
Milestone 11 — Strategy Interface Foundation
```

The project now has enough experiment artifact structure to justify improving strategy boundaries.

The next milestone should define how strategies plug into the research system without rushing into many strategies or live trading.

## Closeout Note

Milestone 10 is complete because the project can now move through this chain:

```text
configured run -> stable manifest -> stable metrics artifact -> deterministic comparison table
```

That is enough for the artifact and comparison foundation. Further work belongs in the next milestone, not in this one.
