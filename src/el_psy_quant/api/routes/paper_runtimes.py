"""Exactly twelve authenticated versioned M35 Paper Runtime operations."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from el_psy_quant.api.dependencies import (
    get_paper_runtime_inspection_service,
    get_paper_runtime_lifecycle_service,
)
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.observability import log_paper_runtime_event
from el_psy_quant.api.paper_runtime_errors import (
    PaperRuntimeApiOperation,
    raise_paper_runtime_api_error,
)
from el_psy_quant.api.paper_runtime_pagination import (
    decode_paper_runtime_list_cursor,
    encode_paper_runtime_list_cursor,
)
from el_psy_quant.api.paper_runtime_schemas import (
    DesiredState,
    ObservedState,
    PaperRuntimeAuditEntryResponse,
    PaperRuntimeAuditListResponse,
    PaperRuntimeCheckpointListResponse,
    PaperRuntimeCheckpointResponse,
    PaperRuntimeCommandResponse,
    PaperRuntimeControlRequest,
    PaperRuntimeCreateRequest,
    PaperRuntimeHealthResponse,
    PaperRuntimeListResponse,
    PaperRuntimeReconciliationResponse,
    PaperRuntimeResponse,
    PaperRuntimeWorkListResponse,
    PaperRuntimeWorkResponse,
    RuntimeId,
)
from el_psy_quant.api.schemas import ApiErrorResponse
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeLifecycleResult,
    PaperRuntimeLifecycleService,
)
from el_psy_quant.application.paper_runtime_inspection import (
    PaperRuntimeInspectionService,
)
from el_psy_quant.persistence.paper_execution_records import (
    PaperExecutionCorruptAuthorityError,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PaperRuntimePersistenceCorruptionError,
)

router = APIRouter(prefix="/paper-runtimes")
LifecycleService = Annotated[
    PaperRuntimeLifecycleService, Depends(get_paper_runtime_lifecycle_service)
]
InspectionService = Annotated[
    PaperRuntimeInspectionService, Depends(get_paper_runtime_inspection_service)
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
RuntimeIdPath = Annotated[RuntimeId, Path(pattern=r"^prt_[0-9a-f]{64}$")]
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


def _runtime_response(value) -> PaperRuntimeResponse:
    return PaperRuntimeResponse.model_validate(value.to_dict())


def _accepted_status(response: Response, *, replayed: bool) -> int:
    status = HTTPStatus.OK if replayed else HTTPStatus.CREATED
    response.status_code = status
    return status


def _command_response(
    *,
    request: Request,
    response: Response,
    operation: PaperRuntimeApiOperation,
    result: PaperRuntimeLifecycleResult,
) -> PaperRuntimeCommandResponse:
    status = _accepted_status(response, replayed=result.replayed)
    request_id = _request_id(request)
    event = (
        "paper_runtime_idempotent_replay"
        if result.replayed
        else {
            "create": "paper_runtime_created",
            "start": "paper_runtime_start_requested",
            "stop": "paper_runtime_stop_requested",
            "resume": "paper_runtime_resume_requested",
            "recover": "paper_runtime_recover_requested",
        }[operation]
    )
    log_paper_runtime_event(
        event=event,
        request_id=request_id,
        operation=operation,
        http_status=status,
        runtime_id=result.runtime.runtime_id,
        desired_state=result.runtime.desired_state,
        observed_state=result.runtime.observed_state,
        row_version=result.runtime.row_version,
        fencing_token=result.runtime.fencing_token,
        replayed=result.replayed,
    )
    return PaperRuntimeCommandResponse(
        schema_version=1,
        replayed=result.replayed,
        request_id=request_id,
        runtime=_runtime_response(result.runtime),
    )


def _raise(
    exc: Exception,
    *,
    request: Request,
    operation: PaperRuntimeApiOperation,
    runtime_id: str | None = None,
) -> None:
    if isinstance(
        exc,
        (PaperRuntimePersistenceCorruptionError, PaperExecutionCorruptAuthorityError),
    ):
        event = "paper_runtime_corruption_refused"
        status = HTTPStatus.SERVICE_UNAVAILABLE
    elif operation in {"create", "start", "stop", "resume", "recover"}:
        try:
            raise_paper_runtime_api_error(exc, operation=operation)
        except PublicApiError as public:
            log_paper_runtime_event(
                event="paper_runtime_lifecycle_refused",
                request_id=_request_id(request),
                operation=operation,
                http_status=public.status_code,
                runtime_id=runtime_id,
            )
            raise public from exc
    else:
        raise_paper_runtime_api_error(exc, operation=operation)
    log_paper_runtime_event(
        event=event,
        request_id=_request_id(request),
        operation=operation,
        http_status=status,
        runtime_id=runtime_id,
    )
    raise_paper_runtime_api_error(exc, operation=operation)


@router.post(
    "",
    response_model=PaperRuntimeCommandResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_paper_runtime_v1",
    responses={
        HTTPStatus.OK: {"model": PaperRuntimeCommandResponse},
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def create_paper_runtime_v1(
    request: Request,
    response: Response,
    command: PaperRuntimeCreateRequest,
    service: LifecycleService,
    idempotency_key: IdempotencyKeyHeader,
) -> PaperRuntimeCommandResponse:
    try:
        result = service.create_runtime(
            execution_order_id=command.execution_order_id,
            execution_order_digest=command.execution_order_digest,
            logical_actor=command.logical_actor,
            runtime_policy_id=command.runtime_policy_id,
            runtime_policy_version=command.runtime_policy_version,
            command_idempotency_key=idempotency_key,
            command_actor=command.actor,
        )
        return _command_response(
            request=request, response=response, operation="create", result=result
        )
    except Exception as exc:
        _raise(exc, request=request, operation="create")


@router.get(
    "",
    response_model=PaperRuntimeListResponse,
    operation_id="list_paper_runtimes_v1",
    responses={
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_runtimes_v1(
    request: Request,
    service: InspectionService,
    account_id: BoundedFilter | None = None,
    replay_id: BoundedFilter | None = None,
    trading_session_id: BoundedFilter | None = None,
    desired_state: Annotated[DesiredState | None, Query()] = None,
    observed_state: Annotated[ObservedState | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperRuntimeListResponse:
    context = {
        "account_id": account_id,
        "replay_id": replay_id,
        "trading_session_id": trading_session_id,
        "desired_state": desired_state,
        "observed_state": observed_state,
    }
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_runtime_list_cursor(
                cursor,
                expected_collection="paper_runtimes",
                query_context=context,
            )
        )
        page = service.list_runtimes(
            limit=limit,
            cursor_created_at=None if decoded is None else decoded.created_at,
            cursor_runtime_id=None if decoded is None else decoded.resource_id,
            account_id=account_id,
            replay_id=replay_id,
            trading_session_id=trading_session_id,
            desired_state=desired_state,
            observed_state=observed_state,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_runtime_list_cursor(
                collection_kind="paper_runtimes",
                resource_id=last.runtime_id,
                created_at=last.created_at,
                query_context=context,
            )
        return PaperRuntimeListResponse(
            schema_version=1,
            items=[_runtime_response(item) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="list")


@router.get(
    "/{runtime_id}",
    response_model=PaperRuntimeResponse,
    operation_id="get_paper_runtime_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_runtime_v1(
    request: Request, runtime_id: RuntimeIdPath, service: InspectionService
) -> PaperRuntimeResponse:
    try:
        return _runtime_response(service.get_runtime(runtime_id=runtime_id))
    except Exception as exc:
        _raise(exc, request=request, operation="detail", runtime_id=runtime_id)


def _control(
    *,
    request: Request,
    response: Response,
    runtime_id: str,
    command: PaperRuntimeControlRequest,
    service: PaperRuntimeLifecycleService,
    idempotency_key: str,
    operation: PaperRuntimeApiOperation,
    method: Callable[..., PaperRuntimeLifecycleResult],
) -> PaperRuntimeCommandResponse:
    try:
        result = method(
            runtime_id=runtime_id,
            runtime_binding_digest=command.runtime_binding_digest,
            expected_runtime_version=command.expected_runtime_version,
            command_idempotency_key=idempotency_key,
            command_actor=command.actor,
        )
        return _command_response(
            request=request,
            response=response,
            operation=operation,
            result=result,
        )
    except Exception as exc:
        _raise(exc, request=request, operation=operation, runtime_id=runtime_id)


def _control_route(operation: str) -> Callable:
    def endpoint(
        request: Request,
        response: Response,
        runtime_id: RuntimeIdPath,
        command: PaperRuntimeControlRequest,
        service: LifecycleService,
        idempotency_key: IdempotencyKeyHeader,
    ) -> PaperRuntimeCommandResponse:
        method = getattr(service, f"{operation}_runtime")
        return _control(
            request=request,
            response=response,
            runtime_id=runtime_id,
            command=command,
            service=service,
            idempotency_key=idempotency_key,
            operation=operation,
            method=method,
        )

    endpoint.__name__ = f"{operation}_paper_runtime_v1"
    return endpoint


for _operation in ("start", "stop", "resume", "recover"):
    router.add_api_route(
        "/{runtime_id}/" + _operation,
        _control_route(_operation),
        methods=["POST"],
        response_model=PaperRuntimeCommandResponse,
        status_code=HTTPStatus.CREATED,
        operation_id=f"{_operation}_paper_runtime_v1",
        responses={
            HTTPStatus.OK: {"model": PaperRuntimeCommandResponse},
            HTTPStatus.NOT_FOUND: _ERROR_404,
            HTTPStatus.CONFLICT: _ERROR_409,
            HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
            HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
        },
    )


@router.get(
    "/{runtime_id}/health",
    response_model=PaperRuntimeHealthResponse,
    operation_id="get_paper_runtime_health_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_runtime_health_v1(
    request: Request, runtime_id: RuntimeIdPath, service: InspectionService
) -> PaperRuntimeHealthResponse:
    try:
        health = service.get_health(runtime_id=runtime_id)
        runtime = health.runtime
        log_paper_runtime_event(
            event="paper_runtime_health_checked",
            request_id=_request_id(request),
            operation="health",
            http_status=HTTPStatus.OK,
            runtime_id=runtime.runtime_id,
            desired_state=runtime.desired_state,
            observed_state=runtime.observed_state,
            row_version=runtime.row_version,
            fencing_token=runtime.fencing_token,
            outcome=health.lease_status,
        )
        return PaperRuntimeHealthResponse(
            schema_version=1,
            runtime_id=runtime.runtime_id,
            desired_state=runtime.desired_state,
            observed_state=runtime.observed_state,
            row_version=runtime.row_version,
            fencing_token=runtime.fencing_token,
            claimed=health.claimed,
            lease_status=health.lease_status,
            claimed_at=runtime.claimed_at,
            heartbeat_at=runtime.heartbeat_at,
            lease_expires_at=runtime.lease_expires_at,
            terminal=health.terminal,
            blocked=health.blocked,
            block_reason_code=runtime.block_reason_code,
            checked_at=health.checked_at,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="health", runtime_id=runtime_id)


@router.get(
    "/{runtime_id}/reconciliation",
    response_model=PaperRuntimeReconciliationResponse,
    operation_id="get_paper_runtime_reconciliation_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.CONFLICT: _ERROR_409,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def get_paper_runtime_reconciliation_v1(
    request: Request, runtime_id: RuntimeIdPath, service: InspectionService
) -> PaperRuntimeReconciliationResponse:
    try:
        result = service.reconcile_runtime(runtime_id=runtime_id)
        runtime = result.runtime
        log_paper_runtime_event(
            event="paper_runtime_reconciliation_checked",
            request_id=_request_id(request),
            operation="reconciliation",
            http_status=HTTPStatus.OK,
            runtime_id=runtime.runtime_id,
            desired_state=runtime.desired_state,
            observed_state=runtime.observed_state,
            row_version=runtime.row_version,
            fencing_token=runtime.fencing_token,
            outcome=result.status,
        )
        return PaperRuntimeReconciliationResponse(
            schema_version=1,
            runtime_id=runtime.runtime_id,
            runtime_binding_digest=runtime.runtime_binding_digest,
            status=result.status,
            historical_coherent=True,
            continuation_status=result.continuation_status,
            execution_order_id=runtime.execution_order_id,
            execution_order_digest=runtime.execution_order_digest,
            execution_version=result.execution_version,
            execution_terminal=result.execution_terminal,
            work_count=result.work_count,
            checkpoint_count=result.checkpoint_count,
            event_count=result.event_count,
            pending_work_id=result.pending_work_id,
        )
    except Exception as exc:
        _raise(
            exc,
            request=request,
            operation="reconciliation",
            runtime_id=runtime_id,
        )


def _runtime_context(runtime_id: str) -> dict[str, str | None]:
    return {"runtime_id": runtime_id}


@router.get(
    "/{runtime_id}/audit",
    response_model=PaperRuntimeAuditListResponse,
    operation_id="list_paper_runtime_audit_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_runtime_audit_v1(
    request: Request,
    runtime_id: RuntimeIdPath,
    service: InspectionService,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperRuntimeAuditListResponse:
    context = _runtime_context(runtime_id)
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_runtime_list_cursor(
                cursor,
                expected_collection="paper_runtime_audit",
                query_context=context,
            )
        )
        page = service.list_audit(
            runtime_id=runtime_id,
            limit=limit,
            cursor_event_sequence=None if decoded is None else decoded.position,
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_runtime_list_cursor(
                collection_kind="paper_runtime_audit",
                resource_id=last.event.event_id,
                position=last.event.event_sequence,
                query_context=context,
            )
        return PaperRuntimeAuditListResponse(
            schema_version=1,
            items=[
                PaperRuntimeAuditEntryResponse(
                    schema_version=1,
                    event_id=item.event.event_id,
                    event_digest=item.event.event_digest,
                    runtime_id=item.event.runtime_id,
                    event_sequence=item.event.event_sequence,
                    event_type=item.event.event_type,
                    resulting_runtime_version=item.event.resulting_runtime_version,
                    recorded_at=item.event.recorded_at,
                    work_id=item.work_id,
                    checkpoint_id=item.checkpoint_id,
                )
                for item in page.items
            ],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="audit", runtime_id=runtime_id)


@router.get(
    "/{runtime_id}/work",
    response_model=PaperRuntimeWorkListResponse,
    operation_id="list_paper_runtime_work_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_runtime_work_v1(
    request: Request,
    runtime_id: RuntimeIdPath,
    service: InspectionService,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperRuntimeWorkListResponse:
    context = _runtime_context(runtime_id)
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_runtime_list_cursor(
                cursor,
                expected_collection="paper_runtime_work",
                query_context=context,
            )
        )
        page = service.list_work(
            runtime_id=runtime_id,
            limit=limit,
            cursor_expected_execution_version=(
                None if decoded is None else decoded.position
            ),
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_runtime_list_cursor(
                collection_kind="paper_runtime_work",
                resource_id=last.work_id,
                position=last.expected_execution_version,
                query_context=context,
            )
        return PaperRuntimeWorkListResponse(
            schema_version=1,
            items=[PaperRuntimeWorkResponse.model_validate(item.to_dict()) for item in page.items],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="work", runtime_id=runtime_id)


@router.get(
    "/{runtime_id}/checkpoints",
    response_model=PaperRuntimeCheckpointListResponse,
    operation_id="list_paper_runtime_checkpoints_v1",
    responses={
        HTTPStatus.NOT_FOUND: _ERROR_404,
        HTTPStatus.UNPROCESSABLE_ENTITY: _ERROR_422,
        HTTPStatus.SERVICE_UNAVAILABLE: _ERROR_503,
    },
)
def list_paper_runtime_checkpoints_v1(
    request: Request,
    runtime_id: RuntimeIdPath,
    service: InspectionService,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> PaperRuntimeCheckpointListResponse:
    context = _runtime_context(runtime_id)
    try:
        decoded = (
            None
            if cursor is None
            else decode_paper_runtime_list_cursor(
                cursor,
                expected_collection="paper_runtime_checkpoints",
                query_context=context,
            )
        )
        page = service.list_checkpoints(
            runtime_id=runtime_id,
            limit=limit,
            cursor_observed_execution_version=(
                None if decoded is None else decoded.position
            ),
        )
        next_cursor = None
        if page.has_more:
            last = page.items[-1]
            next_cursor = encode_paper_runtime_list_cursor(
                collection_kind="paper_runtime_checkpoints",
                resource_id=last.checkpoint_id,
                position=last.observed_execution_version,
                query_context=context,
            )
        return PaperRuntimeCheckpointListResponse(
            schema_version=1,
            items=[
                PaperRuntimeCheckpointResponse.model_validate(item.to_dict())
                for item in page.items
            ],
            next_cursor=next_cursor,
        )
    except Exception as exc:
        _raise(exc, request=request, operation="checkpoints", runtime_id=runtime_id)


__all__ = ["router"]
