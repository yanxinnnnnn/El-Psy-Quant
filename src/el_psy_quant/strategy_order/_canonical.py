"""Private canonicalization helpers for pure M33 domain contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

_LOWERCASE_HEXADECIMAL = frozenset("0123456789abcdef")


def canonical_digest(payload: dict[str, object]) -> str:
    """Return lowercase SHA-256 over the approved canonical JSON form."""
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_bounded_string(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    """Normalize one required bounded string without silent truncation."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must be at most {maximum_length} characters"
        )
    return normalized


def normalize_utc_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    """Require a timezone-aware datetime and normalize it to UTC."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime"
        ) from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime"
        ) from exc


def validate_digest(value: object, *, field_name: str) -> str:
    """Validate one exact lowercase SHA-256 hexadecimal digest."""
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEXADECIMAL for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def reject_public_construction(*args: object, **kwargs: object) -> None:
    """Block callers from bypassing a trusted domain factory."""
    del args, kwargs
    raise TypeError("authority values must be created with a trusted factory")
