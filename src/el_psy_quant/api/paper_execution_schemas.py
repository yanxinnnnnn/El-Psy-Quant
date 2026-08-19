"""Strict public schemas for the M34 Paper Execution API boundary."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
)

from el_psy_quant.api.strategy_order_schemas import (
    OrderIntentReferenceResponse,
    PreTradeRiskPolicyReferenceResponse,
)

BoundedId = Annotated[
    StrictStr,
    Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
BoundedActor = Annotated[
    StrictStr,
    Field(min_length=1, max_length=256, pattern=r"^\S(?:.*\S)?$"),
]
Sha256Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
IntentId = Annotated[StrictStr, Field(pattern=r"^oi_[0-9a-f]{64}$")]
DecisionId = Annotated[
    StrictStr, Field(pattern=r"^risk_decision_[0-9a-f]{64}$")
]
ExecutionOrderId = Annotated[
    StrictStr, Field(pattern=r"^peo_[0-9a-f]{64}$")
]
ExecutionAttemptId = Annotated[
    StrictStr, Field(pattern=r"^pea_[0-9a-f]{64}$")
]
ExecutionFillId = Annotated[
    StrictStr, Field(pattern=r"^pef_[0-9a-f]{64}$")
]
CanonicalDecimal = StrictStr
OrderSide = Literal["buy", "sell"]
ReplayStatus = Literal["ready", "running", "paused", "completed"]
OrderStatus = Literal[
    "working",
    "partially_filled",
    "filled",
    "rejected",
    "partially_filled_rejected",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def _normalized_utc(value: object) -> object:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError("timestamp must be a normalized UTC ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        offset = parsed.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            "timestamp must be a normalized UTC ISO-8601 string"
        ) from exc
    if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp must be a normalized UTC ISO-8601 string")
    return parsed.astimezone(timezone.utc)


class PaperExecutionIntentRequest(_StrictModel):
    intent_id: IntentId
    intent_digest: Sha256Digest


class PaperExecutionDecisionRequest(_StrictModel):
    decision_id: DecisionId
    decision_digest: Sha256Digest


class PaperExecutionPolicyRequest(_StrictModel):
    max_fill_quantity_per_trade_event: CanonicalDecimal | None
    slippage_bps: CanonicalDecimal
    commission_bps: CanonicalDecimal
    fee_bps: CanonicalDecimal
    buy_tax_bps: CanonicalDecimal
    sell_tax_bps: CanonicalDecimal


class PaperExecutionOrderCreateRequest(_StrictModel):
    intent: PaperExecutionIntentRequest
    decision: PaperExecutionDecisionRequest
    execution_policy: PaperExecutionPolicyRequest
    actor: BoundedActor


class PaperExecutionOrderStepRequest(_StrictModel):
    execution_order_digest: Sha256Digest
    expected_execution_version: Annotated[StrictInt, Field(ge=0)]
    actor: BoundedActor


class PaperExecutionPolicyReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    policy_id: Literal["paper_execution_v1"]
    execution_price_policy_id: Literal["consumed_trade_event_price_v1"]
    max_fill_quantity_per_trade_event: CanonicalDecimal | None
    slippage_policy_id: Literal["fixed_bps_slippage_v1"]
    slippage_bps: CanonicalDecimal
    transaction_cost_policy_id: Literal["per_fill_bps_costs_v1"]
    commission_bps: CanonicalDecimal
    fee_bps: CanonicalDecimal
    buy_tax_bps: CanonicalDecimal
    sell_tax_bps: CanonicalDecimal
    configuration_digest: Sha256Digest
    reference_digest: Sha256Digest


class PaperExecutionAccountHandoffResponse(_StrictModel):
    schema_version: Literal[1]
    account_id: BoundedId
    base_currency: Annotated[StrictStr, Field(pattern=r"^[A-Z]{3}$")]
    lifecycle_status: Literal["active"]
    account_head_version: Annotated[StrictInt, Field(gt=0)]
    account_head_event_id: BoundedId
    account_head_chain_digest: Sha256Digest
    cash_balance: CanonicalDecimal
    available_cash: CanonicalDecimal
    instrument_id: BoundedId
    current_instrument_quantity: CanonicalDecimal
    reference_digest: Sha256Digest


class PaperExecutionMarketHandoffResponse(_StrictModel):
    schema_version: Literal[1]
    calendar_id: BoundedId
    calendar_version: Annotated[StrictInt, Field(gt=0)]
    trading_session_id: BoundedId
    trading_date: date
    session_open_time: datetime
    session_close_time: datetime
    session_type: StrictStr
    replay_id: BoundedId
    event_stream_digest: Sha256Digest
    cursor_position: Annotated[StrictInt, Field(gt=0)]
    last_event_id: BoundedId
    current_event_time: datetime
    current_event_id: BoundedId
    instrument_id: BoundedId
    handoff_replay_status: Literal["running"]
    reference_digest: Sha256Digest

    _validate_open = field_validator("session_open_time", mode="before")(
        _normalized_utc
    )
    _validate_close = field_validator("session_close_time", mode="before")(
        _normalized_utc
    )
    _validate_current = field_validator("current_event_time", mode="before")(
        _normalized_utc
    )


class PaperExecutionRiskHandoffResponse(_StrictModel):
    schema_version: Literal[1]
    order_intent_reference: OrderIntentReferenceResponse
    risk_decision_id: DecisionId
    risk_decision_digest: Sha256Digest
    risk_snapshot_id: BoundedId
    risk_snapshot_digest: Sha256Digest
    outcome: Literal["allow"]
    risk_policy_reference: PreTradeRiskPolicyReferenceResponse
    reference_digest: Sha256Digest


class PaperExecutionOrderReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest


class PaperExecutionOrderResponse(_StrictModel):
    schema_version: Literal[1]
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    order_intent_reference: OrderIntentReferenceResponse
    risk_handoff_reference: PaperExecutionRiskHandoffResponse
    account_handoff_reference: PaperExecutionAccountHandoffResponse
    market_handoff_reference: PaperExecutionMarketHandoffResponse
    execution_policy_reference: PaperExecutionPolicyReferenceResponse
    account_id: BoundedId
    instrument_id: BoundedId
    side: OrderSide
    requested_quantity: CanonicalDecimal
    origin_command_digest: Sha256Digest
    origin_actor: StrictStr
    created_at: datetime

    _validate_created = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class PaperExecutionOrderStateResponse(_StrictModel):
    schema_version: Literal[1]
    execution_order_reference: PaperExecutionOrderReferenceResponse
    execution_version: Annotated[StrictInt, Field(ge=0)]
    status: OrderStatus
    requested_quantity: CanonicalDecimal
    cumulative_filled_quantity: CanonicalDecimal
    remaining_quantity: CanonicalDecimal
    terminal: bool


class PaperExecutionOrderViewResponse(_StrictModel):
    order: PaperExecutionOrderResponse
    state: PaperExecutionOrderStateResponse


class PaperExecutionReplayCursorResponse(_StrictModel):
    schema_version: Literal[1]
    replay_id: BoundedId
    event_stream_digest: Sha256Digest
    position: Annotated[StrictInt, Field(ge=0)]
    last_event_id: BoundedId | None
    current_event_time: datetime | None
    status: ReplayStatus

    _validate_time = field_validator("current_event_time", mode="before")(
        _normalized_utc
    )


class PaperExecutionEventReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    replay_id: BoundedId
    event_stream_digest: Sha256Digest
    pre_step_cursor_position: Annotated[StrictInt, Field(ge=0)]
    consumed_event_position: Annotated[StrictInt, Field(gt=0)]
    event_id: BoundedId
    event_digest: Sha256Digest
    event_time: datetime
    instrument_id: BoundedId
    event_type: StrictStr
    post_step_cursor_position: Annotated[StrictInt, Field(gt=0)]
    post_step_last_event_id: BoundedId
    post_step_current_event_time: datetime
    post_step_replay_status: ReplayStatus
    reference_digest: Sha256Digest

    _validate_event_time = field_validator("event_time", mode="before")(
        _normalized_utc
    )
    _validate_post_time = field_validator(
        "post_step_current_event_time", mode="before"
    )(_normalized_utc)


class PaperExecutionPriceEvidenceResponse(_StrictModel):
    schema_version: Literal[1]
    execution_price_policy_id: Literal["consumed_trade_event_price_v1"]
    execution_event_reference: PaperExecutionEventReferenceResponse
    side: OrderSide
    base_trade_price: CanonicalDecimal
    slippage_policy_id: Literal["fixed_bps_slippage_v1"]
    slippage_bps: CanonicalDecimal
    pre_round_execution_price: CanonicalDecimal
    execution_price: CanonicalDecimal
    rounding_quantum: CanonicalDecimal
    rounding_mode: StrictStr
    rounding_applied: bool
    price_evidence_digest: Sha256Digest


class PaperExecutionCostEvidenceResponse(_StrictModel):
    schema_version: Literal[1]
    transaction_cost_policy_id: Literal["per_fill_bps_costs_v1"]
    execution_price_evidence: PaperExecutionPriceEvidenceResponse
    fill_quantity: CanonicalDecimal
    gross_notional_pre_round: CanonicalDecimal
    gross_notional: CanonicalDecimal
    gross_notional_rounding_applied: bool
    commission_bps: CanonicalDecimal
    commission_pre_round: CanonicalDecimal
    commission: CanonicalDecimal
    commission_rounding_applied: bool
    fee_bps: CanonicalDecimal
    fee_pre_round: CanonicalDecimal
    fee: CanonicalDecimal
    fee_rounding_applied: bool
    side_tax_bps: CanonicalDecimal
    tax_pre_round: CanonicalDecimal
    tax: CanonicalDecimal
    tax_rounding_applied: bool
    total_charges: CanonicalDecimal
    rounding_quantum: CanonicalDecimal
    rounding_mode: StrictStr
    cost_evidence_digest: Sha256Digest


class PaperExecutionRiskRuleResponse(_StrictModel):
    rule_id: StrictStr
    passed: bool
    reason_code: StrictStr | None
    observed_value: CanonicalDecimal | None
    limit_value: CanonicalDecimal | None


class PaperExecutionRiskRevalidationResponse(_StrictModel):
    schema_version: Literal[1]
    risk_revalidation_id: BoundedId
    risk_revalidation_digest: Sha256Digest
    execution_order_reference: PaperExecutionOrderReferenceResponse
    execution_version: Annotated[StrictInt, Field(ge=0)]
    account_id: BoundedId
    account_head_version: Annotated[StrictInt, Field(gt=0)]
    account_head_event_id: BoundedId
    account_head_chain_digest: Sha256Digest
    available_cash: CanonicalDecimal
    current_instrument_quantity: CanonicalDecimal
    risk_policy_reference: PreTradeRiskPolicyReferenceResponse
    execution_price_evidence: PaperExecutionPriceEvidenceResponse
    cost_evidence: PaperExecutionCostEvidenceResponse
    requested_quantity: CanonicalDecimal
    remaining_quantity_before_step: CanonicalDecimal
    candidate_fill_quantity: CanonicalDecimal
    cumulative_filled_gross_notional: CanonicalDecimal
    projected_notional_pre_round: CanonicalDecimal
    projected_order_gross_notional: CanonicalDecimal
    projected_notional_rounding_applied: bool
    rounding_quantum: CanonicalDecimal
    rounding_mode: StrictStr
    rules: list[PaperExecutionRiskRuleResponse]
    outcome: Literal["allow", "reject"]
    reason_codes: list[StrictStr]


class PaperExecutionAttemptReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    attempt_id: ExecutionAttemptId
    attempt_digest: Sha256Digest


class PaperExecutionAttemptResponse(_StrictModel):
    schema_version: Literal[1]
    attempt_id: ExecutionAttemptId
    attempt_digest: Sha256Digest
    execution_order_reference: PaperExecutionOrderReferenceResponse
    execution_version_before: Annotated[StrictInt, Field(ge=0)]
    execution_version_after: Annotated[StrictInt, Field(gt=0)]
    prior_order_state: PaperExecutionOrderStateResponse
    pre_step_cursor: PaperExecutionReplayCursorResponse
    post_step_cursor: PaperExecutionReplayCursorResponse
    consumed_event_reference: PaperExecutionEventReferenceResponse | None
    attempt_result: Literal[
        "no_fill", "fill", "risk_rejected", "boundary_rejected"
    ]
    no_fill_reason_code: Literal[
        "instrument_mismatch", "event_type_not_trade", "trade_price_invalid"
    ] | None
    terminal_reason_code: Literal[
        "execution_risk_rejected", "replay_exhausted", "session_exhausted"
    ] | None
    risk_revalidation: PaperExecutionRiskRevalidationResponse | None
    created_at: datetime

    _validate_created = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class PaperExecutionFillReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    fill_id: ExecutionFillId
    fill_digest: Sha256Digest


class PaperExecutionFillResponse(_StrictModel):
    schema_version: Literal[1]
    fill_id: ExecutionFillId
    fill_digest: Sha256Digest
    execution_order_reference: PaperExecutionOrderReferenceResponse
    attempt_reference: PaperExecutionAttemptReferenceResponse
    execution_event_reference: PaperExecutionEventReferenceResponse
    side: OrderSide
    fill_quantity: CanonicalDecimal
    execution_price_evidence: PaperExecutionPriceEvidenceResponse
    cost_evidence: PaperExecutionCostEvidenceResponse
    created_at: datetime

    _validate_created = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class PaperExecutionSettlementLinkResponse(_StrictModel):
    schema_version: Literal[1]
    settlement_link_id: BoundedId
    settlement_link_digest: Sha256Digest
    settlement_link_evidence_digest: Sha256Digest
    execution_order_reference: PaperExecutionOrderReferenceResponse
    execution_attempt_reference: PaperExecutionAttemptReferenceResponse
    execution_fill_reference: PaperExecutionFillReferenceResponse
    account_id: BoundedId
    account_event_id: BoundedId
    account_event_digest: Sha256Digest
    account_chain_digest: Sha256Digest
    account_version: Annotated[StrictInt, Field(gt=0)]
    cash_entry_id: BoundedId
    cash_entry_digest: Sha256Digest
    position_entry_id: BoundedId
    position_entry_digest: Sha256Digest


class PaperExecutionCreateResultResponse(_StrictModel):
    order: PaperExecutionOrderResponse
    state: PaperExecutionOrderStateResponse


class PaperExecutionStepResultResponse(_StrictModel):
    schema_version: Literal[1]
    attempt: PaperExecutionAttemptResponse
    fill: PaperExecutionFillResponse | None
    order_state: PaperExecutionOrderStateResponse
    settlement_link: PaperExecutionSettlementLinkResponse | None
    account_event_id: BoundedId | None


class PaperExecutionOrderCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    result: PaperExecutionCreateResultResponse


class PaperExecutionStepCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    result: PaperExecutionStepResultResponse


class PaperExecutionOrderListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperExecutionOrderViewResponse]
    next_cursor: StrictStr | None


class PaperExecutionAttemptListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperExecutionAttemptResponse]
    next_cursor: StrictStr | None


class PaperExecutionFillListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperExecutionFillResponse]
    next_cursor: StrictStr | None


class PaperExecutionReconciliationResponse(_StrictModel):
    schema_version: Literal[1]
    order: PaperExecutionOrderResponse
    state: PaperExecutionOrderStateResponse
    attempts: list[PaperExecutionAttemptResponse]
    fills: list[PaperExecutionFillResponse]
    settlement_links: list[PaperExecutionSettlementLinkResponse]


__all__ = [
    "ExecutionAttemptId",
    "ExecutionFillId",
    "ExecutionOrderId",
    "OrderSide",
    "PaperExecutionAttemptListResponse",
    "PaperExecutionAttemptResponse",
    "PaperExecutionFillListResponse",
    "PaperExecutionFillResponse",
    "PaperExecutionOrderCommandResponse",
    "PaperExecutionOrderCreateRequest",
    "PaperExecutionOrderListResponse",
    "PaperExecutionOrderStepRequest",
    "PaperExecutionOrderViewResponse",
    "PaperExecutionReconciliationResponse",
    "PaperExecutionStepCommandResponse",
]
