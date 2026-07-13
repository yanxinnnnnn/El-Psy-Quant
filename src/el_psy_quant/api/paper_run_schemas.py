"""Explicit paper-run command request and response schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, StrictStr

NumericPrimitive = StrictInt | StrictFloat


class _PaperRunRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaperAccountStateCommandRequest(_PaperRunRequestModel):
    timestamp: StrictStr
    starting_cash: NumericPrimitive
    current_cash: NumericPrimitive
    positions: dict[str, NumericPrimitive]


class PaperOrderCommandRequest(_PaperRunRequestModel):
    order_id: StrictStr
    timestamp: StrictStr
    symbol: StrictStr
    side: StrictStr
    quantity: NumericPrimitive
    status: StrictStr


class PaperFillCommandRequest(_PaperRunRequestModel):
    timestamp: StrictStr
    symbol: StrictStr
    side: StrictStr
    quantity: NumericPrimitive
    price: NumericPrimitive
    order_id: StrictStr | None = None


class PaperRunCommandRequest(_PaperRunRequestModel):
    run_id: StrictStr
    created_timestamp: StrictStr
    starting_account_state: PaperAccountStateCommandRequest
    ending_account_state: PaperAccountStateCommandRequest
    orders: list[PaperOrderCommandRequest]
    fills: list[PaperFillCommandRequest]


class PaperPositionResponse(BaseModel):
    symbol: str
    quantity: float


class PaperAccountStateResponse(BaseModel):
    timestamp: str
    starting_cash: float
    current_cash: float
    positions: list[PaperPositionResponse]


class PaperOrderResponse(BaseModel):
    order_id: str
    timestamp: str
    symbol: str
    side: str
    quantity: float
    status: str


class PaperFillResponse(BaseModel):
    timestamp: str
    symbol: str
    side: str
    quantity: float
    price: float
    order_id: str | None


class PaperPositionChangeResponse(BaseModel):
    symbol: str
    starting_quantity: float
    ending_quantity: float
    quantity_change: float


class PaperSessionSummaryResponse(BaseModel):
    session_start_timestamp: str
    session_end_timestamp: str
    starting_cash: float
    ending_cash: float
    cash_change: float
    starting_positions: list[PaperPositionResponse]
    ending_positions: list[PaperPositionResponse]
    position_changes: list[PaperPositionChangeResponse]
    order_count: int
    fill_count: int


class PaperTradingArtifactResponse(BaseModel):
    schema_version: Literal[1]
    created_timestamp: str
    starting_account_state: PaperAccountStateResponse
    ending_account_state: PaperAccountStateResponse
    orders: list[PaperOrderResponse]
    fills: list[PaperFillResponse]
    session_summary: PaperSessionSummaryResponse


class PaperRunCommandResponse(BaseModel):
    run_id: str
    request_schema_version: Literal[1]
    artifact: PaperTradingArtifactResponse
