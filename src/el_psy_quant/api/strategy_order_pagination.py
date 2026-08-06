"""Opaque integrity-checked keyset cursors for M33 collection reads."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from el_psy_quant.api.strategy_order_errors import (
    StrategyOrderInvalidCursorError,
)

StrategyOrderCollection = Literal[
    "strategy_signals",
    "order_intents",
    "pre_trade_risk_decisions",
]

_CURSOR_SCHEMA_VERSION = 1
_MAX_CURSOR_LENGTH = 2048
_CURSOR_DIGEST_CONTEXT = b"el-psy-quant:strategy-order-list-cursor:v1\0"
_ID_PATTERNS = {
    "strategy_signals": re.compile(r"^sig_[0-9a-f]{64}$"),
    "order_intents": re.compile(r"^oi_[0-9a-f]{64}$"),
    "pre_trade_risk_decisions": re.compile(
        r"^risk_decision_[0-9a-f]{64}$"
    ),
}


@dataclass(frozen=True)
class StrategyOrderListCursor:
    collection_kind: StrategyOrderCollection
    created_at: datetime
    resource_id: str


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _checksum(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        _CURSOR_DIGEST_CONTEXT + _canonical_json(payload)
    ).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor field")
        result[key] = value
    return result


def _valid_identity(collection: str, value: object) -> str:
    pattern = _ID_PATTERNS.get(collection)
    if type(value) is not str or pattern is None or pattern.fullmatch(value) is None:
        raise ValueError("cursor resource identity is invalid")
    return value


def encode_strategy_order_list_cursor(
    *,
    collection_kind: StrategyOrderCollection,
    created_at: datetime,
    resource_id: str,
) -> str:
    """Encode one exact collection-specific durable ordering anchor."""
    if (
        collection_kind not in _ID_PATTERNS
        or type(created_at) is not datetime
        or created_at.tzinfo is not timezone.utc
    ):
        raise ValueError("strategy-order cursor anchor is invalid")
    identity = _valid_identity(collection_kind, resource_id)
    payload: dict[str, object] = {
        "schema_version": _CURSOR_SCHEMA_VERSION,
        "collection_kind": collection_kind,
        "created_at": created_at.isoformat(),
        "resource_id": identity,
    }
    envelope = {**payload, "checksum": _checksum(payload)}
    return base64.urlsafe_b64encode(_canonical_json(envelope)).decode(
        "ascii"
    ).rstrip("=")


def decode_strategy_order_list_cursor(
    value: object,
    *,
    expected_collection: StrategyOrderCollection,
) -> StrategyOrderListCursor:
    """Decode one canonical cursor and reject every alternate encoding."""
    try:
        if (
            type(value) is not str
            or not value
            or len(value) > _MAX_CURSOR_LENGTH
            or "=" in value
            or expected_collection not in _ID_PATTERNS
        ):
            raise ValueError("strategy-order cursor is invalid")
        padded = value + ("=" * (-len(value) % 4))
        raw = base64.b64decode(
            padded.encode("ascii"), altchars=b"-_", validate=True
        )
        envelope = json.loads(
            raw.decode("ascii"), object_pairs_hook=_unique_object
        )
        fields = {
            "schema_version",
            "collection_kind",
            "created_at",
            "resource_id",
            "checksum",
        }
        if type(envelope) is not dict or set(envelope) != fields:
            raise ValueError("strategy-order cursor is invalid")
        payload = {
            key: envelope[key]
            for key in (
                "schema_version",
                "collection_kind",
                "created_at",
                "resource_id",
            )
        }
        checksum = envelope["checksum"]
        if (
            type(payload["schema_version"]) is not int
            or payload["schema_version"] != _CURSOR_SCHEMA_VERSION
            or payload["collection_kind"] != expected_collection
            or type(checksum) is not str
            or len(checksum) != 64
            or not hmac.compare_digest(checksum, _checksum(payload))
            or _canonical_json(envelope) != raw
            or base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
            != value
        ):
            raise ValueError("strategy-order cursor is invalid")
        timestamp_value = payload["created_at"]
        if type(timestamp_value) is not str:
            raise ValueError("strategy-order cursor is invalid")
        timestamp = datetime.fromisoformat(timestamp_value)
        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
            or timestamp.utcoffset().total_seconds() != 0
        ):
            raise ValueError("strategy-order cursor is invalid")
        normalized = timestamp.astimezone(timezone.utc)
        if normalized.isoformat() != timestamp_value:
            raise ValueError("strategy-order cursor is invalid")
        identity = _valid_identity(
            expected_collection, payload["resource_id"]
        )
        return StrategyOrderListCursor(
            collection_kind=expected_collection,
            created_at=normalized,
            resource_id=identity,
        )
    except (
        UnicodeError,
        binascii.Error,
        json.JSONDecodeError,
        OverflowError,
        TypeError,
        ValueError,
    ) as exc:
        raise StrategyOrderInvalidCursorError() from exc


__all__ = [
    "StrategyOrderCollection",
    "StrategyOrderListCursor",
    "decode_strategy_order_list_cursor",
    "encode_strategy_order_list_cursor",
]
