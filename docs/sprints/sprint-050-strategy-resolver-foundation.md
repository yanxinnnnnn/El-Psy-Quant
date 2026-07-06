# Sprint 50 — Strategy Resolver Foundation

## Objective

Add deterministic resolution for known strategy names.

## Product Goal

Callers should have one small API that lists supported strategies and returns a
fresh strategy implementation for an exact supported name.

## Implementation Scope

- Expose supported names as a deterministic immutable tuple.
- Resolve `moving_average_crossover` to a fresh adapter instance.
- Reject unknown names with the requested and supported names in the error.
- Export the resolver API from the strategies package.

## Resolver Discipline

Resolution is exact and case-sensitive. It performs no normalization, fuzzy or
partial matching, alias lookup, dynamic import, or filesystem discovery.

## Out of Scope

- New strategies or config and CLI wiring.
- Dynamic loading, plugins, entry points, registries, or discovery.
- Artifact, optimization, ranking, portfolio, or trading changes.

## Acceptance Criteria

- Supported names are deterministic and immutable.
- Exact supported names return fresh Strategy-compatible objects.
- Unknown names raise clear `ValueError`s without mutating resolver state.
