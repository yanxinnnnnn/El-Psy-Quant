"""Exactly nine versioned M34 Paper Execution API operations."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from el_psy_quant.api.dependencies import get_paper_execution_application_service
from el_psy_quant.api.observability import log_paper_execution_event
from el_psy_quant.api.paper_execution_errors import (
    PaperExecutionApiOperation,
    PaperExecutionInvalidDecimalError,
    PaperExecutionInvalidPolicyError,
    raise_paper_execution_api_error,
)
from el_psy_quant.api.paper_execution_pagination import (
    decode_paper_execution_list_cursor,
    encode_paper_execution_list_cursor,
)
from el_psy_quant.api.paper_execution_schemas import (
    ExecutionAttemptId,
    ExecutionFillId,
    ExecutionOrderId,
    OrderSide,
    PaperExecutionAttemptListResponse,
    PaperExecutionAttemptResponse,
    PaperExecutionCreateResultResponse,
    PaperExecutionFillListResponse,
    PaperExecutionFillResponse,
    PaperExecutionOrderCommandResponse,
    PaperExecutionOrderCreateRequest,
    PaperExecutionOrderListResponse,
    PaperExecutionOrderResponse,
    PaperExecutionOrderStateResponse,
    PaperExecutionOrderStepRequest,
    PaperExecutionOrderViewResponse,
    PaperExecutionReconciliationResponse,
    PaperExecutionSettlementLinkResponse,
    PaperExecutionStepCommandResponse,
    PaperExecutionStepResultResponse,
)
from el_psy_quant.api.schemas import ApiErrorResponse
from el_psy_quant.application import PaperExecutionApplicationService
from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.paper_execution import (
    PaperExecutionBasisPoints,
    create_paper_execution_policy_reference,
)
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionCorruptAuthorityError,
    PaperExecutionHistory,
    PaperExecutionStaleAuthorityError,
    PaperExecutionStepCommit,
)

router = APIRouter()
PaperExecutionService = Annotated[
    PaperExecutionApplicationService,
    Depends(get_paper_execution_application_service),
]
IdempotencyKeyHeader = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        pattern=r"^\S(?:.*\S)?$",
    ),
]
OrderIdPath = Annotated[
    ExecutionOrderId, Path(pattern=r"^peo_[0-9a-f]{64}$")
]
AttemptIdPath = Annotated[
    ExecutionAttemptId, Path(pattern=r"^pea_[0-9a-f]{64}$")
]
FillIdPath = Annotated[
    ExecutionFillId, Path(pattern=r"^pef_[0-9a-f]{64}$")
]
BoundedFilter = Annotated[
    str, Query(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$")
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


def _policy(command: PaperExecutionOrderCreateRequest):
    selection = command.execution_policy
    try:
        cap = (
            None
            if selection.max_fill_quantity_per_trade_event is None
            else PaperQuantity.parse(
                selection.max_fill_quantity_per_trade_event
            )
        )
        values = tuple(
            PaperExecutionBasisPoints.parse(value)
            for value in (
                selection.slippage_bps,
                selection.commission_bps,
                selection.fee_bps,
                selection.buy_tax_bps,
                selection.sell_tax_bps,
            )
        )
    except ValueError as exc:
        raise PaperExecutionInvalidDecimalError() from exc
    try:
        return create_paper_execution_policy_reference(
            max_fill_quantity_per_trade_event=cap,
            slippage_bps=values[0],
            commission_bps=values[1],
            fee_bps=values[2],
            buy_tax_bps=values[3],
            sell_tax_bps=values[4],
        )
    except (TypeError, ValueError) as exc:
        raise PaperExecutionInvalidPolicyError() from exc


def _order_response(history: PaperExecutionHistory) -> PaperExecutionOrderResponse:
    payload = history.order.to_dict()
    payload.pop("origin_command_idempotency_key")
    return PaperExecutionOrderResponse.model_validate(payload)


def _state_response(history: PaperExecutionHistory) -> PaperExecutionOrderStateResponse:
    return PaperExecutionOrderStateResponse.model_validate(history.state.to_dict())


def _order_view(history: PaperExecutionHistory) -> PaperExecutionOrderViewResponse:
    return PaperExecutionOrderViewResponse(
        order=_order_response(history),
        state=_state_response(history),
    )


def _attempt_response(value) -> PaperExecutionAttemptResponse:
    return PaperExecutionAttemptResponse.model_validate(value.to_dict())


def _fill_response(value) -> PaperExecutionFillResponse:
    return PaperExecutionFillResponse.model_validate(value.to_dict())


def _link_response(value) -> PaperExecutionSettlementLinkResponse:
    return PaperExecutionSettlementLinkResponse.model_validate(value.to_dict())


def _step_result_response(commit: PaperExecutionStepCommit) -> PaperExecutionStepResultResponse:
    step = commit.step_result
    return PaperExecutionStepResultResponse(
        schema_version=1,
        attempt=_attempt_response(step.attempt),
        fill=None if step.fill is None else _fill_response(step.fill),
        order_state=PaperExecutionOrderStateResponse.model_validate(
            step.order_state.to_dict()
        ),
        settlement_link=(
            None
            if commit.settlement_link is None
            else _link_response(commit.settlement_link)
        ),
        account_event_id=commit.account_event_id,
    )


def _audit_result(
    *,
    event: str,
    request_id: str,
    operation: str,
    http_status: int,
    history: PaperExecutionHistory | None = None,
    commit: PaperExecutionStepCommit | None = None,
    replayed: bool | None = None,
) -> None:
    order = None if history is None else history.order
    attempt = None if commit is None else commit.step_result.attempt
    fill = None if commit is None else commit.step_result.fill
    log_paper_execution_event(
        event=event,
        request_id=request_id,
        operation=operation,
        http_status=http_status,
        execution_order_id=(
            None
            if order is None and attempt is None
            else order.execution_order_id
            if order is not None
            else attempt.execution_order_reference.execution_order_id
        ),
        execution_order_digest=(
            None
            if order is None and attempt is None
            else order.execution_order_digest
            if order is not None
            else attempt.execution_order_reference.execution_order_digest
        ),
        attempt_id=None if attempt is None else attempt.attempt_id,
        attempt_digest=None if attempt is None else attempt.attempt_digest,
        fill_id=None if fill is None else fill.fill_id,
        fill_digest=None if fill is None else fill.fill_digest,
        account_id=None if order is None else order.account_id,
        replay_id=(
            None if order is None else order.market_handoff_reference.replay_id
        ),
        instrument_id=None if order is None else order.instrument_id,
        execution_version=(
            None
            if commit is None
            else commit.step_result.order_state.execution_version
        ),
        attempt_result=None if attempt is None else attempt.attempt_result,
        terminal_reason=None if attempt is None else attempt.terminal_reason_code,
        no_fill_reason=None if attempt is None else attempt.no_fill_reason_code,
        replayed=replayed,
    )


def _raise(
    exc: Exception,
    *,
    request: Request,
    operation: PaperExecutionApiOperation,
    execution_order_id: str | None = None,
) -> None:
    if isinstance(exc, PaperExecutionStaleAuthorityError):
        log_paper_execution_event(
            event="paper_execution_stale_authority_refused",
            request_id=_request_id(request),
            operation=operation,
            http_status=HTTPStatus.CONFLICT,
            execution_order_id=execution_order_id,
        )
    elif isinstance(exc, PaperExecutionCorruptAuthorityError):
        log_paper_execution_event(
            event="paper_execution_corruption_refused",
            request_id=_request_id(request),
            operation=operation,
            http_status=HTTPStatus.SERVICE_UNAVAILABLE,
            execution_order_id=execution_order_id,
        )
    raise_paper_execution_api_error(exc, operation=operation)


@router.post(
    "/paper-execution/orders",
    response_model=PaperExecutionOrderCommandResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_paper_execution_order_v1",
    responses={
        HTTPStatus.OK: {"model": PaperExecutionOrderCommandResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def create_paper_execution_order_v1(
    request: Request,
    response: Response,
    command: PaperExecutionOrderCreateRequest,
    service: PaperExecutionService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperExecutionOrderCommandResponse:
    try:
        stored = service.create_order_from_references(
            intent_id=command.intent.intent_id,
            intent_digest=command.intent.intent_digest,
            decision_id=command.decision.decision_id,
            decision_digest=command.decision.decision_digest,
            execution_policy_reference=_policy(command),
            command_idempotency_key=idempotency_key,
            actor=command.actor,
        )
        status = _accepted_status(response, replayed=stored.replayed)
        request_id = _request_id(request)
        history = stored.result
        body = PaperExecutionOrderCommandResponse(
            schema_version=1,
            replayed=stored.replayed,
            request_id=request_id,
            result=PaperExecutionCreateResultResponse(
                order=_order_response(history), state=_state_response(history)
            ),
        )
        _audit_result(
            event=(
                "paper_execution_idempotent_replay"
                if stored.replayed
                else "paper_execution_order_created"
            ),
            request_id=request_id,
            operation="order_create",
            http_status=status,
            history=history,
            replayed=stored.replayed,
        )
        return body
    except Exception as exc:
        _raise(exc, request=request, operation="order_create")


@router.get(
    "/paper-execution/orders",
    response_model=PaperExecutionOrderListResponse,
    operation_id="list_paper_execution_orders_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_execution_orders_v1(
    request: Request,
    service: PaperExecutionService,
    account_id: BoundedFilter | None = None,
    replay_id: BoundedFilter | None = None,
    trading_session_id: BoundedFilter | None = None,
    instrument_id: BoundedFilter | None = None,
    side: Annotated[OrderSide | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperExecutionOrderListResponse:
    context = {
        "account_id": account_id,
        "replay_id": replay_id,
        "trading_session_id": trading_session_id,
        "instrument_id": instrument_id,
        "side": side,
    }
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_execution_list_cursor(
                cursor,
                expected_collection="paper_execution_orders",
                query_context=context,
            )
        )
        page = service.list_order_histories(
            limit=limit,
            cursor_created_at=None if decoded is None else decoded.created_at,
            cursor_execution_order_id=(
                None if decoded is None else decoded.resource_id
            ),
            account_id=account_id,
            replay_id=replay_id,
            trading_session_id=trading_session_id,
            instrument_id=instrument_id,
            side=side,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1].order
            next_cursor = encode_paper_execution_list_cursor(
                collection_kind="paper_execution_orders",
                resource_id=last.execution_order_id,
                created_at=last.created_at,
                query_context=context,
            )
        return PaperExecutionOrderListResponse(
            schema_version=1,
            items=[_order_view(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="order_list")


@router.get(
    "/paper-execution/orders/{execution_order_id}",
    response_model=PaperExecutionOrderViewResponse,
    operation_id="get_paper_execution_order_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_execution_order_v1(
    request: Request,
    execution_order_id: OrderIdPath,
    service: PaperExecutionService,
) -> PaperExecutionOrderViewResponse:
    try:
        return _order_view(service.get_history(execution_order_id=execution_order_id))
    except Exception as exc:
        _raise(
            exc,
            request=request,
            operation="order_detail",
            execution_order_id=execution_order_id,
        )


@router.post(
    "/paper-execution/orders/{execution_order_id}/steps",
    response_model=PaperExecutionStepCommandResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="step_paper_execution_order_v1",
    responses={
        HTTPStatus.OK: {"model": PaperExecutionStepCommandResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def step_paper_execution_order_v1(
    request: Request,
    response: Response,
    execution_order_id: OrderIdPath,
    command: PaperExecutionOrderStepRequest,
    service: PaperExecutionService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperExecutionStepCommandResponse:
    try:
        stored = service.step_order_from_reference(
            execution_order_id=execution_order_id,
            execution_order_digest=command.execution_order_digest,
            expected_execution_version=command.expected_execution_version,
            command_idempotency_key=idempotency_key,
            actor=command.actor,
        )
        status = _accepted_status(response, replayed=stored.replayed)
        request_id = _request_id(request)
        commit = stored.result
        if stored.replayed:
            events = ("paper_execution_idempotent_replay",)
        else:
            state = commit.step_result.order_state
            events_list = []
            if commit.step_result.fill is None:
                events_list.append("paper_execution_step_no_fill")
            else:
                events_list.append("paper_execution_fill_created")
            if state.status == "filled":
                events_list.append("paper_execution_order_filled")
            elif state.status == "rejected":
                events_list.append("paper_execution_order_rejected")
            elif state.status == "partially_filled_rejected":
                events_list.append(
                    "paper_execution_order_partially_filled_rejected"
                )
            events = tuple(events_list)
        for event in events:
            _audit_result(
                event=event,
                request_id=request_id,
                operation="order_step",
                http_status=status,
                commit=commit,
                replayed=stored.replayed,
            )
        return PaperExecutionStepCommandResponse(
            schema_version=1,
            replayed=stored.replayed,
            request_id=request_id,
            result=_step_result_response(commit),
        )
    except Exception as exc:
        _raise(
            exc,
            request=request,
            operation="order_step",
            execution_order_id=execution_order_id,
        )


@router.get(
    "/paper-execution/orders/{execution_order_id}/attempts",
    response_model=PaperExecutionAttemptListResponse,
    operation_id="list_paper_execution_attempts_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_execution_attempts_v1(
    request: Request,
    execution_order_id: OrderIdPath,
    service: PaperExecutionService,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperExecutionAttemptListResponse:
    context = {"execution_order_id": execution_order_id}
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_execution_list_cursor(
                cursor,
                expected_collection="paper_execution_attempts",
                query_context=context,
            )
        )
        page = service.list_attempts(
            execution_order_id=execution_order_id,
            limit=limit,
            cursor_execution_version_before=(
                None if decoded is None else decoded.execution_version_before
            ),
            cursor_attempt_id=None if decoded is None else decoded.resource_id,
            version_anchor=None if decoded is None else decoded.version_anchor,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_execution_list_cursor(
                collection_kind="paper_execution_attempts",
                resource_id=last.attempt_id,
                execution_version_before=last.execution_version_before,
                execution_order_id=execution_order_id,
                version_anchor=page.version_anchor,
                query_context=context,
            )
        return PaperExecutionAttemptListResponse(
            schema_version=1,
            items=[_attempt_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(
            exc,
            request=request,
            operation="attempt_list",
            execution_order_id=execution_order_id,
        )


@router.get(
    "/paper-execution/attempts/{attempt_id}",
    response_model=PaperExecutionAttemptResponse,
    operation_id="get_paper_execution_attempt_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_execution_attempt_v1(
    request: Request,
    attempt_id: AttemptIdPath,
    service: PaperExecutionService,
) -> PaperExecutionAttemptResponse:
    try:
        return _attempt_response(service.get_attempt(attempt_id=attempt_id))
    except Exception as exc:
        _raise(exc, request=request, operation="attempt_detail")


@router.get(
    "/paper-execution/fills",
    response_model=PaperExecutionFillListResponse,
    operation_id="list_paper_execution_fills_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_execution_fills_v1(
    request: Request,
    service: PaperExecutionService,
    execution_order_id: Annotated[
        ExecutionOrderId | None, Query(pattern=r"^peo_[0-9a-f]{64}$")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperExecutionFillListResponse:
    context = {"execution_order_id": execution_order_id}
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_execution_list_cursor(
                cursor,
                expected_collection="paper_execution_fills",
                query_context=context,
            )
        )
        page = service.list_fills(
            limit=limit,
            cursor_created_at=None if decoded is None else decoded.created_at,
            cursor_fill_id=None if decoded is None else decoded.resource_id,
            execution_order_id=execution_order_id,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_execution_list_cursor(
                collection_kind="paper_execution_fills",
                resource_id=last.fill_id,
                created_at=last.created_at,
                query_context=context,
            )
        return PaperExecutionFillListResponse(
            schema_version=1,
            items=[_fill_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="fill_list")


@router.get(
    "/paper-execution/fills/{fill_id}",
    response_model=PaperExecutionFillResponse,
    operation_id="get_paper_execution_fill_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_execution_fill_v1(
    request: Request,
    fill_id: FillIdPath,
    service: PaperExecutionService,
) -> PaperExecutionFillResponse:
    try:
        return _fill_response(service.get_fill(fill_id=fill_id))
    except Exception as exc:
        _raise(exc, request=request, operation="fill_detail")


@router.get(
    "/paper-execution/orders/{execution_order_id}/reconciliation",
    response_model=PaperExecutionReconciliationResponse,
    operation_id="get_paper_execution_reconciliation_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_execution_reconciliation_v1(
    request: Request,
    execution_order_id: OrderIdPath,
    service: PaperExecutionService,
) -> PaperExecutionReconciliationResponse:
    try:
        history = service.reconcile_order(execution_order_id=execution_order_id)
        request_id = _request_id(request)
        body = PaperExecutionReconciliationResponse(
            schema_version=1,
            order=_order_response(history),
            state=_state_response(history),
            attempts=[_attempt_response(item) for item in history.attempts],
            fills=[_fill_response(item) for item in history.fills],
            settlement_links=[
                _link_response(item) for item in history.settlement_links
            ],
        )
        _audit_result(
            event="paper_execution_reconciliation_checked",
            request_id=request_id,
            operation="reconciliation",
            http_status=HTTPStatus.OK,
            history=history,
            replayed=False,
        )
        return body
    except Exception as exc:
        _raise(
            exc,
            request=request,
            operation="reconciliation",
            execution_order_id=execution_order_id,
        )


__all__ = ["router"]
