"""Request correlation and bounded local request-completion observability."""

from collections.abc import Callable
from time import monotonic
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from el_psy_quant.api.observability import (
    approved_route_template_for_path,
    bounded_duration_ms,
    log_api_request_completed,
    resolve_api_operation,
)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign a server UUID and emit one sanitized completion event."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__(app)
        self._clock = monotonic if clock is None else clock

    def _log_completion(
        self,
        *,
        request: Request,
        request_id: str,
        status_code: int,
        started: float,
        error_code: str | None,
    ) -> None:
        matched_route_template = approved_route_template_for_path(
            request.scope.get("path")
        )
        operation, route_template = resolve_api_operation(
            method=request.method,
            matched_route_template=matched_route_template,
        )
        log_api_request_completed(
            request_id=request_id,
            method=request.method,
            operation=operation,
            route_template=route_template,
            status_code=status_code,
            duration_ms=bounded_duration_ms(started, self._clock()),
            error_code=error_code,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        request.state.error_code = None
        started = self._clock()
        try:
            response = await call_next(request)
        except Exception:
            self._log_completion(
                request=request,
                request_id=request_id,
                status_code=500,
                started=started,
                error_code="internal_server_error",
            )
            raise
        response.headers[REQUEST_ID_HEADER] = request_id
        error_code = getattr(request.state, "error_code", None)
        self._log_completion(
            request=request,
            request_id=request_id,
            status_code=response.status_code,
            started=started,
            error_code=error_code if isinstance(error_code, str) else None,
        )
        return response
