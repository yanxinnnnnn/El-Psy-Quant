"""Strict durable paper-request codec and immutable paper-job records."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, TypeAlias, cast
from uuid import UUID

from el_psy_quant.paper import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PaperRunRequest,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_run_request,
)

PAPER_JOB_RECORD_SCHEMA_VERSION = 1

PaperJobStatus: TypeAlias = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "canceled",
]
SUPPORTED_PAPER_JOB_STATUSES: tuple[PaperJobStatus, ...] = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "canceled",
)
_LEGAL_PAPER_JOB_TRANSITIONS: frozenset[tuple[PaperJobStatus, PaperJobStatus]] = (
    frozenset(
        {
            ("queued", "running"),
            ("queued", "canceled"),
            ("running", "succeeded"),
            ("running", "failed"),
            ("running", "queued"),
            ("failed", "queued"),
        }
    )
)

_REQUEST_FIELDS = {
    "schema_version",
    "run_id",
    "created_timestamp",
    "starting_account_state",
    "ending_account_state",
    "orders",
    "fills",
}
_ACCOUNT_FIELDS = {"timestamp", "starting_cash", "current_cash", "positions"}
_POSITION_FIELDS = {"symbol", "quantity"}
_ORDER_FIELDS = {
    "order_id",
    "timestamp",
    "symbol",
    "side",
    "quantity",
    "status",
}
_FILL_FIELDS = {"timestamp", "symbol", "side", "quantity", "price"}


def _invalid_snapshot() -> ValueError:
    return ValueError("paper run request snapshot is invalid")


def _reject_json_constant(_value: str) -> None:
    raise _invalid_snapshot()


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _invalid_snapshot()
        result[key] = value
    return result


def _object(value: object, *, fields: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise _invalid_snapshot()
    return cast(dict[str, Any], value)


def _sequence(value: object) -> list[Any]:
    if type(value) is not list:
        raise _invalid_snapshot()
    return cast(list[Any], value)


def _schema_version(value: object) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value != PAPER_RUN_REQUEST_SCHEMA_VERSION
    ):
        raise _invalid_snapshot()


def _account_state(value: object):
    payload = _object(value, fields=_ACCOUNT_FIELDS)
    positions: dict[str, object] = {}
    for item in _sequence(payload["positions"]):
        position = _object(item, fields=_POSITION_FIELDS)
        symbol = position["symbol"]
        if not isinstance(symbol, str) or symbol in positions:
            raise _invalid_snapshot()
        positions[symbol] = position["quantity"]
    return create_paper_account_state(
        timestamp=payload["timestamp"],
        starting_cash=payload["starting_cash"],  # type: ignore[arg-type]
        current_cash=payload["current_cash"],  # type: ignore[arg-type]
        positions=positions,  # type: ignore[arg-type]
    )


def _orders(value: object):
    orders = []
    for item in _sequence(value):
        payload = _object(item, fields=_ORDER_FIELDS)
        orders.append(
            create_paper_order_record(
                order_id=payload["order_id"],  # type: ignore[arg-type]
                timestamp=payload["timestamp"],
                symbol=payload["symbol"],  # type: ignore[arg-type]
                side=payload["side"],  # type: ignore[arg-type]
                quantity=payload["quantity"],  # type: ignore[arg-type]
                status=payload["status"],  # type: ignore[arg-type]
            )
        )
    return orders


def _fills(value: object):
    fills = []
    for item in _sequence(value):
        if type(item) is not dict:
            raise _invalid_snapshot()
        fields = set(item)
        if fields not in (_FILL_FIELDS, _FILL_FIELDS | {"order_id"}):
            raise _invalid_snapshot()
        payload = cast(dict[str, Any], item)
        fills.append(
            create_paper_fill(
                timestamp=payload["timestamp"],
                symbol=payload["symbol"],  # type: ignore[arg-type]
                side=payload["side"],  # type: ignore[arg-type]
                quantity=payload["quantity"],  # type: ignore[arg-type]
                price=payload["price"],  # type: ignore[arg-type]
                order_id=payload.get("order_id"),  # type: ignore[arg-type]
            )
        )
    return fills


def serialize_paper_run_request(request: PaperRunRequest) -> str:
    """Serialize one validated request as deterministic canonical JSON."""
    if type(request) is not PaperRunRequest:
        raise ValueError("request must be a PaperRunRequest")
    return json.dumps(
        request.to_dict(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def deserialize_paper_run_request(payload: str) -> PaperRunRequest:
    """Strictly reconstruct one domain request without executing or doing I/O."""
    if not isinstance(payload, str):
        raise _invalid_snapshot()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
        request_payload = _object(value, fields=_REQUEST_FIELDS)
        _schema_version(request_payload["schema_version"])
        return create_paper_run_request(
            run_id=request_payload["run_id"],  # type: ignore[arg-type]
            created_timestamp=request_payload["created_timestamp"],
            starting_account_state=_account_state(
                request_payload["starting_account_state"]
            ),
            ending_account_state=_account_state(
                request_payload["ending_account_state"]
            ),
            orders=_orders(request_payload["orders"]),
            fills=_fills(request_payload["fills"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc) == str(_invalid_snapshot()):
            raise
        raise _invalid_snapshot() from exc


_PREPARED_REQUEST_TOKEN = object()


@dataclass(frozen=True, init=False)
class PreparedPaperRunRequest:
    """Codec-validated immutable request input for one persistence write."""

    request: PaperRunRequest
    _canonical_payload: str = field(repr=False)
    _validation_token: object = field(repr=False, compare=False)

    def __init__(self) -> None:
        raise TypeError(
            "PreparedPaperRunRequest must be created through the persistence factory"
        )


def prepare_paper_run_request_for_persistence(
    request: PaperRunRequest,
) -> PreparedPaperRunRequest:
    """Bind one validated request to its strict canonical storage payload."""
    canonical_payload = serialize_paper_run_request(request)
    prepared = object.__new__(PreparedPaperRunRequest)
    object.__setattr__(prepared, "request", request)
    object.__setattr__(prepared, "_canonical_payload", canonical_payload)
    object.__setattr__(prepared, "_validation_token", _PREPARED_REQUEST_TOKEN)
    return prepared


def digest_prepared_paper_run_request(
    prepared_request: PreparedPaperRunRequest,
) -> str:
    """Digest the exact codec-prepared canonical UTF-8 request payload."""
    if (
        type(prepared_request) is not PreparedPaperRunRequest
        or getattr(prepared_request, "_validation_token", None)
        is not _PREPARED_REQUEST_TOKEN
    ):
        raise ValueError("prepared request must come from the strict codec factory")
    return hashlib.sha256(
        prepared_request._canonical_payload.encode("utf-8")
    ).hexdigest()


def _prepared_payload_for_request(
    prepared_request: PreparedPaperRunRequest,
    *,
    request: PaperRunRequest,
) -> str:
    if (
        type(prepared_request) is not PreparedPaperRunRequest
        or getattr(prepared_request, "_validation_token", None)
        is not _PREPARED_REQUEST_TOKEN
    ):
        raise ValueError("prepared request must come from the strict codec factory")
    if prepared_request.request is not request:
        raise ValueError("prepared request must belong to the paper job request")
    return prepared_request._canonical_payload


def _job_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("job_id must be a canonical UUID string")
    try:
        parsed = UUID(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError("job_id must be a canonical UUID string") from exc
    if str(parsed) != value:
        raise ValueError("job_id must be a canonical UUID string")
    return value


def _run_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("run_id must be normalized")
    return value


def _status(value: object) -> PaperJobStatus:
    if not isinstance(value, str) or value not in SUPPORTED_PAPER_JOB_STATUSES:
        raise ValueError("paper job status is unsupported")
    return cast(PaperJobStatus, value)


def _utc_timestamp(value: object, *, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime") from exc
    if value.tzinfo is None or offset != timedelta(0):
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class PaperJobRecord:
    """Immutable durable operational input for one future paper runner."""

    record_schema_version: Literal[1]
    job_id: str
    run_id: str
    status: PaperJobStatus
    request: PaperRunRequest
    submitted_timestamp: datetime
    updated_timestamp: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(self.record_schema_version, int)
            or isinstance(self.record_schema_version, bool)
            or self.record_schema_version != PAPER_JOB_RECORD_SCHEMA_VERSION
        ):
            raise ValueError("record_schema_version must be 1")
        object.__setattr__(self, "job_id", _job_id(self.job_id))
        run_id = _run_id(self.run_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "status", _status(self.status))
        if type(self.request) is not PaperRunRequest:
            raise ValueError("request must be a PaperRunRequest")
        if run_id != self.request.run_id:
            raise ValueError("run_id must match request.run_id")
        submitted = _utc_timestamp(
            self.submitted_timestamp, field_name="submitted_timestamp"
        )
        updated = _utc_timestamp(self.updated_timestamp, field_name="updated_timestamp")
        if updated < submitted:
            raise ValueError("updated_timestamp must not precede submitted_timestamp")
        object.__setattr__(self, "submitted_timestamp", submitted)
        object.__setattr__(self, "updated_timestamp", updated)


def create_queued_paper_job_record(
    *,
    job_id: str,
    request: PaperRunRequest,
    submitted_timestamp: datetime,
) -> PaperJobRecord:
    """Create one queued record whose initial timestamps are identical."""
    return PaperJobRecord(
        record_schema_version=1,
        job_id=job_id,
        run_id=request.run_id,
        status="queued",
        request=request,
        submitted_timestamp=submitted_timestamp,
        updated_timestamp=submitted_timestamp,
    )


def _validate_paper_job_status_transition(
    current_status: PaperJobStatus,
    target_status: PaperJobStatus,
) -> None:
    if (current_status, target_status) not in _LEGAL_PAPER_JOB_TRANSITIONS:
        raise ValueError("paper job status transition is not allowed")


def transition_paper_job_record(
    *,
    job: PaperJobRecord,
    target_status: PaperJobStatus,
    updated_timestamp: datetime,
) -> PaperJobRecord:
    """Return one immutable record after an approved operational transition."""
    if type(job) is not PaperJobRecord:
        raise ValueError("job must be a PaperJobRecord")
    validated_target = _status(target_status)
    validated_timestamp = _utc_timestamp(
        updated_timestamp,
        field_name="updated_timestamp",
    )
    _validate_paper_job_status_transition(job.status, validated_target)
    if validated_timestamp < job.updated_timestamp:
        raise ValueError(
            "updated_timestamp must not precede the current updated_timestamp"
        )
    return replace(
        job,
        status=validated_target,
        updated_timestamp=validated_timestamp,
    )
