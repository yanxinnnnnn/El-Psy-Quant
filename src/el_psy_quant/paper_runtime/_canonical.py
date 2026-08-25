"""Private strict canonical helpers for M35 durable runtime contracts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON keys are invalid")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON is invalid")


def load_canonical_json(value: object) -> object:
    if type(value) is not str:
        raise ValueError("canonical JSON must be a string")
    parsed = json.loads(
        value,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if canonical_json(parsed) != value:
        raise ValueError("JSON is not canonical")
    return parsed


def bounded_string(value: object, field: str, maximum: int) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{field} is invalid")
    return value


def digest(value: object, field: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def utc_datetime(value: object, field: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field} must be an exact UTC datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field} must be an exact UTC datetime") from exc
    if offset is None or offset.total_seconds() != 0:
        raise ValueError(f"{field} must be an exact UTC datetime")
    return value.astimezone(timezone.utc)


def non_negative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("paper runtime authority must be created by a factory")
