"""Versioned built-in strategy catalog routes."""

from fastapi import APIRouter, HTTPException

from el_psy_quant.api.schemas import (
    StrategyDetailResponse,
    StrategyListResponse,
    StrategyParameterResponse,
    StrategySummaryResponse,
)
from el_psy_quant.application import (
    StrategyDetail,
    StrategyNotFoundError,
    StrategySummary,
    get_strategy_detail,
    list_strategies,
)

router = APIRouter(prefix="/strategies")


def _summary_response(summary: StrategySummary) -> StrategySummaryResponse:
    return StrategySummaryResponse(
        name=summary.name,
        display_name=summary.display_name,
        description=summary.description,
    )


def _detail_response(detail: StrategyDetail) -> StrategyDetailResponse:
    return StrategyDetailResponse(
        name=detail.name,
        display_name=detail.display_name,
        description=detail.description,
        parameters=[
            StrategyParameterResponse(
                name=parameter.name,
                value_type=parameter.value_type,
                required=parameter.required,
                default=parameter.default,
            )
            for parameter in detail.parameters
        ],
    )


@router.get("", response_model=StrategyListResponse)
async def get_strategies() -> StrategyListResponse:
    """List descriptive metadata for built-in supported strategies."""
    return StrategyListResponse(
        strategies=[_summary_response(summary) for summary in list_strategies()]
    )


@router.get("/{strategy_name}", response_model=StrategyDetailResponse)
async def get_strategy(strategy_name: str) -> StrategyDetailResponse:
    """Return descriptive metadata for one exact built-in strategy name."""
    try:
        detail = get_strategy_detail(strategy_name)
    except StrategyNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    return _detail_response(detail)
