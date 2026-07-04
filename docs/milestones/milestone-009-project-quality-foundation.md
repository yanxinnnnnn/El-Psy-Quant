# Milestone 9 — Project Quality Foundation

## Status

Complete.

## Summary

Milestone 9 added the first practical project quality foundation for El-Psy-Quant.

Before this milestone, review quality relied too heavily on local claims: a contributor or Codex could say that tests passed, but the repository itself did not enforce a shared quality gate. This milestone changed that by adding GitHub-hosted checks, repository hygiene guardrails, and a local quality command that mirrors CI.

The goal was not to add research features. The goal was to make future research and platform changes safer to review.

## Product Outcome

Pull requests can now be checked consistently without relying only on local claims.

The repository now has:

- GitHub Actions CI for pull requests and pushes to `main`.
- A single quality job using Ubuntu, Python 3.11, and `uv`.
- Automated checks for pytest, Ruff, package import, and CLI help.
- Repository line-ending normalization through `.gitattributes`.
- A concise pull request template for review evidence.
- A local quality-check entrypoint in `scripts/check.py`.
- CI invoking `scripts/check.py`, making the script the single source of truth for quality commands.

## Sprint History

| Sprint | Status | Main Deliverable | Guardrail |
|---:|---|---|---|
| S37 | Complete | Planned Milestone 9 and chose project quality before more research surface area. | No feature work during planning. |
| S38 | Complete | Added GitHub Actions CI for PRs and pushes to `main`. | No deployment, release automation, package publishing, or coverage gate. |
| S39 | Complete | Added `.gitattributes`, a PR template, and repository hygiene documentation. | No formatter, pre-commit framework, or style crusade. |
| S40 | Complete | Added `scripts/check.py` and aligned CI to call it. | No task-runner framework or duplicated quality command list. |
| S41 | Complete | Refreshed milestone documentation and closed Milestone 9. | Documentation only. |

## Architecture Impact

Milestone 9 changed the project from a locally checked codebase into a repository with a basic automated quality loop.

The quality path is now:

```text
scripts/check.py
  -> uv run pytest
  -> uv run ruff check .
  -> uv run python -c "import el_psy_quant"
  -> uv run el-psy-quant --help
```

GitHub Actions calls the same script:

```text
.github/workflows/ci.yml
  -> uv sync
  -> uv run python scripts/check.py
```

That makes `scripts/check.py` the quality command source of truth. If a future sprint adds another basic quality check, it should normally be added to the script once, then CI will inherit it automatically.

## Repository Hygiene Added

Milestone 9 also added review-noise controls:

```text
.gitattributes
.github/pull_request_template.md
```

`.gitattributes` normalizes text files to LF so line-ending churn does not hide semantic changes.

The pull request template asks for:

- Summary.
- Scope.
- Validation.
- Out of scope / guardrails.
- Notes for CTO review.

The template is intentionally short. Its purpose is to surface review evidence, not to create bureaucracy.

## What This Milestone Did Not Do

Milestone 9 intentionally did not add:

- New strategies.
- New data providers.
- Portfolio construction.
- Backtest feature expansion.
- Deployment automation.
- Package publishing.
- Branch protection automation.
- Coverage thresholds.
- Large Python or OS matrices.
- Formatter or pre-commit adoption.

The project needed a reliable quality base before adding more platform surface area.

## Review Principle Established

Milestone 9 established a new review standard:

```text
Local claims are useful, but GitHub CI is the entry ticket for review.
```

For future implementation sprints, the expected delivery remains:

```text
implement -> test -> commit -> push -> open PR -> mark PR ready for review -> return PR URL
```

But after Milestone 9, review should also check that the GitHub CI quality job is green.

## Current Capability Boundary

The repository now has better engineering discipline, but it still does not claim production trading readiness.

The project remains a research platform foundation. It does not yet have:

- Strategy plugin interfaces.
- Data integrity checks beyond current loaders.
- Portfolio construction.
- Portfolio risk attribution.
- Execution realism beyond existing costs and slippage.
- Paper trading or broker integration.

Those belong to future milestones.

## Next Milestone Candidate

The recommended next milestone is:

```text
Milestone 10 — Experiment Artifact & Comparison Foundation
```

Reason:

Milestone 8 made experiments runnable. Milestone 9 made changes safer to review. The next high-leverage step is to make experiment outputs easier to compare and inspect across runs without rushing into strategy proliferation.

## CTO Assessment

Milestone 9 was deliberately unglamorous, and that was the point.

A quant research platform that cannot reliably check its own changes will eventually drown in fragile experiments, noisy diffs, and unverifiable claims. This milestone added the minimum quality machinery needed before expanding the research surface again.
