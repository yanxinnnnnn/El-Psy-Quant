# Sprint 45 — Experiment Comparison Foundation

## Objective

Add a small Python API for comparing metrics from saved local experiment runs.

## Product Goal

A reviewer should be able to provide two or more run directories and receive a
single table of their existing per-symbol metrics without rerunning backtests.

## Implementation Scope

- Read each run's `manifest.json` and follow its relative metrics artifact path.
- Read versioned `results/metrics.json` artifacts.
- Combine run identity and existing metric records in one pandas DataFrame.
- Preserve input run order and per-run metric record order.
- Reject missing, unsupported, absolute, or parent-traversing artifacts.

## Comparison Discipline

The helper surfaces saved values only. It does not calculate metrics, sort by
performance, rank runs, select winners, or make trading decisions.

## Out of Scope

- New metrics, recomputation, strategies, optimization, or ranking.
- CLI commands, charts, dashboards, databases, cloud storage, or reports.
- Trading decisions or live data.

## Acceptance Criteria

- Two or more saved runs produce one deterministic comparison DataFrame.
- Existing metric and annualized metric columns are preserved.
- Unsafe or incomplete artifact paths raise clear `ValueError`s.
- No new metric or performance-ranking logic is introduced.
