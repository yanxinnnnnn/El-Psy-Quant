# Sprint 145 — SQLite and SQLAlchemy Product Persistence Foundation

## Status

Complete.

## Objective

Start Milestone 27 with the smallest explicit local SQLite and SQLAlchemy
persistence foundation needed by later product repositories and durable
paper-job control.

## Delivered Chain

```text
explicit local database path
  -> SQLite SQLAlchemy engine
  -> product declarative metadata boundary
  -> caller-owned session factory
  -> Alembic environment and empty baseline
  -> focused tests and documentation
```

## Configuration Contract

The database is one local SQLite file selected by:

```text
EL_PSY_QUANT_PRODUCT_DATABASE_PATH
```

An explicit function argument may override the environment value for tests and
future composition. Missing values, blank values, generic database URLs, and
existing directory paths are rejected. Resolution normalizes through
`pathlib.Path` and creates no files or directories.

## SQLAlchemy Foundation

`ProductPersistenceBase` is the project-owned SQLAlchemy 2.x metadata registry
for future product persistence models. Sprint 145 maps no business models.

`create_product_database_engine(...)` constructs a lazy SQLite engine. It opens
no connection and creates no schema merely by being constructed. SQLite foreign
keys are enabled for every connection. `check_same_thread=False` supports future
FastAPI composition, but connections and sessions must not be shared
concurrently; each unit of work owns its own session.

`create_product_session_factory(...)` returns a new SQLAlchemy session factory.
Callers explicitly create, commit or roll back, and close sessions. There is no
global engine, global session, hidden auto-commit, repository, or speculative
unit-of-work framework.

## Migration Discipline

Alembic owns production schema changes. The baseline revision is intentionally
empty: upgrading a fresh database creates only Alembic version tracking, and
downgrading to `base` is deterministic.

Ensure the configured parent directory exists, then run:

```powershell
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="C:\path\to\el-psy-quant-product.sqlite3"
uv run alembic upgrade head
```

Migrations do not run during import or FastAPI startup, and production schema
management does not use `Base.metadata.create_all()`.

## Verification

Focused tests cover:

- explicit configuration precedence, validation, and side-effect freedom
- import and engine-construction side effects
- SQLite foreign-key enforcement on independent connections
- separate caller-owned sessions, explicit commit visibility, and rollback
- fresh upgrade to the baseline, exact revision tracking, no business tables,
  deterministic downgrade, and working-directory independence
- unchanged application construction and health behavior without database config

The complete project quality gate is:

```text
uv run python scripts/check.py
```

## Preserved Boundaries

Sprint 145 does not add artifact discovery or indexing, product repositories,
artifact payload duplication, paper-job tables or behavior, workers, job APIs,
request-scoped database dependencies, lifecycle current-state storage, Web UI,
broker or QMT integration, live execution, or capital behavior.

Existing artifact files remain authoritative. Lifecycle current state remains a
future derived read model. Future paper-job operational state remains separate
from lifecycle governance.

## Next Sprint

```text
Sprint 146 — Artifact Index and Product Repository Foundation
```
