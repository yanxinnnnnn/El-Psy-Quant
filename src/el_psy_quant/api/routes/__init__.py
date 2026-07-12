"""Versioned API route configuration."""

from fastapi import APIRouter

from el_psy_quant.api.routes.health import router as health_router

API_V1_PREFIX = "/api/v1"

api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(health_router)

__all__ = ["API_V1_PREFIX", "api_v1_router"]
