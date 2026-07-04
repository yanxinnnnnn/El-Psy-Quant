# Sprint 38 — GitHub Actions CI Foundation

## Objective

Add the first automated GitHub-hosted quality checks for pull requests and
pushes to `main`.

## Product Goal

Basic repository checks should run automatically so code review does not rely
only on local test claims.

## Implementation Scope

- Run one GitHub Actions job on Ubuntu.
- Use Python 3.11 and install project dependencies with `uv`.
- Run the existing pytest suite.
- Run the existing Ruff checks.
- Verify the package import and CLI help entrypoint.
- Trigger on pull requests and pushes to `main`.

## Out of Scope

- Deployment, releases, or package publishing.
- Coverage thresholds or large Python and operating-system matrices.
- Secrets, cloud credentials, Docker builds, or benchmark jobs.
- Feature, strategy, benchmark, or portfolio changes.

## Acceptance Criteria

- `.github/workflows/ci.yml` is small and readable.
- CI runs `pytest`, Ruff, the package import, and CLI help checks.
- The workflow uses Ubuntu and Python 3.11.
- Local project checks continue to pass.
