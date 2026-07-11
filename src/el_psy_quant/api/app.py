"""FastAPI application construction."""

from importlib.metadata import version

from fastapi import FastAPI

from el_psy_quant.api.errors import register_exception_handlers
from el_psy_quant.api.middleware import RequestIdMiddleware
from el_psy_quant.api.routes import api_v1_router

SERVICE_NAME = "el-psy-quant"


def create_app() -> FastAPI:
    """Create one independent, side-effect-free local API application."""
    application = FastAPI(
        title=SERVICE_NAME,
        version=version("el-psy-quant"),
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(api_v1_router)
    return application


app = create_app()
