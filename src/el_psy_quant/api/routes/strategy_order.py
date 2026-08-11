"""Exact versioned M33 Strategy Signal, Intent, and Risk API surface."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from el_psy_quant.api.dependencies import (
    get_server_utc_timestamp,
    get_strategy_order_application_service,
)
from el_psy_quant.api.observability import (
    log_order_intent_derivation_completed,
    log_pre_trade_risk_evaluation_completed,
    log_strategy_signal_evaluation_completed,
)
from el_psy_quant.api.schemas import ApiErrorResponse
from el_psy_quant.api.strategy_order_errors import (
    StrategyOrderApiOperation,
    StrategyOrderInvalidDecimalError,
    StrategyOrderInvalidRiskPolicyError,
    StrategyOrderInvalidRuntimeConfigurationError,
    raise_strategy_order_api_error,
)
from el_psy_quant.api.strategy_order_pagination import (
    decode_strategy_order_list_cursor,
    encode_strategy_order_list_cursor,
)
from el_psy_quant.api.strategy_order_schemas import (
    OrderIntentCommandResponse,
    OrderIntentCommandResultResponse,
    OrderIntentCreateRequest,
    OrderIntentListResponse,
    OrderIntentNoActionCommandResponse,
    OrderIntentNoActionResponse,
    OrderIntentResponse,
    OrderSide,
    PreTradeRiskDecisionCommandResponse,
    PreTradeRiskDecisionCreateRequest,
    PreTradeRiskDecisionListResponse,
    PreTradeRiskDecisionResponse,
    RiskOutcome,
    StrategySignalCommandResponse,
    StrategySignalEvaluateRequest,
    StrategySignalListResponse,
    StrategySignalResponse,
)
from el_psy_quant.application import StrategyOrderApplicationService
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentNoAction,
    PreTradeRiskDecision,
    PreTradeRiskPolicyReference,
    StrategyRuntimeReference,
    StrategySignal,
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
)

router = APIRouter()
StrategyOrderService = Annotated[
    StrategyOrderApplicationService,
    Depends(get_strategy_order_application_service),
]
ServerUtcTimestamp = Annotated[datetime, Depends(get_server_utc_timestamp)]
IdempotencyKeyHeader = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        pattern=r"^\S(?:.*\S)?$",
    ),
]
SignalIdPath = Annotated[
    str, Path(pattern=r"^sig_[0-9a-f]{64}$")
]
IntentIdPath = Annotated[str, Path(pattern=r"^oi_[0-9a-f]{64}$")]
DecisionIdPath = Annotated[
    str, Path(pattern=r"^risk_decision_[0-9a-f]{64}$")
]
SignalIdFilter = Annotated[
    str,
    Query(min_length=68, max_length=68, pattern=r"^sig_[0-9a-f]{64}$"),
]
IntentIdFilter = Annotated[
    str,
    Query(min_length=67, max_length=67, pattern=r"^oi_[0-9a-f]{64}$"),
]
BoundedFilter = Annotated[
    str,
    Query(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$"),
]
StrategyNameFilter = Annotated[
    str,
    Query(min_length=1, max_length=128, pattern=r"^\S(?:.*\S)?$"),
]

_ERROR_404 = {"model": ApiErrorResponse}
_ERROR_409 = {"model": ApiErrorResponse}
_ERROR_422 = {"model": ApiErrorResponse}
_ERROR_503 = {"model": ApiErrorResponse}


def _request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if not isinstance(value, str):
        raise RuntimeError("server request ID is unavailable")
    return value


def _accepted_status(response: Response, *, replayed: bool) -> int:
    status = HTTPStatus.OK if replayed else HTTPStatus.CREATED
    response.status_code = status
    return status


def _runtime_reference(
    command: StrategySignalEvaluateRequest,
) -> StrategyRuntimeReference:
    try:
        target = PaperQuantity.parse(
            command.runtime.target_position_quantity
        )
    except ValueError as exc:
        raise StrategyOrderInvalidDecimalError() from exc
    try:
        return create_moving_average_crossover_runtime_reference(
            fast_window=command.runtime.fast_window,
            slow_window=command.runtime.slow_window,
            target_position_quantity=target,
            strategy_name=command.runtime.strategy_name,
            strategy_version=command.runtime.strategy_version,
            adapter_version=command.runtime.adapter_version,
            runtime_sizing_semantics=(
                command.runtime.runtime_sizing_semantics
            ),
        )
    except (TypeError, ValueError) as exc:
        raise StrategyOrderInvalidRuntimeConfigurationError() from exc


def _risk_policy(
    command: PreTradeRiskDecisionCreateRequest,
) -> PreTradeRiskPolicyReference:
    try:
        maximum_quantity = (
            None
            if command.policy.maximum_order_quantity is None
            else PaperQuantity.parse(command.policy.maximum_order_quantity)
        )
        maximum_notional = (
            None
            if command.policy.maximum_order_notional is None
            else PaperMoney.parse(command.policy.maximum_order_notional)
        )
    except ValueError as exc:
        raise StrategyOrderInvalidDecimalError() from exc
    try:
        return create_long_only_cash_risk_policy_reference(
            maximum_order_quantity=maximum_quantity,
            maximum_order_notional=maximum_notional,
        )
    except (TypeError, ValueError) as exc:
        raise StrategyOrderInvalidRiskPolicyError() from exc


def _signal_response(signal: StrategySignal) -> StrategySignalResponse:
    return StrategySignalResponse.model_validate(signal.to_dict())


def _intent_response(intent: OrderIntent) -> OrderIntentResponse:
    payload = intent.to_dict()
    payload.pop("origin_command_idempotency_key")
    return OrderIntentResponse.model_validate(payload)


def _no_action_response(
    result: OrderIntentNoAction,
) -> OrderIntentNoActionResponse:
    payload = result.to_dict()
    payload.pop("origin_command_idempotency_key")
    return OrderIntentNoActionResponse.model_validate(payload)


def _decision_response(
    decision: PreTradeRiskDecision,
) -> PreTradeRiskDecisionResponse:
    payload = decision.to_dict()
    payload.pop("origin_command_idempotency_key")
    return PreTradeRiskDecisionResponse.model_validate(payload)


def _raise(exc: Exception, operation: StrategyOrderApiOperation) -> None:
    raise_strategy_order_api_error(exc, operation=operation)


@router.post(
    "/strategy-signals/evaluate",
    response_model=StrategySignalCommandResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="evaluate_strategy_signal_v1",
    responses={
        HTTPStatus.OK: {"model": StrategySignalCommandResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def evaluate_strategy_signal_v1(
    request: Request,
    response: Response,
    command: StrategySignalEvaluateRequest,
    service: StrategyOrderService,
    idempotency_key: IdempotencyKeyHeader,
    created_at: ServerUtcTimestamp,
) -> StrategySignalCommandResponse:
    """Evaluate one approved runtime against exact current M32 authority."""
    try:
        market = command.market
        stored = service.evaluate_and_store_strategy_signal(
            strategy_runtime_reference=_runtime_reference(command),
            calendar_id=market.calendar_id,
            expected_calendar_version=market.expected_calendar_version,
            trading_session_id=market.trading_session_id,
            replay_id=market.replay_id,
            expected_event_stream_digest=(
                market.expected_event_stream_digest
            ),
            expected_cursor_position=market.expected_cursor_position,
            expected_signal_event_id=market.expected_signal_event_id,
            expected_signal_time=market.expected_signal_time_utc,
            instrument_id=market.instrument_id,
            command_idempotency_key=idempotency_key,
            actor=command.actor,
            created_at=created_at,
        )
        status = _accepted_status(response, replayed=stored.replayed)
        request_id = _request_id(request)
        signal = stored.result
        body = StrategySignalCommandResponse(
            schema_version=1,
            replayed=stored.replayed,
            request_id=request_id,
            signal=_signal_response(signal),
        )
        log_strategy_signal_evaluation_completed(
            request_id=request_id,
            http_status=status,
            replayed=stored.replayed,
            signal_id=signal.signal_id,
            signal_digest=signal.signal_digest,
            replay_id=signal.market_reference.replay_id,
            instrument_id=signal.market_reference.instrument_id,
        )
        return body
    except Exception as exc:
        _raise(exc, "signal_evaluate")


@router.get(
    "/strategy-signals",
    response_model=StrategySignalListResponse,
    operation_id="list_strategy_signals_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_strategy_signals_v1(
    service: StrategyOrderService,
    strategy_name: StrategyNameFilter | None = None,
    instrument_id: BoundedFilter | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> StrategySignalListResponse:
    """Return one deterministic bounded Signal page."""
    try:
        decoded = (
            None
            if cursor is None
            else decode_strategy_order_list_cursor(
                cursor, expected_collection="strategy_signals"
            )
        )
        page = service.list_strategy_signals(
            limit=limit,
            cursor_created_at=(
                None if decoded is None else decoded.created_at
            ),
            cursor_signal_id=(
                None if decoded is None else decoded.resource_id
            ),
            strategy_name=strategy_name,
            instrument_id=instrument_id,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_strategy_order_list_cursor(
                collection_kind="strategy_signals",
                created_at=last.created_at,
                resource_id=last.signal_id,
            )
        return StrategySignalListResponse(
            schema_version=1,
            items=[_signal_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, "signal_list")


@router.get(
    "/strategy-signals/{signal_id}",
    response_model=StrategySignalResponse,
    operation_id="get_strategy_signal_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_strategy_signal_v1(
    signal_id: SignalIdPath,
    service: StrategyOrderService,
) -> StrategySignalResponse:
    """Return one strictly reconstructed immutable Signal."""
    try:
        return _signal_response(service.get_strategy_signal(signal_id=signal_id))
    except Exception as exc:
        _raise(exc, "signal_detail")


@router.post(
    "/order-intents",
    response_model=OrderIntentCommandResultResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_order_intent_v1",
    responses={
        HTTPStatus.OK: {"model": OrderIntentCommandResultResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def create_order_intent_v1(
    request: Request,
    response: Response,
    command: OrderIntentCreateRequest,
    service: StrategyOrderService,
    idempotency_key: IdempotencyKeyHeader,
    created_at: ServerUtcTimestamp,
) -> OrderIntentCommandResponse | OrderIntentNoActionCommandResponse:
    """Derive one Intent or no-action result from persisted authority."""
    try:
        account = command.account
        stored = service.derive_and_store_order_intent(
            signal_id=command.signal_id,
            account_id=account.account_id,
            expected_account_head_version=(
                account.expected_account_head_version
            ),
            expected_account_head_event_id=(
                account.expected_account_head_event_id
            ),
            expected_account_head_chain_digest=(
                account.expected_account_head_chain_digest
            ),
            intent_policy_version=command.intent_policy_version,
            command_idempotency_key=idempotency_key,
            actor=command.actor,
            created_at=created_at,
        )
        status = _accepted_status(response, replayed=stored.replayed)
        request_id = _request_id(request)
        result = stored.result
        if type(result) is OrderIntent:
            body: OrderIntentCommandResponse | OrderIntentNoActionCommandResponse
            body = OrderIntentCommandResponse(
                schema_version=1,
                replayed=stored.replayed,
                request_id=request_id,
                result_kind="order_intent",
                result=_intent_response(result),
            )
            result_kind: Literal["order_intent", "order_intent_no_action"] = (
                "order_intent"
            )
            result_id = result.intent_id
            result_digest = result.intent_digest
            side = result.side
            no_action_reason = None
        else:
            body = OrderIntentNoActionCommandResponse(
                schema_version=1,
                replayed=stored.replayed,
                request_id=request_id,
                result_kind="order_intent_no_action",
                result=_no_action_response(result),
            )
            result_kind = "order_intent_no_action"
            result_id = result.no_action_id
            result_digest = result.no_action_digest
            side = None
            no_action_reason = result.reason_code
        log_order_intent_derivation_completed(
            request_id=request_id,
            http_status=status,
            replayed=stored.replayed,
            result_kind=result_kind,
            result_id=result_id,
            result_digest=result_digest,
            signal_id=result.signal_reference.signal_id,
            account_id=result.account_reference.account_id,
            replay_id=result.market_reference.replay_id,
            instrument_id=result.market_reference.instrument_id,
            side=side,
            no_action_reason=no_action_reason,
        )
        return body
    except Exception as exc:
        _raise(exc, "intent_create")


@router.get(
    "/order-intents",
    response_model=OrderIntentListResponse,
    operation_id="list_order_intents_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_order_intents_v1(
    service: StrategyOrderService,
    signal_id: SignalIdFilter | None = None,
    account_id: BoundedFilter | None = None,
    instrument_id: BoundedFilter | None = None,
    side: Annotated[OrderSide | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> OrderIntentListResponse:
    """Return one deterministic bounded Intent page."""
    try:
        decoded = (
            None
            if cursor is None
            else decode_strategy_order_list_cursor(
                cursor, expected_collection="order_intents"
            )
        )
        page = service.list_order_intents(
            limit=limit,
            cursor_created_at=(
                None if decoded is None else decoded.created_at
            ),
            cursor_intent_id=(
                None if decoded is None else decoded.resource_id
            ),
            signal_id=signal_id,
            account_id=account_id,
            instrument_id=instrument_id,
            side=side,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_strategy_order_list_cursor(
                collection_kind="order_intents",
                created_at=last.created_at,
                resource_id=last.intent_id,
            )
        return OrderIntentListResponse(
            schema_version=1,
            items=[_intent_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, "intent_list")


@router.get(
    "/order-intents/{intent_id}",
    response_model=OrderIntentResponse,
    operation_id="get_order_intent_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_order_intent_v1(
    intent_id: IntentIdPath,
    service: StrategyOrderService,
) -> OrderIntentResponse:
    """Return one strictly reconstructed immutable Intent."""
    try:
        return _intent_response(service.get_order_intent(intent_id=intent_id))
    except Exception as exc:
        _raise(exc, "intent_detail")


@router.post(
    "/pre-trade-risk-decisions",
    response_model=PreTradeRiskDecisionCommandResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_pre_trade_risk_decision_v1",
    responses={
        HTTPStatus.OK: {"model": PreTradeRiskDecisionCommandResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def create_pre_trade_risk_decision_v1(
    request: Request,
    response: Response,
    command: PreTradeRiskDecisionCreateRequest,
    service: StrategyOrderService,
    idempotency_key: IdempotencyKeyHeader,
    created_at: ServerUtcTimestamp,
) -> PreTradeRiskDecisionCommandResponse:
    """Evaluate pre-trade risk without creating execution authority."""
    try:
        account = command.account
        market = command.market
        stored = service.evaluate_and_store_pre_trade_risk(
            intent_id=command.intent_id,
            risk_policy_reference=_risk_policy(command),
            expected_account_head_version=(
                account.expected_account_head_version
            ),
            expected_account_head_event_id=(
                account.expected_account_head_event_id
            ),
            expected_account_head_chain_digest=(
                account.expected_account_head_chain_digest
            ),
            expected_calendar_id=market.expected_calendar_id,
            expected_calendar_version=market.expected_calendar_version,
            expected_trading_session_id=(
                market.expected_trading_session_id
            ),
            expected_replay_id=market.expected_replay_id,
            expected_event_stream_digest=(
                market.expected_event_stream_digest
            ),
            expected_cursor_position=market.expected_cursor_position,
            expected_current_event_id=market.expected_current_event_id,
            expected_current_event_time=(
                market.expected_current_event_time_utc
            ),
            expected_instrument_id=market.expected_instrument_id,
            command_idempotency_key=idempotency_key,
            actor=command.actor,
            created_at=created_at,
        )
        status = _accepted_status(response, replayed=stored.replayed)
        request_id = _request_id(request)
        decision = stored.result
        body = PreTradeRiskDecisionCommandResponse(
            schema_version=1,
            replayed=stored.replayed,
            request_id=request_id,
            decision=_decision_response(decision),
        )
        snapshot = decision.input_snapshot
        log_pre_trade_risk_evaluation_completed(
            request_id=request_id,
            http_status=status,
            replayed=stored.replayed,
            decision_id=decision.decision_id,
            decision_digest=decision.decision_digest,
            intent_id=snapshot.intent_reference.intent_id,
            account_id=snapshot.account_reference.account_id,
            replay_id=snapshot.market_reference.replay_id,
            instrument_id=snapshot.market_reference.instrument_id,
            outcome=decision.outcome,
            reason_codes=decision.reason_codes,
        )
        return body
    except Exception as exc:
        _raise(exc, "decision_create")


@router.get(
    "/pre-trade-risk-decisions",
    response_model=PreTradeRiskDecisionListResponse,
    operation_id="list_pre_trade_risk_decisions_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_pre_trade_risk_decisions_v1(
    service: StrategyOrderService,
    intent_id: IntentIdFilter | None = None,
    account_id: BoundedFilter | None = None,
    outcome: Annotated[RiskOutcome | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PreTradeRiskDecisionListResponse:
    """Return one deterministic bounded Decision page."""
    try:
        decoded = (
            None
            if cursor is None
            else decode_strategy_order_list_cursor(
                cursor, expected_collection="pre_trade_risk_decisions"
            )
        )
        page = service.list_pre_trade_risk_decisions(
            limit=limit,
            cursor_created_at=(
                None if decoded is None else decoded.created_at
            ),
            cursor_decision_id=(
                None if decoded is None else decoded.resource_id
            ),
            intent_id=intent_id,
            account_id=account_id,
            outcome=outcome,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_strategy_order_list_cursor(
                collection_kind="pre_trade_risk_decisions",
                created_at=last.created_at,
                resource_id=last.decision_id,
            )
        return PreTradeRiskDecisionListResponse(
            schema_version=1,
            items=[_decision_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, "decision_list")


@router.get(
    "/pre-trade-risk-decisions/{decision_id}",
    response_model=PreTradeRiskDecisionResponse,
    operation_id="get_pre_trade_risk_decision_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_pre_trade_risk_decision_v1(
    decision_id: DecisionIdPath,
    service: StrategyOrderService,
) -> PreTradeRiskDecisionResponse:
    """Return one strictly reconstructed immutable risk Decision."""
    try:
        decision = service.get_pre_trade_risk_decision(
            decision_id=decision_id
        )
        return _decision_response(decision)
    except Exception as exc:
        _raise(exc, "decision_detail")


__all__ = ["router"]
