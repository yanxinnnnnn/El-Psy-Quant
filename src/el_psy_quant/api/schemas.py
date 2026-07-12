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
