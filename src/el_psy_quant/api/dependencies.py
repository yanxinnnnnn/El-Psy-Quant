"""Explicit reusable composition dependencies for durable local routes."""

import sqlite3
from http import HTTPStatus
from pathlib import Path

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.application import PaperArtifactRootUnavailableError
from el_psy_quant.application.paper_jobs import validate_paper_artifact_root

PRODUCT_SCHEMA_REVISION = "0005_paper_job_result_references"
_REQUIRED_PRODUCT_SCHEMA_PROBES = (
    "SELECT job_id, status, request_payload, updated_timestamp "
    "FROM paper_jobs LIMIT 0",
    "SELECT idempotency_key, job_id, request_digest "
    "FROM paper_job_submission_keys LIMIT 0",
    "SELECT attempt_id, job_id, attempt_number, status, completed_timestamp, "
    "error_code FROM paper_job_attempts LIMIT 0",
    "SELECT job_id, root_type, artifact_relative_path, "
    "result_summary_relative_path FROM paper_job_result_references LIMIT 0",
)


def product_database_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="product_database_unavailable",
        message="Product database is unavailable",
    )


def paper_artifact_root_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="paper_artifact_root_unavailable",
        message="Paper artifact root is unavailable",
    )


def _product_schema_is_compatible(path: Path) -> bool:
    """Probe the exact durable-route schema through one read-only connection."""
    connection: sqlite3.Connection | None = None
    compatible = False
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_file():
            return False
        connection = sqlite3.connect(
            f"{resolved.as_uri()}?mode=ro",
            uri=True,
            timeout=1.0,
        )
        revisions = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall()
        if revisions != [(PRODUCT_SCHEMA_REVISION,)]:
            return False
        for statement in _REQUIRED_PRODUCT_SCHEMA_PROBES:
            connection.execute(statement).fetchall()
        compatible = True
    except (OSError, RuntimeError, sqlite3.Error, ValueError):
        compatible = False
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                compatible = False
    return compatible


def get_product_session_factory(request: Request) -> sessionmaker[Session]:
    """Return a factory only after a closed, read-only schema preflight."""
    path = getattr(request.app.state, "product_database_path", None)
    factory = getattr(request.app.state, "product_session_factory", None)
    try:
        available = (
            isinstance(path, Path)
            and path.exists()
            and path.is_file()
            and isinstance(factory, sessionmaker)
            and _product_schema_is_compatible(path)
        )
    except OSError:
        available = False
    if not available:
        raise product_database_unavailable()
    return factory


def get_paper_artifact_root(request: Request) -> Path:
    """Return one validated existing server-owned paper root."""
    root = getattr(request.app.state, "paper_artifact_root", None)
    if root is None:
        raise paper_artifact_root_unavailable()
    try:
        return validate_paper_artifact_root(root)
    except PaperArtifactRootUnavailableError as exc:
        raise paper_artifact_root_unavailable() from exc
