"""Read-only contract for the one supported product database schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

CURRENT_PRODUCT_SCHEMA_REVISION = "0005_paper_job_result_references"
APPROVED_PRODUCT_SCHEMA_REVISIONS = (
    "0001_product_baseline",
    "0002_artifact_index",
    "0003_paper_jobs",
    "0004_paper_job_recovery_audit",
    CURRENT_PRODUCT_SCHEMA_REVISION,
)

REQUIRED_PRODUCT_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_index_entries": (
        "record_schema_version",
        "artifact_type",
        "artifact_key",
        "root_type",
        "relative_path",
        "source_id",
    ),
    "paper_jobs": (
        "record_schema_version",
        "job_id",
        "run_id",
        "status",
        "request_schema_version",
        "request_payload",
        "submitted_timestamp",
        "updated_timestamp",
    ),
    "paper_job_submission_keys": (
        "record_schema_version",
        "idempotency_key",
        "job_id",
        "request_schema_version",
        "request_digest",
        "created_timestamp",
    ),
    "paper_job_attempts": (
        "record_schema_version",
        "attempt_id",
        "job_id",
        "attempt_number",
        "status",
        "started_timestamp",
        "completed_timestamp",
        "error_code",
    ),
    "paper_job_result_references": (
        "record_schema_version",
        "job_id",
        "root_type",
        "artifact_schema_version",
        "result_summary_schema_version",
        "artifact_relative_path",
        "result_summary_relative_path",
        "created_timestamp",
    ),
}


class ProductSchemaVerificationError(Exception):
    """Raised when a product database cannot satisfy the read-only contract."""


def _read_only_connection(database_path: Path) -> sqlite3.Connection:
    try:
        resolved = database_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ProductSchemaVerificationError(
            "product database is unavailable"
        ) from exc
    if database_path.is_symlink() or not resolved.is_file():
        raise ProductSchemaVerificationError(
            "product database must be an existing real file"
        )
    try:
        return sqlite3.connect(
            f"{resolved.as_uri()}?mode=ro",
            uri=True,
            timeout=1.0,
        )
    except sqlite3.Error as exc:
        raise ProductSchemaVerificationError(
            "product database is not readable"
        ) from exc


def _read_product_schema_revision(connection: sqlite3.Connection) -> str:
    try:
        revisions = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall()
    except sqlite3.Error as exc:
        raise ProductSchemaVerificationError(
            "product database revision is unavailable"
        ) from exc
    if len(revisions) != 1:
        raise ProductSchemaVerificationError(
            "product database must contain exactly one revision"
        )
    revision = revisions[0][0]
    if (
        not isinstance(revision, str)
        or revision not in APPROVED_PRODUCT_SCHEMA_REVISIONS
    ):
        raise ProductSchemaVerificationError(
            "product database revision is not recognized"
        )
    return revision


def read_product_schema_revision(database_path: str | Path) -> str:
    """Read exactly one approved product revision without changing the database."""
    if not isinstance(database_path, (str, Path)):
        raise ProductSchemaVerificationError(
            "product database path must be a local file path"
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = _read_only_connection(Path(database_path))
        return _read_product_schema_revision(connection)
    except ProductSchemaVerificationError:
        raise
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        raise ProductSchemaVerificationError(
            "product database revision verification failed"
        ) from exc
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database revision verification failed"
                ) from exc


def verify_product_schema(database_path: str | Path) -> str:
    """Verify the exact current revision and API-required schema without writes."""
    if not isinstance(database_path, (str, Path)):
        raise ProductSchemaVerificationError(
            "product database path must be a local file path"
        )
    connection: sqlite3.Connection | None = None
    try:
        connection = _read_only_connection(Path(database_path))
        revision = _read_product_schema_revision(connection)
        if revision != CURRENT_PRODUCT_SCHEMA_REVISION:
            raise ProductSchemaVerificationError(
                "product database revision does not match the current revision"
            )

        for table_name, expected_columns in REQUIRED_PRODUCT_TABLE_COLUMNS.items():
            try:
                columns = tuple(
                    row[1]
                    for row in connection.execute(
                        f'PRAGMA table_info("{table_name}")'
                    ).fetchall()
                )
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database schema is incompatible"
                ) from exc
            if columns != expected_columns:
                raise ProductSchemaVerificationError(
                    "product database schema is incompatible"
                )
        return CURRENT_PRODUCT_SCHEMA_REVISION
    except ProductSchemaVerificationError:
        raise
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as exc:
        raise ProductSchemaVerificationError(
            "product database verification failed"
        ) from exc
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as exc:
                raise ProductSchemaVerificationError(
                    "product database verification failed"
                ) from exc


def product_schema_is_compatible(database_path: str | Path) -> bool:
    """Return whether one existing database satisfies the exact read-only contract."""
    try:
        verify_product_schema(database_path)
    except ProductSchemaVerificationError:
        return False
    return True


__all__ = [
    "APPROVED_PRODUCT_SCHEMA_REVISIONS",
    "CURRENT_PRODUCT_SCHEMA_REVISION",
    "ProductSchemaVerificationError",
    "REQUIRED_PRODUCT_TABLE_COLUMNS",
    "product_schema_is_compatible",
    "read_product_schema_revision",
    "verify_product_schema",
]
