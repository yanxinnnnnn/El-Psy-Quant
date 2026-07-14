"""Versioned API route configuration."""

from fastapi import APIRouter

from el_psy_quant.api.routes.evidence_manifests import (
    router as evidence_manifests_router,
)
from el_psy_quant.api.routes.health import router as health_router
from el_psy_quant.api.routes.lifecycle_commands import (
    router as lifecycle_commands_router,
)
from el_psy_quant.api.routes.paper_runs import router as paper_runs_router
from el_psy_quant.api.routes.paper_jobs import router as paper_jobs_router
from el_psy_quant.api.routes.research_runs import router as research_runs_router
from el_psy_quant.api.routes.strategies import router as strategies_router

API_V1_PREFIX = "/api/v1"

api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(evidence_manifests_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(lifecycle_commands_router)
api_v1_router.include_router(paper_runs_router)
api_v1_router.include_router(paper_jobs_router)
api_v1_router.include_router(research_runs_router)
api_v1_router.include_router(strategies_router)

__all__ = ["API_V1_PREFIX", "api_v1_router"]
