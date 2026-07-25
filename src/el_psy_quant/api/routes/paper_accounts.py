"""Exact versioned M31 Paper Account API surface."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from el_psy_quant.api.dependencies import (
    get_paper_account_application_service,
)
from el_psy_quant.api.observability import (
    log_paper_account_command_completed,
    log_paper_account_reconciliation_completed,
    log_paper_account_snapshot_completed,
)
from el_psy_quant.api.paper_account_errors import (
    PaperAccountApiOperation,
    raise_paper_account_api_error,
)
from el_psy_quant.api.paper_account_pagination import (
    decode_paper_account_list_cursor,
    encode_paper_account_list_cursor,
)
from el_psy_quant.api.paper_account_schemas import (
    PaperAccountCashMovementRequest,
    PaperAccountCommandResponse,
    PaperAccountCreateRequest,
    PaperAccountDetailResponse,
    PaperAccountEvidenceLinkRequest,
    PaperAccountEvidenceOperationRequest,
    PaperAccountLedgerEventResponse,
    PaperAccountLedgerResponse,
    PaperAccountLifecycleRequest,
    PaperAccountListResponse,
    PaperAccountPositionAdjustmentRequest,
    PaperAccountProjectionResponse,
    PaperAccountReconciliationCommandResponse,
    PaperAccountReconciliationResponse,
    PaperAccountSnapshotCommandResponse,
    PaperAccountSnapshotResponse,
    PaperAccountSummaryResponse,
)
from el_psy_quant.application import PaperAccountApplicationService
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.persistence import (
    PaperAccountCommandResult,
    PaperAccountRecord,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountLedgerPageItem,
)

router = APIRouter(prefix="/paper-accounts")
PaperAccountService = Annotated[
    PaperAccountApplicationService,
    Depends(get_paper_account_application_service),
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
AccountIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=512,
        pattern=r"^\S(?:.*\S)?$",
    ),
]
LifecycleFilter = Literal["active", "frozen", "closed"]


def _request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if not isinstance(value, str):
        raise RuntimeError("server request ID is unavailable")
    return value


def _idempotency_key(value: str) -> str:
    if not value or len(value) > 128 or value.strip() != value:
        raise ValueError("Idempotency-Key must already be normalized")
    return value


def _summary(record: PaperAccountRecord) -> PaperAccountSummaryResponse:
    identity = record.account_identity
    return PaperAccountSummaryResponse(
        record_schema_version=record.record_schema_version,
        account_id=record.account_id,
        display_name=identity.display_name,
        base_currency=identity.base_currency,
        lifecycle_status=record.lifecycle_status,
        head_version=record.head_version,
        head_event_id=record.head_event_id,
        head_chain_digest=record.head_chain_digest,
        projection_status=record.projection_status,
        created_by=identity.created_by,
        created_timestamp=identity.created_timestamp,
        updated_timestamp=record.updated_timestamp,
        closed_timestamp=record.closed_timestamp,
    )


def _projection(value: object) -> PaperAccountProjectionResponse:
    payload = value.to_dict()  # type: ignore[attr-defined]
    return PaperAccountProjectionResponse.model_validate(payload)


def _ledger_event(
    item: PaperAccountLedgerPageItem,
) -> PaperAccountLedgerEventResponse:
    payload = item.event.to_dict()
    payload.pop("command_idempotency_key")
    payload["cash_postings"] = [
        posting.to_dict() for posting in item.cash_postings
    ]
    payload["position_postings"] = [
        posting.to_dict() for posting in item.position_postings
    ]
    return PaperAccountLedgerEventResponse.model_validate(payload)


def _accepted_item(
    result: PaperAccountCommandResult,
) -> PaperAccountLedgerPageItem:
    bundle = result.history[-1]
    if bundle.event.event_id != result.event.event_id:
        raise RuntimeError("accepted Paper Account event is unavailable")
    return PaperAccountLedgerPageItem(
        event=bundle.event,
        cash_postings=bundle.cash_entries,
        position_postings=bundle.position_entries,
    )


def _command_response(
    result: PaperAccountCommandResult,
    *,
    request_id: str,
) -> PaperAccountCommandResponse:
    return PaperAccountCommandResponse(
        schema_version=1,
        replayed=result.replayed,
        request_id=request_id,
        account=_summary(result.account),
        event=_ledger_event(_accepted_item(result)),
        projection=_projection(result.projection),
    )


def _snapshot_response(value: object) -> PaperAccountSnapshotResponse:
    payload = value.to_dict()  # type: ignore[attr-defined]
    payload.pop("operation_idempotency_key")
    return PaperAccountSnapshotResponse.model_validate(payload)


def _reconciliation_response(
    value: object,
) -> PaperAccountReconciliationResponse:
    payload = value.to_dict()  # type: ignore[attr-defined]
    payload.pop("operation_idempotency_key")
    return PaperAccountReconciliationResponse.model_validate(payload)


def _accepted_status(response: Response, *, replayed: bool) -> int:
    status = HTTPStatus.OK if replayed else HTTPStatus.CREATED
    response.status_code = status
    return status


def _raise(exc: Exception, operation: PaperAccountApiOperation) -> None:
    raise_paper_account_api_error(exc, operation=operation)


@router.post(
    "",
    response_model=PaperAccountCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PaperAccountCommandResponse}},
)
def post_paper_account(
    request: Request,
    response: Response,
    command: PaperAccountCreateRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountCommandResponse:
    """Create or exactly replay one durable Paper Account."""
    try:
        result = service.create_account(
            display_name=command.display_name,
            base_currency=command.base_currency,
            initial_cash=PaperMoney.parse(command.initial_cash),
            creation_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
        )
        status = _accepted_status(response, replayed=result.replayed)
        request_id = _request_id(request)
        body = _command_response(result, request_id=request_id)
        log_paper_account_command_completed(
            operation="create",
            request_id=request_id,
            http_status=status,
            account_id=result.account.account_id,
            event_id=result.event.event_id,
            account_version=result.event.account_version,
            event_type=result.event.event_type,
            replayed=result.replayed,
            projection_status=result.account.projection_status,
        )
        return body
    except Exception as exc:
        _raise(exc, "create")


@router.get("", response_model=PaperAccountListResponse)
def get_paper_accounts(
    service: PaperAccountService,
    lifecycle_status: Annotated[LifecycleFilter | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperAccountListResponse:
    """Return one deterministic bounded keyset page."""
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_account_list_cursor(cursor)
        )
        page = service.list_account_page(
            lifecycle_status=lifecycle_status,
            limit=limit,
            cursor_created_timestamp=(
                None if decoded is None else decoded.created_timestamp
            ),
            cursor_account_id=(
                None if decoded is None else decoded.account_id
            ),
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_account_list_cursor(
                created_timestamp=last.account_identity.created_timestamp,
                account_id=last.account_id,
            )
        return PaperAccountListResponse(
            schema_version=1,
            items=[_summary(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, "list")


@router.get(
    "/{account_id}",
    response_model=PaperAccountDetailResponse,
)
def get_paper_account(
    account_id: AccountIdPath,
    service: PaperAccountService,
) -> PaperAccountDetailResponse:
    """Return one account and its validated current projection."""
    try:
        detail = service.get_account_detail(account_id=account_id)
        return PaperAccountDetailResponse(
            schema_version=1,
            account=_summary(detail.account),
            projection=_projection(detail.projection),
        )
    except Exception as exc:
        _raise(exc, "detail")


@router.get(
    "/{account_id}/ledger",
    response_model=PaperAccountLedgerResponse,
)
def get_paper_account_ledger(
    account_id: AccountIdPath,
    service: PaperAccountService,
    after_sequence_number: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaperAccountLedgerResponse:
    """Return one contiguous validated bounded ledger page."""
    try:
        page = service.get_account_history_page(
            account_id=account_id,
            after_sequence_number=after_sequence_number,
            limit=limit,
        )
        next_after = (
            page.items[-1].event.sequence_number if page.has_more else None
        )
        return PaperAccountLedgerResponse(
            schema_version=1,
            events=[_ledger_event(item) for item in page.items],
            next_after_sequence_number=next_after,
        )
    except Exception as exc:
        _raise(exc, "ledger")


def _post_command(
    *,
    operation: Literal[
        "cash_movement",
        "position_adjustment",
        "evidence_link",
        "freeze",
        "reactivate",
        "close",
    ],
    request: Request,
    response: Response,
    result: PaperAccountCommandResult,
) -> PaperAccountCommandResponse:
    status = _accepted_status(response, replayed=result.replayed)
    request_id = _request_id(request)
    body = _command_response(result, request_id=request_id)
    log_paper_account_command_completed(
        operation=operation,
        request_id=request_id,
        http_status=status,
        account_id=result.account.account_id,
        event_id=result.event.event_id,
        account_version=result.event.account_version,
        event_type=result.event.event_type,
        replayed=result.replayed,
        projection_status=result.account.projection_status,
    )
    return body


@router.post(
    "/{account_id}/cash-movements",
    response_model=PaperAccountCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PaperAccountCommandResponse}},
)
def post_paper_account_cash_movement(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountCashMovementRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountCommandResponse:
    try:
        result = service.post_cash_movement(
            account_id=account_id,
            expected_account_version=command.expected_account_version,
            command_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
            reason=command.reason,
            movement_type=command.movement_type,
            requested_amount=PaperMoney.parse(command.requested_amount),
            effective_timestamp_utc=command.effective_timestamp_utc,
        )
        return _post_command(
            operation="cash_movement",
            request=request,
            response=response,
            result=result,
        )
    except Exception as exc:
        _raise(exc, "cash_movement")


@router.post(
    "/{account_id}/position-adjustments",
    response_model=PaperAccountCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PaperAccountCommandResponse}},
)
def post_paper_account_position_adjustment(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountPositionAdjustmentRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountCommandResponse:
    try:
        result = service.post_position_adjustment(
            account_id=account_id,
            expected_account_version=command.expected_account_version,
            command_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
            reason=command.reason,
            symbol=command.symbol,
            adjustment_category=command.adjustment_category,
            signed_quantity_delta=PaperQuantity.parse(
                command.signed_quantity_delta
            ),
            signed_cost_basis_delta=PaperMoney.parse(
                command.signed_cost_basis_delta
            ),
            effective_timestamp_utc=command.effective_timestamp_utc,
        )
        return _post_command(
            operation="position_adjustment",
            request=request,
            response=response,
            result=result,
        )
    except Exception as exc:
        _raise(exc, "position_adjustment")


@router.post(
    "/{account_id}/evidence-links",
    response_model=PaperAccountCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PaperAccountCommandResponse}},
)
def post_paper_account_evidence_link(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountEvidenceLinkRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountCommandResponse:
    try:
        result = service.link_approved_portfolio_review(
            account_id=account_id,
            expected_account_version=command.expected_account_version,
            command_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
            reason=command.reason,
            review_id=command.review_id,
        )
        return _post_command(
            operation="evidence_link",
            request=request,
            response=response,
            result=result,
        )
    except Exception as exc:
        _raise(exc, "evidence_link")


@router.post(
    "/{account_id}/lifecycle",
    response_model=PaperAccountCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PaperAccountCommandResponse}},
)
def post_paper_account_lifecycle(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountLifecycleRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountCommandResponse:
    try:
        arguments = {
            "account_id": account_id,
            "expected_account_version": command.expected_account_version,
            "command_idempotency_key": _idempotency_key(idempotency_key),
            "actor": command.actor,
            "reason": command.reason,
        }
        if command.action == "freeze":
            result = service.freeze_account(**arguments)
        elif command.action == "reactivate":
            result = service.reactivate_account(**arguments)
        else:
            result = service.close_account(**arguments)
        return _post_command(
            operation=command.action,
            request=request,
            response=response,
            result=result,
        )
    except Exception as exc:
        _raise(exc, "lifecycle")


@router.post(
    "/{account_id}/snapshots",
    response_model=PaperAccountSnapshotCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.OK: {"model": PaperAccountSnapshotCommandResponse}
    },
)
def post_paper_account_snapshot(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountEvidenceOperationRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountSnapshotCommandResponse:
    try:
        result = service.create_snapshot(
            account_id=account_id,
            expected_account_version=command.expected_account_version,
            expected_head_event_id=command.expected_head_event_id,
            expected_head_chain_digest=command.expected_head_chain_digest,
            operation_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
            reason=command.reason,
        )
        status = _accepted_status(response, replayed=result.replayed)
        request_id = _request_id(request)
        body = PaperAccountSnapshotCommandResponse(
            schema_version=1,
            replayed=result.replayed,
            request_id=request_id,
            snapshot=_snapshot_response(result.snapshot),
        )
        log_paper_account_snapshot_completed(
            request_id=request_id,
            http_status=status,
            account_id=result.snapshot.account_id,
            account_version=result.snapshot.account_version,
            snapshot_id=result.snapshot.snapshot_id,
            replayed=result.replayed,
        )
        return body
    except Exception as exc:
        _raise(exc, "snapshot")


@router.post(
    "/{account_id}/reconciliations",
    response_model=PaperAccountReconciliationCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.OK: {
            "model": PaperAccountReconciliationCommandResponse
        }
    },
)
def post_paper_account_reconciliation(
    account_id: AccountIdPath,
    request: Request,
    response: Response,
    command: PaperAccountEvidenceOperationRequest,
    service: PaperAccountService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperAccountReconciliationCommandResponse:
    try:
        result = service.reconcile_projection(
            account_id=account_id,
            expected_account_version=command.expected_account_version,
            expected_head_event_id=command.expected_head_event_id,
            expected_head_chain_digest=command.expected_head_chain_digest,
            operation_idempotency_key=_idempotency_key(idempotency_key),
            actor=command.actor,
            reason=command.reason,
        )
        status = _accepted_status(response, replayed=result.replayed)
        request_id = _request_id(request)
        body = PaperAccountReconciliationCommandResponse(
            schema_version=1,
            replayed=result.replayed,
            request_id=request_id,
            reconciliation=_reconciliation_response(
                result.reconciliation
            ),
        )
        projection_status = (
            "current"
            if result.reconciliation.outcome == "matched"
            else "reconciliation_required"
        )
        log_paper_account_reconciliation_completed(
            request_id=request_id,
            http_status=status,
            account_id=result.reconciliation.account_id,
            account_version=(
                result.reconciliation.authoritative_account_version
            ),
            reconciliation_id=result.reconciliation.reconciliation_id,
            outcome=result.reconciliation.outcome,
            replayed=result.replayed,
            projection_status=projection_status,
        )
        return body
    except Exception as exc:
        _raise(exc, "reconciliation")


__all__ = ["router"]
