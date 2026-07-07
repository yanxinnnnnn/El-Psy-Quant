# Sprint 85 — Paper Artifact File Contract Foundation

## Objective

Define the smallest useful file contract for saved paper-trading artifacts.

Sprint 85 is the first implementation sprint in Milestone 17 — Paper Trading Persistence & Audit Foundation. It defines what a future saved paper-trading artifact file should contain without adding writer or reader behavior.

## Delivered Scope

Sprint 85 adds:

- `PAPER_TRADING_ARTIFACT_FILE_NAME`
- `PAPER_TRADING_ARTIFACT_FILE_ENCODING`
- `PAPER_TRADING_ARTIFACT_FILE_TOP_LEVEL_KEYS`
- `create_paper_trading_artifact_file_payload(...)`

The file contract states that a saved paper-trading artifact is expected to be:

- a local JSON document
- encoded as UTF-8
- named `paper_trading_artifact.json`
- represented by the existing `PaperTradingArtifact.to_dict()` payload
- tied to the existing `PAPER_TRADING_ARTIFACT_SCHEMA_VERSION`

## Expected Top-Level Payload Keys

The contract expects these deterministic top-level keys:

```text
schema_version
created_timestamp
starting_account_state
ending_account_state
orders
fills
session_summary
```

## Critical Boundary

Sprint 85 does not write files.

It only prepares a deterministic JSON-compatible dictionary suitable for future file writing. It does not create paths, default output directories, file handles, writer methods, reader methods, persistence workflows, or runtime integrations.

The existing `PaperTradingArtifact` remains an in-memory immutable artifact boundary.

## Out of Scope

Sprint 85 does not add:

- file writing
- file reading
- path creation
- default output directories
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
