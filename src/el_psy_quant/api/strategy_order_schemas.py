"""Strict public schemas for the M33 strategy-to-risk API boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
)

ExactPositiveInt = Annotated[StrictInt, Field(gt=0)]
BoundedId = Annotated[
    StrictStr,
    Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
BoundedStrategyName = Annotated[
    StrictStr,
    Field(min_length=1, max_length=128, pattern=r"^\S(?:.*\S)?$"),
]
BoundedActor = Annotated[
    StrictStr,
    Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
Sha256Digest = Annotated[
    StrictStr,
    Field(pattern=r"^[0-9a-f]{64}$"),
]
SignalId = Annotated[
    StrictStr,
    Field(pattern=r"^sig_[0-9a-f]{64}$"),
]
IntentId = Annotated[
    StrictStr,
    Field(pattern=r"^oi_[0-9a-f]{64}$"),
]
DecisionId = Annotated[
    StrictStr,
    Field(pattern=r"^risk_decision_[0-9a-f]{64}$"),
]
NoActionId = Annotated[
    StrictStr,
    Field(pattern=r"^no_action_[0-9a-f]{64}$"),
]
RiskInputId = Annotated[
    StrictStr,
    Field(pattern=r"^risk_input_[0-9a-f]{64}$"),
]
CanonicalDecimal = StrictStr
OrderSide = Literal["buy", "sell"]
RiskOutcome = Literal["allow", "reject"]
RiskRuleCode = Literal[
    "insufficient_position_quantity",
    "maximum_order_quantity_exceeded",
    "maximum_order_notional_exceeded",
    "insufficient_available_cash",
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
    if (
        parsed.tzinfo is None
        or offset is None
        or offset.total_seconds() != 0
    ):
        raise ValueError("timestamp must be a normalized UTC ISO-8601 string")
    return parsed.astimezone(timezone.utc)


class MovingAverageRuntimeRequest(_StrictModel):
    strategy_name: Literal["moving_average_crossover"]
    strategy_version: Literal["v1"]
    adapter_version: Literal["v1"]
    runtime_sizing_semantics: Literal["target_position_quantity"]
    fast_window: ExactPositiveInt
    slow_window: ExactPositiveInt
    target_position_quantity: CanonicalDecimal


class StrategySignalMarketRequest(_StrictModel):
    calendar_id: BoundedId
    expected_calendar_version: ExactPositiveInt
    trading_session_id: BoundedId
    replay_id: BoundedId
    expected_event_stream_digest: Sha256Digest
    expected_cursor_position: ExactPositiveInt
    expected_signal_event_id: BoundedId
    expected_signal_time_utc: datetime | None = None
    instrument_id: BoundedId

    _validate_expected_signal_time = field_validator(
        "expected_signal_time_utc", mode="before"
    )(_normalized_utc)


class StrategySignalEvaluateRequest(_StrictModel):
    runtime: MovingAverageRuntimeRequest
    market: StrategySignalMarketRequest
    actor: BoundedActor


class StrategyRuntimeParametersResponse(_StrictModel):
    fast_window: ExactPositiveInt
    slow_window: ExactPositiveInt
    target_position_quantity: CanonicalDecimal


class StrategyRuntimeReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    strategy_name: Literal["moving_average_crossover"]
    strategy_version: Literal["v1"]
    adapter_version: Literal["v1"]
    runtime_sizing_semantics: Literal["target_position_quantity"]
    parameters: StrategyRuntimeParametersResponse
    parameters_digest: Sha256Digest
    reference_digest: Sha256Digest


class StrategySignalMarketReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    calendar_id: BoundedId
    calendar_version: ExactPositiveInt
    trading_session_id: BoundedId
    replay_id: BoundedId
    event_stream_digest: Sha256Digest
    cursor_position: ExactPositiveInt
    last_event_id: BoundedId
    signal_event_id: BoundedId
    signal_time: datetime
    instrument_id: BoundedId
    reference_digest: Sha256Digest

    _validate_signal_time = field_validator("signal_time", mode="before")(
        _normalized_utc
    )


class StrategySignalResponse(_StrictModel):
    schema_version: Literal[1]
    signal_id: SignalId
    signal_digest: Sha256Digest
    strategy_runtime_reference: StrategyRuntimeReferenceResponse
    market_reference: StrategySignalMarketReferenceResponse
    target_semantics: Literal["target_position_quantity"]
    target_position_quantity: CanonicalDecimal
    created_at: datetime

    _validate_created_at = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class StrategySignalCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    signal: StrategySignalResponse


class StrategySignalListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[StrategySignalResponse]
    next_cursor: StrictStr | None


class OrderIntentAccountRequest(_StrictModel):
    account_id: BoundedId
    expected_account_head_version: ExactPositiveInt
    expected_account_head_event_id: BoundedId
    expected_account_head_chain_digest: Sha256Digest


class OrderIntentCreateRequest(_StrictModel):
    signal_id: SignalId
    account: OrderIntentAccountRequest
    intent_policy_version: Literal["target_position_quantity_delta_v1"]
    actor: BoundedActor


class StrategySignalReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    signal_id: SignalId
    signal_digest: Sha256Digest


class OrderIntentAccountReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    account_id: BoundedId
    base_currency: Annotated[StrictStr, Field(pattern=r"^[A-Z]{3}$")]
    lifecycle_status: Literal["active"]
    account_head_version: ExactPositiveInt
    account_head_event_id: BoundedId
    account_head_chain_digest: Sha256Digest
    cash_balance: CanonicalDecimal
    available_cash: CanonicalDecimal
    instrument_id: BoundedId
    current_instrument_quantity: CanonicalDecimal
    reference_digest: Sha256Digest


class OrderIntentResponse(_StrictModel):
    schema_version: Literal[1]
    intent_id: IntentId
    intent_digest: Sha256Digest
    signal_reference: StrategySignalReferenceResponse
    market_reference: StrategySignalMarketReferenceResponse
    account_reference: OrderIntentAccountReferenceResponse
    target_semantics: Literal["target_position_quantity"]
    target_position_quantity: CanonicalDecimal
    current_position_quantity: CanonicalDecimal
    side: OrderSide
    requested_quantity: CanonicalDecimal
    intent_policy_version: Literal["target_position_quantity_delta_v1"]
    origin_command_digest: Sha256Digest
    origin_actor: StrictStr
    created_at: datetime

    _validate_created_at = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class OrderIntentNoActionResponse(_StrictModel):
    schema_version: Literal[1]
    no_action_id: NoActionId
    no_action_digest: Sha256Digest
    reason_code: Literal["target_already_satisfied"]
    signal_reference: StrategySignalReferenceResponse
    market_reference: StrategySignalMarketReferenceResponse
    account_reference: OrderIntentAccountReferenceResponse
    target_semantics: Literal["target_position_quantity"]
    target_position_quantity: CanonicalDecimal
    current_position_quantity: CanonicalDecimal
    intent_policy_version: Literal["target_position_quantity_delta_v1"]
    origin_command_digest: Sha256Digest
    origin_actor: StrictStr
    created_at: datetime

    _validate_created_at = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class OrderIntentCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    result_kind: Literal["order_intent"]
    result: OrderIntentResponse


class OrderIntentNoActionCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    result_kind: Literal["order_intent_no_action"]
    result: OrderIntentNoActionResponse


OrderIntentCommandResultResponse = Annotated[
    OrderIntentCommandResponse | OrderIntentNoActionCommandResponse,
    Field(discriminator="result_kind"),
]


class OrderIntentListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[OrderIntentResponse]
    next_cursor: StrictStr | None


class PreTradeRiskPolicyRequest(_StrictModel):
    policy_id: Literal["long_only_cash_risk_v1"]
    reference_price_policy_id: Literal["latest_trade_price_v1"]
    maximum_order_quantity: CanonicalDecimal | None = None
    maximum_order_notional: CanonicalDecimal | None = None


class PreTradeRiskMarketRequest(_StrictModel):
    expected_calendar_id: BoundedId
    expected_calendar_version: ExactPositiveInt
    expected_trading_session_id: BoundedId
    expected_replay_id: BoundedId
    expected_event_stream_digest: Sha256Digest
    expected_cursor_position: ExactPositiveInt
    expected_current_event_id: BoundedId
    expected_current_event_time_utc: datetime | None = None
    expected_instrument_id: BoundedId

    _validate_current_event_time = field_validator(
        "expected_current_event_time_utc", mode="before"
    )(_normalized_utc)


class PreTradeRiskAccountRequest(_StrictModel):
    expected_account_head_version: ExactPositiveInt
    expected_account_head_event_id: BoundedId
    expected_account_head_chain_digest: Sha256Digest


class PreTradeRiskDecisionCreateRequest(_StrictModel):
    intent_id: IntentId
    policy: PreTradeRiskPolicyRequest
    account: PreTradeRiskAccountRequest
    market: PreTradeRiskMarketRequest
    actor: BoundedActor


class OrderIntentReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    intent_id: IntentId
    intent_digest: Sha256Digest


class PreTradeRiskPolicyReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    policy_id: Literal["long_only_cash_risk_v1"]
    reference_price_policy_id: Literal["latest_trade_price_v1"]
    maximum_order_quantity: CanonicalDecimal | None
    maximum_order_notional: CanonicalDecimal | None
    configuration_digest: Sha256Digest
    reference_digest: Sha256Digest


class PreTradeRiskPriceReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    reference_price_policy_id: Literal["latest_trade_price_v1"]
    event_stream_digest: Sha256Digest
    replay_id: BoundedId
    cursor_position: ExactPositiveInt
    price_event_position: ExactPositiveInt
    price_event_id: BoundedId
    price_event_time: datetime
    instrument_id: BoundedId
    price_event_digest: Sha256Digest
    reference_price: CanonicalDecimal
    reference_digest: Sha256Digest

    _validate_price_event_time = field_validator(
        "price_event_time", mode="before"
    )(_normalized_utc)


class PreTradeRiskRuleEvidenceResponse(_StrictModel):
    schema_version: Literal[1]
    rule_code: RiskRuleCode
    applicable: bool
    value_type: Literal["quantity", "money"]
    observed_value: CanonicalDecimal | None
    threshold_value: CanonicalDecimal | None
    passed: bool
    rule_digest: Sha256Digest


class PreTradeRiskInputSnapshotResponse(_StrictModel):
    schema_version: Literal[1]
    snapshot_id: RiskInputId
    snapshot_digest: Sha256Digest
    intent_reference: OrderIntentReferenceResponse
    market_reference: StrategySignalMarketReferenceResponse
    account_reference: OrderIntentAccountReferenceResponse
    risk_policy_reference: PreTradeRiskPolicyReferenceResponse
    price_reference: PreTradeRiskPriceReferenceResponse
    side: OrderSide
    requested_quantity: CanonicalDecimal
    verified_available_cash: CanonicalDecimal
    verified_current_instrument_quantity: CanonicalDecimal
    estimated_order_notional: CanonicalDecimal
    rule_evidence: list[PreTradeRiskRuleEvidenceResponse]


class PreTradeRiskDecisionResponse(_StrictModel):
    schema_version: Literal[1]
    decision_id: DecisionId
    decision_digest: Sha256Digest
    input_snapshot: PreTradeRiskInputSnapshotResponse
    outcome: RiskOutcome
    reason_codes: list[RiskRuleCode]
    origin_command_digest: Sha256Digest
    origin_actor: StrictStr
    created_at: datetime

    _validate_created_at = field_validator("created_at", mode="before")(
        _normalized_utc
    )


class PreTradeRiskDecisionCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    decision: PreTradeRiskDecisionResponse


class PreTradeRiskDecisionListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PreTradeRiskDecisionResponse]
    next_cursor: StrictStr | None


__all__ = [
    "DecisionId",
    "IntentId",
    "OrderIntentCommandResponse",
    "OrderIntentCommandResultResponse",
    "OrderIntentCreateRequest",
    "OrderIntentListResponse",
    "OrderIntentNoActionCommandResponse",
    "OrderIntentNoActionResponse",
    "OrderIntentResponse",
    "OrderSide",
    "PreTradeRiskDecisionCommandResponse",
    "PreTradeRiskDecisionCreateRequest",
    "PreTradeRiskDecisionListResponse",
    "PreTradeRiskDecisionResponse",
    "RiskOutcome",
    "SignalId",
    "StrategySignalCommandResponse",
    "StrategySignalEvaluateRequest",
    "StrategySignalListResponse",
    "StrategySignalResponse",
]
