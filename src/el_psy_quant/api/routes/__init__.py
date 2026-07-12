"""Versioned API route configuration."""

from fastapi import APIRouter

from el_psy_quant.api.routes.health import router as health_router
from el_psy_quant.api.routes.strategies import router as strategies_router

API_V1_PREFIX = "/api/v1"

api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(health_router)
api_v1_router.include_router(strategies_router)

__all__ = ["API_V1_PREFIX", "api_v1_router"]
