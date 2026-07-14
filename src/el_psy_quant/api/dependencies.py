"""Explicit reusable composition dependencies for durable local routes."""

from http import HTTPStatus
from pathlib import Path

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.application import PaperArtifactRootUnavailableError
from el_psy_quant.application.paper_jobs import validate_paper_artifact_root


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


def get_product_session_factory(request: Request) -> sessionmaker[Session]:
    """Return a factory only when the configured migrated file can be opened later."""
    path = getattr(request.app.state, "product_database_path", None)
    factory = getattr(request.app.state, "product_session_factory", None)
    try:
        available = (
            isinstance(path, Path)
            and path.exists()
            and path.is_file()
            and isinstance(factory, sessionmaker)
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
