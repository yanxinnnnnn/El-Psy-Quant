# Sprint 39 — Repository Hygiene Guardrails

## Objective

Reduce avoidable diff noise and make pull requests easier to review without
introducing a broader style or tooling framework.

## Product Goal

Repository defaults should keep text line endings consistent, while pull
requests should carry concise scope and validation evidence for CTO review.

## Implementation Scope

- Normalize text files to LF through a small `.gitattributes` rule.
- Add a concise pull request template covering summary, scope, validation,
  guardrails, and CTO review notes.
- Keep the roadmap aligned with completed quality-foundation sprints.

## Why These Guardrails Matter

Consistent line endings prevent whole-file diffs that hide semantic changes.
A short PR template keeps review evidence visible without requiring a heavy
process. These guardrails help reviewers focus on architecture, scope, and
research correctness.

## Out of Scope

- Formatter or pre-commit adoption.
- Lint or Ruff configuration changes.
- CI redesign or branch-protection automation.
- Feature code, test, or broad formatting changes.

This sprint is repository hygiene, not style policing.

## Acceptance Criteria

- Text files default to LF line endings.
- New pull requests receive a concise review template.
- No existing files are broadly reformatted or renormalized.
