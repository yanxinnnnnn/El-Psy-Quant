"""Private deterministic helpers for the pure M34 contract boundary."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def canonical_json(value: object) -> str:
    """Serialize one JSON-safe value with the project canonical convention."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_digest(value: object) -> str:
    """Return lowercase SHA-256 over canonical UTF-8 JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("paper execution authority must be created by a factory")


def normalize_bounded_string(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(normalized) > maximum_length:
        raise ValueError(f"{field_name} must be at most {maximum_length} characters")
    return normalized


def normalize_utc_datetime(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a timezone-aware datetime") from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a timezone-aware datetime") from exc


def validate_digest(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or _DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value
