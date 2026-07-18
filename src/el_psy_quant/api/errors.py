"""Small explicit exception-to-API translation boundary."""

from collections.abc import Mapping
from http import HTTPStatus
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import ApiError, ApiErrorResponse


class PublicApiError(Exception):
    """Small explicit public error translated through the stable envelope."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else str(uuid4())


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    request.state.error_code = code
    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = request_id
    body = ApiErrorResponse(
        error=ApiError(code=code, message=message),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers=response_headers,
    )


async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
) -> JSONResponse:
    """Translate framework HTTP errors into the stable public envelope."""
    codes = {
        HTTPStatus.NOT_FOUND: "not_found",
        HTTPStatus.METHOD_NOT_ALLOWED: "method_not_allowed",
    }
    code = codes.get(exception.status_code, "http_error")
    try:
        message = HTTPStatus(exception.status_code).phrase
    except ValueError:
        message = "HTTP Error"
    return _error_response(
        request,
        status_code=exception.status_code,
        code=code,
        message=message,
        headers=exception.headers,
    )


async def request_validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Return a stable response without exposing validation internals."""
    del exception
    return _error_response(
        request,
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="request_validation_error",
        message="Request Validation Error",
    )


async def unexpected_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Sanitize unexpected failures at the public API boundary."""
    del exception
    return _error_response(
        request,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="Internal Server Error",
    )


async def public_api_error_handler(
    request: Request,
    exception: PublicApiError,
) -> JSONResponse:
    """Return one explicitly sanitized application-facing error."""
    return _error_response(
        request,
        status_code=exception.status_code,
        code=exception.code,
        message=exception.message,
        headers=exception.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the bounded Sprint 138 exception mappings."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(PublicApiError, public_api_error_handler)
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )
    app.add_exception_handler(Exception, unexpected_exception_handler)
