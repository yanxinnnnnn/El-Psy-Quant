"""Explicit research-run artifact inspection response schemas."""

from typing import Literal

from pydantic import BaseModel


class ResearchRunSummaryResponse(BaseModel):
    experiment_slug: str
    run_id: str
    experiment_name: str
    strategy: str
    data_source: Literal["csv", "cache"]
    symbols: list[str]


class ResearchRunListResponse(BaseModel):
    runs: list[ResearchRunSummaryResponse]


class ResearchRunDataResponse(BaseModel):
    source: Literal["csv", "cache"]
    symbols: list[str]


class ResearchRunParametersResponse(BaseModel):
    fast_window: int
    slow_window: int
    initial_capital: float
    transaction_cost_rate: float
    slippage_rate: float


class ResearchRunEvaluationResponse(BaseModel):
    periods_per_year: float | None
    annual_risk_free_rate: float


class ResearchArtifactReferencesResponse(BaseModel):
    config: str
    metadata: str
    summary: str
    metrics: str
    logs_dir: str


class ResearchMetricRecordResponse(BaseModel):
    symbol: str
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    periods: float
    cagr: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None


class ResearchRunDetailResponse(BaseModel):
    manifest_schema_version: Literal[1]
    metrics_schema_version: Literal[1]
    experiment_slug: str
    run_id: str
    experiment_name: str
    strategy: str
    data: ResearchRunDataResponse
    parameters: ResearchRunParametersResponse
    evaluation: ResearchRunEvaluationResponse
    artifacts: ResearchArtifactReferencesResponse
    metrics: list[ResearchMetricRecordResponse]
