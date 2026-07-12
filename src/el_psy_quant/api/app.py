"""FastAPI application construction."""

import os
from pathlib import Path

from fastapi import FastAPI

from el_psy_quant import __version__
from el_psy_quant.api.errors import register_exception_handlers
from el_psy_quant.api.middleware import RequestIdMiddleware
from el_psy_quant.api.routes import api_v1_router

SERVICE_NAME = "el-psy-quant"
RESEARCH_ARTIFACT_ROOT_ENV = "EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT"


def _configured_research_artifact_root(
    override: str | Path | None,
) -> Path | None:
    value = os.getenv(RESEARCH_ARTIFACT_ROOT_ENV) if override is None else override
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return Path(value)


def create_app(
    *,
    research_artifact_root: str | Path | None = None,
) -> FastAPI:
    """Create one independent, side-effect-free local API application."""
    application = FastAPI(
        title=SERVICE_NAME,
        version=__version__,
    )
    application.state.research_artifact_root = _configured_research_artifact_root(
        research_artifact_root
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(api_v1_router)
    return application


app = create_app()
