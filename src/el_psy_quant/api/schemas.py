"""Explicit API response schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Local application-process health response."""

    status: Literal["ok"]
    service: Literal["el-psy-quant"]
    api_version: Literal["v1"]


class ApiError(BaseModel):
    """Stable public error detail."""

    code: str
    message: str


class ApiErrorResponse(BaseModel):
    """Stable public error envelope with request correlation."""

    error: ApiError
    request_id: str


class StrategyParameterResponse(BaseModel):
    """Descriptive strategy parameter metadata."""

    name: str
    value_type: Literal["integer", "number"]
    required: bool
    default: int | float | None


class StrategySummaryResponse(BaseModel):
    """Built-in strategy list item."""

    name: str
    display_name: str
    description: str


class StrategyDetailResponse(StrategySummaryResponse):
    """Built-in strategy detail response."""

    parameters: list[StrategyParameterResponse]


class StrategyListResponse(BaseModel):
    """Deterministically ordered built-in strategy list."""

    strategies: list[StrategySummaryResponse]
