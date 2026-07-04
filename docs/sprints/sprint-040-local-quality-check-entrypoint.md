# Sprint 40 — Local Quality Check Entrypoint

## Objective

Add one small local command that mirrors the repository's GitHub Actions CI
checks.

## Product Goal

Contributors and Codex should be able to run the same quality gate locally
before opening a pull request.

## Implementation Scope

- Add `scripts/check.py` using only the Python standard library.
- Run pytest, Ruff, the package import check, and CLI help check in CI order.
- Print each command before execution.
- Stop immediately and return nonzero when a command fails.
- Document the single local invocation in README.

## Design

Commands are passed to `subprocess.run` as argument sequences without a shell.
The script is an entrypoint, not a task-runner framework.

## Out of Scope

- nox, tox, Makefile dependencies, or pre-commit.
- Formatters, lint rule changes, or CI redesign.
- Branch-protection, feature code, or test changes.
- Complex command-line parsing or plugins.

## Acceptance Criteria

- `uv run python scripts/check.py` runs the four CI checks in order.
- Each command is visible before it runs.
- The script fails fast and returns the failed command's nonzero status.
- Existing GitHub CI remains unchanged.
