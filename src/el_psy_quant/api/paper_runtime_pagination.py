"""Opaque integrity-checked cursors for bounded M35 runtime collections."""

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

from el_psy_quant.api.paper_runtime_errors import PaperRuntimeInvalidCursorError

PaperRuntimeCollection = Literal[
    "paper_runtimes",
    "paper_runtime_audit",
    "paper_runtime_work",
    "paper_runtime_checkpoints",
]

_MAX_CURSOR_LENGTH = 2048
_DIGEST_CONTEXT = b"el-psy-quant:paper-runtime-list-cursor:v1\0"
_QUERY_CONTEXT = b"el-psy-quant:paper-runtime-query-context:v1\0"
_PATTERNS = {
    "paper_runtimes": re.compile(r"^prt_[0-9a-f]{64}$"),
    "paper_runtime_audit": re.compile(r"^pre_[0-9a-f]{64}$"),
    "paper_runtime_work": re.compile(r"^prw_[0-9a-f]{64}$"),
    "paper_runtime_checkpoints": re.compile(r"^prc_[0-9a-f]{64}$"),
}


@dataclass(frozen=True)
class PaperRuntimeListCursor:
    collection_kind: PaperRuntimeCollection
    resource_id: str
    created_at: datetime | None
    position: int | None


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


def _digest(context: bytes, value: object) -> str:
    return hashlib.sha256(context + _canonical_json(value)).hexdigest()


def _query_digest(
    collection: PaperRuntimeCollection, query: Mapping[str, str | None]
) -> str:
    if any(type(key) is not str for key in query) or any(
        value is not None and type(value) is not str for value in query.values()
    ):
        raise ValueError("runtime cursor query context is invalid")
    return _digest(_QUERY_CONTEXT, {"collection": collection, "query": dict(query)})


def _identity(collection: PaperRuntimeCollection, value: object) -> str:
    if type(value) is not str or _PATTERNS[collection].fullmatch(value) is None:
        raise ValueError("runtime cursor identity is invalid")
    return value


def encode_paper_runtime_list_cursor(
    *,
    collection_kind: PaperRuntimeCollection,
    resource_id: str,
    query_context: Mapping[str, str | None],
    created_at: datetime | None = None,
    position: int | None = None,
) -> str:
    identity = _identity(collection_kind, resource_id)
    if collection_kind == "paper_runtimes":
        if (
            type(created_at) is not datetime
            or created_at.tzinfo is None
            or created_at.utcoffset() is None
            or created_at.utcoffset().total_seconds() != 0
            or position is not None
        ):
            raise ValueError("runtime cursor anchor is invalid")
    elif created_at is not None or type(position) is not int or position < 0:
        raise ValueError("runtime evidence cursor anchor is invalid")
    payload = {
        "schema_version": 1,
        "collection_kind": collection_kind,
        "resource_id": identity,
        "created_at": None if created_at is None else created_at.isoformat(),
        "position": position,
        "query_digest": _query_digest(collection_kind, query_context),
    }
    envelope = {**payload, "checksum": _digest(_DIGEST_CONTEXT, payload)}
    return base64.urlsafe_b64encode(_canonical_json(envelope)).decode("ascii").rstrip("=")


def decode_paper_runtime_list_cursor(
    value: object,
    *,
    expected_collection: PaperRuntimeCollection,
    query_context: Mapping[str, str | None],
) -> PaperRuntimeListCursor:
    try:
        if (
            type(value) is not str
            or not value
            or len(value) > _MAX_CURSOR_LENGTH
            or "=" in value
            or expected_collection not in _PATTERNS
        ):
            raise ValueError("runtime cursor is invalid")
        raw = base64.b64decode(
            (value + "=" * (-len(value) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        envelope = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_object)
        fields = {
            "schema_version",
            "collection_kind",
            "resource_id",
            "created_at",
            "position",
            "query_digest",
            "checksum",
        }
        if type(envelope) is not dict or set(envelope) != fields:
            raise ValueError("runtime cursor fields are invalid")
        payload = {key: envelope[key] for key in fields - {"checksum"}}
        if (
            payload["schema_version"] != 1
            or payload["collection_kind"] != expected_collection
            or payload["query_digest"]
            != _query_digest(expected_collection, query_context)
            or type(envelope["checksum"]) is not str
            or not hmac.compare_digest(
                envelope["checksum"], _digest(_DIGEST_CONTEXT, payload)
            )
            or _canonical_json(envelope) != raw
            or base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value
        ):
            raise ValueError("runtime cursor integrity is invalid")
        identity = _identity(expected_collection, payload["resource_id"])
        if expected_collection == "paper_runtimes":
            if payload["position"] is not None or type(payload["created_at"]) is not str:
                raise ValueError("runtime cursor anchor is invalid")
            timestamp = datetime.fromisoformat(payload["created_at"])
            if (
                timestamp.tzinfo is None
                or timestamp.utcoffset() is None
                or timestamp.utcoffset().total_seconds() != 0
            ):
                raise ValueError("runtime cursor timestamp is invalid")
            normalized = timestamp.astimezone(timezone.utc)
            if normalized.isoformat() != payload["created_at"]:
                raise ValueError("runtime cursor timestamp is not canonical")
            return PaperRuntimeListCursor(
                collection_kind=expected_collection,
                resource_id=identity,
                created_at=normalized,
                position=None,
            )
        position = payload["position"]
        if payload["created_at"] is not None or type(position) is not int or position < 0:
            raise ValueError("runtime evidence cursor anchor is invalid")
        return PaperRuntimeListCursor(
            collection_kind=expected_collection,
            resource_id=identity,
            created_at=None,
            position=position,
        )
    except (
        UnicodeError,
        binascii.Error,
        json.JSONDecodeError,
        OverflowError,
        TypeError,
        ValueError,
    ) as exc:
        raise PaperRuntimeInvalidCursorError() from exc


__all__ = [
    "PaperRuntimeCollection",
    "PaperRuntimeListCursor",
    "decode_paper_runtime_list_cursor",
    "encode_paper_runtime_list_cursor",
]
