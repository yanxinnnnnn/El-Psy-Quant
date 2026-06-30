# Sprint 36 — Milestone 8 Documentation Refresh

## Objective

Close Milestone 8 by documenting the local research operations workflow clearly.

## Product Goal

Users should understand how the Milestone 8 pieces fit together:

```text
YAML config -> deterministic output layout -> minimal CLI run
```

## Implementation Scope

- Add the Milestone 8 summary document.
- Update the roadmap to mark Milestone 8 and Sprint 36 complete.
- Point the roadmap next step to Sprint 37 — Milestone 9 Planning.
- Keep the milestone story focused on local research operations.

## Milestone 8 Summary

Milestone 8 added the first local operations layer on top of the stable research functions:

- Sprint 33 added YAML experiment config loading and validation.
- Sprint 34 added deterministic local output layout helpers.
- Sprint 35 added a thin `argparse` CLI wrapper.
- Sprint 36 closed the milestone with documentation.

The resulting local workflow is:

```bash
el-psy-quant run experiment.yaml --output-root outputs --run-id 20260630T141500Z
```

The command writes only:

```text
config.yaml
metadata.json
results/summary.csv
logs/
```

## Out of Scope

- New CLI behavior.
- New output artifacts.
- New config fields.
- Live downloads from the CLI.
- Databases, schedulers, dashboards, or reports.
- Strategy, benchmark, optimization, or portfolio changes.
- CI setup.

## Acceptance Criteria

- Milestone 8 documentation exists.
- Roadmap marks S36 and Milestone 8 complete.
- The next step is Sprint 37 — Milestone 9 Planning.
- The documentation reinforces that the CLI is an entrypoint, not the architecture.
- No feature code changes are introduced.
