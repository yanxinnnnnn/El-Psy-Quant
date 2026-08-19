"""Opaque integrity-checked cursors for M34 collection reads."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from el_psy_quant.api.paper_execution_errors import (
    PaperExecutionInvalidCursorError,
)

PaperExecutionCollection = Literal[
    "paper_execution_orders",
    "paper_execution_attempts",
    "paper_execution_fills",
]

_CURSOR_SCHEMA_VERSION = 1
_MAX_CURSOR_LENGTH = 2048
_CURSOR_DIGEST_CONTEXT = b"el-psy-quant:paper-execution-list-cursor:v1\0"
_QUERY_DIGEST_CONTEXT = b"el-psy-quant:paper-execution-query-context:v1\0"
_ID_PATTERNS = {
    "paper_execution_orders": re.compile(r"^peo_[0-9a-f]{64}$"),
    "paper_execution_attempts": re.compile(r"^pea_[0-9a-f]{64}$"),
    "paper_execution_fills": re.compile(r"^pef_[0-9a-f]{64}$"),
}
_ORDER_ID_PATTERN = re.compile(r"^peo_[0-9a-f]{64}$")


@dataclass(frozen=True)
class PaperExecutionListCursor:
    collection_kind: PaperExecutionCollection
    resource_id: str
    created_at: datetime | None
    execution_version_before: int | None
    execution_order_id: str | None
    version_anchor: int | None


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor field")
        result[key] = value
    return result


def _digest(context: bytes, payload: object) -> str:
    return hashlib.sha256(context + _canonical_json(payload)).hexdigest()


def _query_digest(
    collection_kind: PaperExecutionCollection,
    query_context: Mapping[str, str | None],
) -> str:
    if any(type(key) is not str for key in query_context):
        raise ValueError("cursor query context is invalid")
    if any(value is not None and type(value) is not str for value in query_context.values()):
        raise ValueError("cursor query context is invalid")
    return _digest(
        _QUERY_DIGEST_CONTEXT,
        {"collection_kind": collection_kind, "query": dict(query_context)},
    )


def _identity(collection_kind: str, value: object) -> str:
    pattern = _ID_PATTERNS.get(collection_kind)
    if type(value) is not str or pattern is None or pattern.fullmatch(value) is None:
        raise ValueError("cursor resource identity is invalid")
    return value


def encode_paper_execution_list_cursor(
    *,
    collection_kind: PaperExecutionCollection,
    resource_id: str,
    query_context: Mapping[str, str | None],
    created_at: datetime | None = None,
    execution_version_before: int | None = None,
    execution_order_id: str | None = None,
    version_anchor: int | None = None,
) -> str:
    """Encode one exact collection-specific ordering anchor."""
    identity = _identity(collection_kind, resource_id)
    is_attempt = collection_kind == "paper_execution_attempts"
    if is_attempt:
        if (
            created_at is not None
            or type(execution_version_before) is not int
            or execution_version_before < 0
            or type(execution_order_id) is not str
            or _ORDER_ID_PATTERN.fullmatch(execution_order_id) is None
            or type(version_anchor) is not int
            or version_anchor < 0
            or execution_version_before >= version_anchor
        ):
            raise ValueError("Attempt cursor anchor is invalid")
    elif (
        type(created_at) is not datetime
        or created_at.tzinfo is not timezone.utc
        or execution_version_before is not None
        or execution_order_id is not None
        or version_anchor is not None
    ):
        raise ValueError("Paper Execution cursor anchor is invalid")
    payload: dict[str, object] = {
        "schema_version": _CURSOR_SCHEMA_VERSION,
        "collection_kind": collection_kind,
        "resource_id": identity,
        "created_at": None if created_at is None else created_at.isoformat(),
        "execution_version_before": execution_version_before,
        "execution_order_id": execution_order_id,
        "version_anchor": version_anchor,
        "query_digest": _query_digest(collection_kind, query_context),
    }
    envelope = {
        **payload,
        "checksum": _digest(_CURSOR_DIGEST_CONTEXT, payload),
    }
    return base64.urlsafe_b64encode(_canonical_json(envelope)).decode("ascii").rstrip("=")


def decode_paper_execution_list_cursor(
    value: object,
    *,
    expected_collection: PaperExecutionCollection,
    query_context: Mapping[str, str | None],
) -> PaperExecutionListCursor:
    """Decode one canonical cursor and reject all alternate encodings."""
    try:
        if (
            type(value) is not str
            or not value
            or len(value) > _MAX_CURSOR_LENGTH
            or "=" in value
            or expected_collection not in _ID_PATTERNS
        ):
            raise ValueError("Paper Execution cursor is invalid")
        padded = value + ("=" * (-len(value) % 4))
        raw = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
        envelope = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_object)
        fields = {
            "schema_version",
            "collection_kind",
            "resource_id",
            "created_at",
            "execution_version_before",
            "execution_order_id",
            "version_anchor",
            "query_digest",
            "checksum",
        }
        if type(envelope) is not dict or set(envelope) != fields:
            raise ValueError("Paper Execution cursor is invalid")
        payload = {key: envelope[key] for key in fields - {"checksum"}}
        checksum = envelope["checksum"]
        if (
            type(payload["schema_version"]) is not int
            or payload["schema_version"] != _CURSOR_SCHEMA_VERSION
            or payload["collection_kind"] != expected_collection
            or payload["query_digest"]
            != _query_digest(expected_collection, query_context)
            or type(checksum) is not str
            or len(checksum) != 64
            or not hmac.compare_digest(
                checksum, _digest(_CURSOR_DIGEST_CONTEXT, payload)
            )
            or _canonical_json(envelope) != raw
            or base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value
        ):
            raise ValueError("Paper Execution cursor is invalid")
        identity = _identity(expected_collection, payload["resource_id"])
        if expected_collection == "paper_execution_attempts":
            version = payload["execution_version_before"]
            order_id = payload["execution_order_id"]
            anchor = payload["version_anchor"]
            if (
                payload["created_at"] is not None
                or type(version) is not int
                or version < 0
                or type(order_id) is not str
                or _ORDER_ID_PATTERN.fullmatch(order_id) is None
                or type(anchor) is not int
                or anchor < 0
                or version >= anchor
            ):
                raise ValueError("Attempt cursor is invalid")
            return PaperExecutionListCursor(
                collection_kind=expected_collection,
                resource_id=identity,
                created_at=None,
                execution_version_before=version,
                execution_order_id=order_id,
                version_anchor=anchor,
            )
        if any(
            payload[field] is not None
            for field in (
                "execution_version_before",
                "execution_order_id",
                "version_anchor",
            )
        ):
            raise ValueError("Paper Execution cursor is invalid")
        timestamp_value = payload["created_at"]
        if type(timestamp_value) is not str:
            raise ValueError("Paper Execution cursor timestamp is invalid")
        timestamp = datetime.fromisoformat(timestamp_value)
        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
            or timestamp.utcoffset().total_seconds() != 0
        ):
            raise ValueError("Paper Execution cursor timestamp is invalid")
        normalized = timestamp.astimezone(timezone.utc)
        if normalized.isoformat() != timestamp_value:
            raise ValueError("Paper Execution cursor timestamp is invalid")
        return PaperExecutionListCursor(
            collection_kind=expected_collection,
            resource_id=identity,
            created_at=normalized,
            execution_version_before=None,
            execution_order_id=None,
            version_anchor=None,
        )
    except (
        UnicodeError,
        binascii.Error,
        json.JSONDecodeError,
        OverflowError,
        TypeError,
        ValueError,
    ) as exc:
        raise PaperExecutionInvalidCursorError() from exc


__all__ = [
    "PaperExecutionCollection",
    "PaperExecutionListCursor",
    "decode_paper_execution_list_cursor",
    "encode_paper_execution_list_cursor",
]
