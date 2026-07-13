# Sprint 146 — Artifact Index and Product Repository Foundation

## Status

Complete.

## Objective

Add the smallest compact and rebuildable product index for the authoritative
research and evidence manifests delivered before Milestone 27, without copying
their payloads or beginning durable paper-job control.

## Delivered Chain

```text
authoritative research/evidence list readers
  -> immutable six-field index entries
  -> explicit multi-root discovery
  -> one caller-owned SQLAlchemy transaction
  -> root-isolated repository replacement
  -> compact database-only reads
```

## Indexed Artifact Contract

Exactly four artifact types are supported:

| Artifact type | Root | Artifact key | Relative path | Source ID |
|---|---|---|---|---|
| `research_run_manifest` | `research` | `<experiment_slug>/<run_id>` | `<experiment_slug>/<run_id>/manifest.json` | normalized run ID |
| `strategy_decision_manifest` | `evidence` | filename key | `strategy-decisions/<key>.json` | normalized manifest ID |
| `report_artifact_manifest` | `evidence` | filename key | `report-artifacts/<key>.json` | normalized manifest ID |
| `strategy_review_workflow_manifest` | `evidence` | filename key | `strategy-review/<key>.json` | normalized manifest ID |

`ArtifactIndexEntry` is frozen and stores only record schema version `1`, type,
key, root type, normalized POSIX relative path, and source ID. Evidence filename
keys remain distinct from normalized domain manifest IDs.

## Migration and Repository

Alembic revision `0002_artifact_index` follows the unchanged
`0001_product_baseline` and creates only `artifact_index_entries`. The composite
primary key is `(artifact_type, artifact_key)` and `(root_type, relative_path)`
is unique. Database checks enforce schema version, supported types and roots,
and the exact type-to-root mapping. Downgrade removes only this table.

`SqlAlchemyArtifactIndexRepository` receives a caller-owned `Session`. It never
commits, rolls back, or closes it. Replacement affects one selected root,
removes stale rows, preserves the other root, treats a supplied empty tuple as
a clear operation, and is repeatable without duplicates.

## Refresh and Read Services

`refresh_artifact_index(...)` accepts explicitly supplied research and/or
evidence roots. It uses only `list_research_runs(...)` and
`list_evidence_manifests(...)`; it does not parse JSON independently. All
supplied-root discovery completes before the session is opened. Replacements
then occur in one transaction, so discovery or database failure leaves the
previous index intact. Omitted roots are untouched and supplied empty roots are
cleared. Refresh never runs during import, application startup, migration, or an
API request unless a future sprint explicitly composes it.

`list_indexed_artifacts(...)` and `get_indexed_artifact(...)` query only the
repository. They do not open, resolve, or return artifact payloads.

## Explicit Local Use

Ensure the database parent exists and migrate explicitly:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\product.sqlite3"
uv run alembic upgrade head
```

Then compose engine, session factory, and refresh in Python:

```python
from el_psy_quant.application import list_indexed_artifacts, refresh_artifact_index
from el_psy_quant.persistence import (
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)

engine = create_product_database_engine(config=resolve_product_database_config())
sessions = create_product_session_factory(engine=engine)
refresh_artifact_index(
    session_factory=sessions,
    research_artifact_root=r"C:\path\to\research",
    evidence_artifact_root=r"C:\path\to\evidence",
)
entries = list_indexed_artifacts(session_factory=sessions)
```

## Preserved Boundaries

Artifact files remain authoritative. SQLite stores no complete artifact payload,
absolute artifact root, mutable lifecycle current state, paper-job status,
orders, fills, credentials, or authentication data. Sprint 146 adds no API
route, automatic refresh, paper-job submission or record, worker, queue,
scheduler, retry, recovery, idempotency behavior, Web UI, broker, QMT, live
execution, or capital behavior.

## Verification

Tests cover the immutable contract and exact layouts, migration order and
constraints, caller-owned transactions and rollback, root isolation and stale
cleanup, real-reader refresh, atomic multi-root failure, idempotency, unchanged
artifact bytes, and database-only reads. The complete quality gate is:

```text
uv run python scripts/check.py
```

## Next Sprint

```text
Sprint 147 — Durable Paper Job Record and Submission Foundation
```
