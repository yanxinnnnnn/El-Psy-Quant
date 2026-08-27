"""Versioned API route configuration."""

from fastapi import APIRouter, Depends

from el_psy_quant.api.auth import require_founder_auth
from el_psy_quant.api.routes.demo_workspace import router as demo_workspace_router
from el_psy_quant.api.routes.evidence_manifests import (
    router as evidence_manifests_router,
)
from el_psy_quant.api.routes.health import router as health_router
from el_psy_quant.api.routes.lifecycle_commands import (
    router as lifecycle_commands_router,
)
from el_psy_quant.api.routes.market_time import router as market_time_router
from el_psy_quant.api.routes.paper_runs import router as paper_runs_router
from el_psy_quant.api.routes.paper_execution import router as paper_execution_router
from el_psy_quant.api.routes.paper_accounts import (
    router as paper_accounts_router,
)
from el_psy_quant.api.routes.paper_jobs import router as paper_jobs_router
from el_psy_quant.api.routes.paper_runtimes import router as paper_runtimes_router
from el_psy_quant.api.routes.portfolio_reviews import (
    router as portfolio_reviews_router,
)
from el_psy_quant.api.routes.research_runs import router as research_runs_router
from el_psy_quant.api.routes.strategies import router as strategies_router
from el_psy_quant.api.routes.strategy_order import router as strategy_order_router

API_V1_PREFIX = "/api/v1"

api_v1_router = APIRouter(
    prefix=API_V1_PREFIX,
    dependencies=[Depends(require_founder_auth)],
)
api_v1_router.include_router(demo_workspace_router)
api_v1_router.include_router(evidence_manifests_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(lifecycle_commands_router)
api_v1_router.include_router(market_time_router)
api_v1_router.include_router(paper_runs_router)
api_v1_router.include_router(paper_execution_router)
api_v1_router.include_router(paper_accounts_router)
api_v1_router.include_router(paper_jobs_router)
api_v1_router.include_router(paper_runtimes_router)
api_v1_router.include_router(portfolio_reviews_router)
api_v1_router.include_router(research_runs_router)
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(strategy_order_router)

__all__ = ["API_V1_PREFIX", "api_v1_router"]
