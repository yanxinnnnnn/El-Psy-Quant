# Sprint 34 — Local Experiment Output Layout

## Objective

Add a deterministic local directory and path contract for future experiment
artifacts without building an experiment runner.

## Product Goal

Each future local experiment run should have predictable locations for its
configuration, metadata, results, and logs.

## Implementation Scope

- Slugify experiment names into safe directory names.
- Validate caller-provided run IDs or generate a UTC timestamp run ID.
- Create experiment, run, results, and logs directories.
- Return typed `Path` values for directories and reserved artifact locations.
- Document the output layout and public helper.

## Output Shape

```text
<output_root>/<experiment_name>/<run_id>/
  config.yaml
  metadata.json
  results/
  logs/
```

`config.yaml` and `metadata.json` are reserved paths only. This sprint does not
create them or write result contents.

## Out of Scope

- Experiment execution, strategy changes, or benchmark changes.
- Config, metadata, result, report, or log file writing.
- CLI commands, databases, schedulers, dashboards, or cloud storage.
- Live downloads or portfolio logic.

## Acceptance Criteria

- Layout paths are deterministic when a run ID is supplied.
- Timestamp run IDs use UTC `YYYYMMDDTHHMMSSZ` format.
- Only the required directories are created.
- Tests are deterministic, local-only, and network-free.
- `uv run pytest` and `uv run ruff check .` pass.
