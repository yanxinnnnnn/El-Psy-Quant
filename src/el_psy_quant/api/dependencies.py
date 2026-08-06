"""Explicit reusable composition dependencies for durable local routes."""

from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.application import (
    PaperArtifactRootUnavailableError,
    PaperAccountApplicationService,
    PortfolioReviewArtifactRootUnavailableError,
    StrategyOrderApplicationService,
)
from el_psy_quant.application.paper_jobs import validate_paper_artifact_root
from el_psy_quant.portfolio_review import validate_portfolio_review_artifact_root
from el_psy_quant.persistence.schema import product_schema_is_compatible


def product_database_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="product_database_unavailable",
        message="Product database is unavailable",
    )


def paper_account_schema_incompatible() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="paper_account_schema_incompatible",
        message="Paper Account durable authority is unavailable",
    )


def strategy_order_authority_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="strategy_order_authority_unavailable",
        message="Strategy-to-risk authority is unavailable",
    )


def strategy_order_schema_incompatible() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="strategy_order_schema_incompatible",
        message="Strategy-to-risk schema is incompatible",
    )


def paper_artifact_root_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="paper_artifact_root_unavailable",
        message="Paper artifact root is unavailable",
    )


def portfolio_review_artifact_root_unavailable() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        code="portfolio_review_artifact_root_unavailable",
        message="Portfolio review artifact root is unavailable",
    )


def _product_schema_is_compatible(path: Path) -> bool:
    """Probe the exact durable-route schema through one read-only connection."""
    return product_schema_is_compatible(path)


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


def get_paper_account_session_factory(
    request: Request,
) -> sessionmaker[Session]:
    """Resolve Paper Account storage while distinguishing schema failure."""
    path = getattr(request.app.state, "product_database_path", None)
    factory = getattr(request.app.state, "product_session_factory", None)
    if (
        not isinstance(path, Path)
        or not path.exists()
        or not path.is_file()
        or not isinstance(factory, sessionmaker)
    ):
        raise product_database_unavailable()
    try:
        if not _product_schema_is_compatible(path):
            raise paper_account_schema_incompatible()
    except PublicApiError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise paper_account_schema_incompatible() from exc
    return factory


def get_paper_account_application_service(
    request: Request,
    session_factory: Annotated[
        sessionmaker[Session],
        Depends(get_paper_account_session_factory),
    ],
) -> PaperAccountApplicationService:
    """Construct one request-scoped service over explicit durable authority."""
    evidence_root = getattr(request.app.state, "evidence_artifact_root", None)
    return PaperAccountApplicationService(
        session_factory=session_factory,
        portfolio_review_artifact_root=(
            evidence_root if isinstance(evidence_root, Path) else None
        ),
        portfolio_review_session_factory=session_factory,
    )


def get_strategy_order_session_factory(
    request: Request,
) -> sessionmaker[Session]:
    """Resolve M33 storage while preserving availability/schema boundaries."""
    path = getattr(request.app.state, "product_database_path", None)
    factory = getattr(request.app.state, "product_session_factory", None)
    try:
        storage_available = (
            isinstance(path, Path)
            and path.exists()
            and path.is_file()
            and isinstance(factory, sessionmaker)
        )
    except OSError as exc:
        raise strategy_order_authority_unavailable() from exc
    if not storage_available:
        raise strategy_order_authority_unavailable()
    try:
        if not _product_schema_is_compatible(path):
            raise strategy_order_schema_incompatible()
    except PublicApiError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise strategy_order_schema_incompatible() from exc
    return factory


def get_strategy_order_application_service(
    session_factory: Annotated[
        sessionmaker[Session],
        Depends(get_strategy_order_session_factory),
    ],
) -> StrategyOrderApplicationService:
    """Construct one explicit request-scoped M33 application service."""
    return StrategyOrderApplicationService(session_factory=session_factory)


def get_server_utc_timestamp() -> datetime:
    """Return one server-owned normalized UTC command audit timestamp."""
    return datetime.now(timezone.utc)


def get_paper_artifact_root(request: Request) -> Path:
    """Return one validated existing server-owned paper root."""
    root = getattr(request.app.state, "paper_artifact_root", None)
    if root is None:
        raise paper_artifact_root_unavailable()
    try:
        return validate_paper_artifact_root(root)
    except PaperArtifactRootUnavailableError as exc:
        raise paper_artifact_root_unavailable() from exc


def get_portfolio_review_artifact_root(request: Request) -> Path:
    """Return the validated existing evidence root for portfolio reviews."""
    root = getattr(request.app.state, "evidence_artifact_root", None)
    if root is None:
        raise portfolio_review_artifact_root_unavailable()
    try:
        return validate_portfolio_review_artifact_root(root)
    except PortfolioReviewArtifactRootUnavailableError as exc:
        raise portfolio_review_artifact_root_unavailable() from exc
