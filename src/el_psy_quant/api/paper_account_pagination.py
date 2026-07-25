"""Opaque integrity-checked keyset cursors for Paper Account listing."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from el_psy_quant.paper_account._shared import normalize_bounded_string

_CURSOR_SCHEMA_VERSION = 1
_MAX_CURSOR_LENGTH = 2048
_CURSOR_DIGEST_CONTEXT = b"el-psy-quant:paper-account-list-cursor:v1\0"


@dataclass(frozen=True)
class PaperAccountListCursor:
    created_timestamp: datetime
    account_id: str


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


def encode_paper_account_list_cursor(
    *,
    created_timestamp: datetime,
    account_id: str,
) -> str:
    """Encode only the validated durable ordering anchors."""
    if (
        type(created_timestamp) is not datetime
        or created_timestamp.tzinfo is not timezone.utc
    ):
        raise ValueError("cursor timestamp must be normalized to UTC")
    normalized_account_id = normalize_bounded_string(
        account_id,
        field_name="cursor account ID",
        maximum_length=512,
    )
    if normalized_account_id != account_id:
        raise ValueError("cursor account ID must already be normalized")
    payload: dict[str, object] = {
        "schema_version": _CURSOR_SCHEMA_VERSION,
        "created_timestamp": created_timestamp.isoformat(),
        "account_id": account_id,
    }
    envelope = {
        "checksum": _checksum(payload),
        "payload": payload,
    }
    return base64.urlsafe_b64encode(_canonical_json(envelope)).decode(
        "ascii"
    ).rstrip("=")


def decode_paper_account_list_cursor(value: object) -> PaperAccountListCursor:
    """Decode one exact server-produced cursor or reject it entirely."""
    try:
        if (
            type(value) is not str
            or not value
            or len(value) > _MAX_CURSOR_LENGTH
            or "=" in value
        ):
            raise ValueError("paper account cursor is invalid")
        padded = value + ("=" * (-len(value) % 4))
        raw = base64.b64decode(
            padded.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        envelope = json.loads(raw.decode("ascii"))
        if (
            type(envelope) is not dict
            or set(envelope) != {"checksum", "payload"}
            or type(envelope["checksum"]) is not str
            or type(envelope["payload"]) is not dict
        ):
            raise ValueError("paper account cursor is invalid")
        payload = envelope["payload"]
        if set(payload) != {
            "schema_version",
            "created_timestamp",
            "account_id",
        }:
            raise ValueError("paper account cursor is invalid")
        if (
            type(payload["schema_version"]) is not int
            or payload["schema_version"] != _CURSOR_SCHEMA_VERSION
            or not hmac.compare_digest(
                envelope["checksum"],
                _checksum(payload),
            )
            or _canonical_json(envelope) != raw
        ):
            raise ValueError("paper account cursor is invalid")
        timestamp_value = payload["created_timestamp"]
        if type(timestamp_value) is not str:
            raise ValueError("paper account cursor is invalid")
        timestamp = datetime.fromisoformat(timestamp_value)
        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
            or timestamp.utcoffset().total_seconds() != 0
        ):
            raise ValueError("paper account cursor is invalid")
        normalized_timestamp = timestamp.astimezone(timezone.utc)
        if normalized_timestamp.isoformat() != timestamp_value:
            raise ValueError("paper account cursor is invalid")
        account_id = normalize_bounded_string(
            payload["account_id"],
            field_name="cursor account ID",
            maximum_length=512,
        )
        if account_id != payload["account_id"]:
            raise ValueError("paper account cursor is invalid")
        return PaperAccountListCursor(
            created_timestamp=normalized_timestamp,
            account_id=account_id,
        )
    except (
        UnicodeError,
        binascii.Error,
        json.JSONDecodeError,
        OverflowError,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError("paper account cursor is invalid") from exc


__all__ = [
    "PaperAccountListCursor",
    "decode_paper_account_list_cursor",
    "encode_paper_account_list_cursor",
]
