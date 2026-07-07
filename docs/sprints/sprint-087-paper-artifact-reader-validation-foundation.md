# Sprint 87 — Paper Artifact Reader & Validation Foundation

## Objective

Add the smallest useful local reader and top-level validation boundary for saved paper-trading artifact files.

Sprint 87 builds on:

- Sprint 85 paper artifact file contract
- Sprint 86 local paper artifact writer

## Delivered Scope

Sprint 87 adds:

- `read_paper_trading_artifact_file(...)`
- `validate_paper_trading_artifact_file_payload(...)`
- top-level schema/version validation
- top-level key validation against `PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS`
- UTF-8 JSON reading using `PAPER_TRADING_ARTIFACT_FILE_ENCODING`

The reader returns a validated JSON-compatible `dict[str, object]`.

## Validation Boundary

Sprint 87 validates the top-level paper artifact file contract only.

It checks:

- payload is a dictionary
- `schema_version` is present
- `schema_version` matches `PAPER_TRADING_ARTIFACT_SCHEMA_VERSION`
- expected top-level keys are present
- unexpected top-level keys are rejected

Sprint 87 does not deeply reconstruct or validate account state, orders, fills, or session summary objects.

## Critical Boundary

Sprint 87 adds reader and top-level validation behavior only.

It does not reconstruct `PaperTradingArtifact` objects, add `from_dict(...)`, add migrations, create audit summaries, add default output directories, or integrate with configured runs, CLI workflows, databases, dashboards, brokers, exchange APIs, live execution, or order routing.

The existing `PaperTradingArtifact` remains an in-memory immutable artifact boundary.

## Out of Scope

Sprint 87 does not add:

- audit summary behavior
- deep object reconstruction
- `PaperTradingArtifact.from_dict(...)`
- automatic migrations
- schema migration framework
- default output directories
- run-id directory conventions
- configured-run integration
- CLI workflow expansion
- broker integration
- exchange APIs
- live execution
- order routing
- market data streaming
- real account synchronization
- database behavior
- dashboard behavior
- report generation
- plugin frameworks or dynamic loading
