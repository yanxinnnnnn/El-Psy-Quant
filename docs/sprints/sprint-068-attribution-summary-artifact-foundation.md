# Sprint 68 — Attribution Summary Artifact Foundation

## Objective

Add a standalone, machine-readable attribution summary artifact built from
existing portfolio risk, drawdown, and symbol contribution helpers.

## Implementation Scope

- Record a schema version and normalized portfolio construction assumptions.
- Validate and record static weights when supplied.
- Compose existing portfolio risk, worst-drawdown, and symbol contribution
  summaries without reimplementing their calculations.
- Record the optional annualization frequency.
- Return deterministic, JSON-compatible data without mutating inputs.

## Artifact Scope

Sprint 68 adds a standalone attribution summary artifact builder only. It does
not write or alter configured experiment artifacts and does not introduce new
attribution mathematics.

## Out of Scope

- Configured-run, YAML, CLI, manifest, or metrics changes.
- New attribution calculations, dynamic weights, or rebalancing.
- Portfolio construction, strategy, resolver, database, or dashboard changes.
- Plugin frameworks or dynamic loading.

## Acceptance Criteria

- Construction metadata preserves normalized symbol order and optional weights.
- Risk, drawdown, and contribution sections match their existing helpers.
- The artifact is deterministic, strictly JSON-compatible, and versioned.
- Invalid construction methods and weights fail clearly.
