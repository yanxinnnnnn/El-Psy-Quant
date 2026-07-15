"""FastAPI application construction."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from el_psy_quant import __version__
from el_psy_quant.api.auth import resolve_founder_auth_config
from el_psy_quant.api.errors import register_exception_handlers
from el_psy_quant.api.middleware import RequestIdMiddleware
from el_psy_quant.api.routes import api_v1_router
from el_psy_quant.persistence import (
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)

SERVICE_NAME = "el-psy-quant"
RESEARCH_ARTIFACT_ROOT_ENV = "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT"
EVIDENCE_ARTIFACT_ROOT_ENV = "EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT"
PRODUCT_DATABASE_PATH_ENV = "EL_PSY_QUANT_PRODUCT_DATABASE_PATH"
PAPER_ARTIFACT_ROOT_ENV = "EL_PSY_QUANT_PAPER_ARTIFACT_ROOT"


def _configured_artifact_root(
    environment_name: str,
    override: str | Path | None,
) -> Path | None:
    value = os.getenv(environment_name) if override is None else override
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return Path(value)


def create_app(
    *,
    research_artifact_root: str | Path | None = None,
    evidence_artifact_root: str | Path | None = None,
    product_database_path: str | Path | None = None,
    paper_artifact_root: str | Path | None = None,
    founder_username: str | None = None,
    founder_password: str | None = None,
) -> FastAPI:
    """Create one independent, side-effect-free local API application."""
    configured_database_path = _configured_artifact_root(
        PRODUCT_DATABASE_PATH_ENV, product_database_path
    )
    engine = None
    session_factory = None
    if configured_database_path is not None:
        try:
            config = resolve_product_database_config(
                database_path=configured_database_path
            )
            configured_database_path = config.database_path
            engine = create_product_database_engine(config=config)
            session_factory = create_product_session_factory(engine=engine)
        except (OSError, RuntimeError, ValueError):
            engine = None
            session_factory = None

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()

    application = FastAPI(
        title=SERVICE_NAME,
        version=__version__,
        lifespan=lifespan,
    )
    application.state.research_artifact_root = _configured_artifact_root(
        RESEARCH_ARTIFACT_ROOT_ENV, research_artifact_root
    )
    application.state.evidence_artifact_root = _configured_artifact_root(
        EVIDENCE_ARTIFACT_ROOT_ENV, evidence_artifact_root
    )
    application.state.product_database_path = configured_database_path
    application.state.paper_artifact_root = _configured_artifact_root(
        PAPER_ARTIFACT_ROOT_ENV, paper_artifact_root
    )
    application.state.founder_auth = resolve_founder_auth_config(
        username=founder_username,
        password=founder_password,
    )
    application.state.product_database_engine = engine
    application.state.product_session_factory = session_factory
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(api_v1_router)
    return application


app = create_app()
