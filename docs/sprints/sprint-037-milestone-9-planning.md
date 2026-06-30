# Sprint 37 — Milestone 9 Planning

## Objective

Choose the next platform foundation milestone after closing the local research operations loop in Milestone 8.

## CTO Decision

Milestone 9 will be:

```text
Project Quality Foundation
```

The reason is simple: the project now has enough surface area that local claims are no longer enough. Tests and lint checks should run automatically on pull requests before deeper CTO review.

During Milestone 8 reviews, the main repeated operational weakness was clear:

```text
Codex says tests passed locally, but GitHub does not verify it.
```

That is fine for an early toy repo. It is not fine for a platform that is becoming more serious.

## Milestone 9 Product Goal

As the founder, I want every future pull request to have basic automated quality signals so code review can focus on scope, architecture, and research correctness instead of wondering whether the basic checks were actually run.

## Planned Sprint Sequence

### Sprint 38 — GitHub Actions CI Foundation

Goal: add GitHub-hosted quality checks.

Expected checks:

```text
uv run pytest
uv run ruff check .
uv run python -c "import el_psy_quant"
uv run el-psy-quant --help
```

Guardrail: no deployment, packaging, release automation, coverage gates, or matrix explosion yet.

### Sprint 39 — Repository Hygiene Guardrails

Goal: prevent avoidable diff noise and review friction.

Expected work:

- Add line-ending normalization.
- Add a concise pull request template.
- Document expected PR evidence.

Guardrail: do not turn this into style bikeshedding.

### Sprint 40 — Local Quality Check Entrypoint

Goal: give humans and Codex one local command that mirrors CI.

Expected work:

- Add a small local check entrypoint or script.
- Keep it cross-platform and easy to understand.
- Avoid heavy task-runner frameworks.

Guardrail: no nox, tox, makefile dependency, or custom build system unless there is a clear need.

### Sprint 41 — Milestone 9 Documentation Refresh

Goal: close the milestone and summarize the new quality workflow.

Expected work:

- Add Milestone 9 summary documentation.
- Update README and roadmap.
- Explain the quality gate workflow and what remains out of scope.

Guardrail: no new feature behavior.

## Out of Scope for Milestone 9

- New trading strategy logic.
- New data providers.
- New research outputs.
- New CLI behavior except quality checks.
- Deployment automation.
- Release automation.
- Package publishing.
- Coverage thresholds.
- Large CI matrices.
- Formatting wars.

## Acceptance Criteria for Sprint 37

- Roadmap includes Milestone 9.
- Milestone 9 has a clear theme, goal, and sprint sequence.
- Current next step is Sprint 38 — GitHub Actions CI Foundation.
- No feature code is changed.

## Engineering Principle Reinforced

```text
Automated quality gates should verify basic claims before humans review deeper logic.
```

Human judgment still owns product direction and architecture. CI should handle the boring checks so humans can spend attention where it matters.
