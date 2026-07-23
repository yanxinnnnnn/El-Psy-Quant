"""Immutable Paper Account creation identity and compact references."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

PAPER_ACCOUNT_IDENTITY_SCHEMA_VERSION = 1
PAPER_ACCOUNT_REFERENCE_SCHEMA_VERSION = 1

MAX_PAPER_ACCOUNT_ID_LENGTH = 512
MAX_PAPER_ACCOUNT_DISPLAY_NAME_LENGTH = 200
MAX_PAPER_ACCOUNT_ACTOR_LENGTH = 512


def _normalize_bounded_string(
    value: str,
    field_name: str,
    maximum_length: int,
) -> str:
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


def _normalize_base_currency(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("base_currency must contain three ASCII letters")
    normalized = value.strip().upper()
    if len(normalized) != 3 or any(
        character < "A" or character > "Z" for character in normalized
    ):
        raise ValueError("base_currency must contain three ASCII letters")
    return normalized


def _normalize_utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("created_timestamp must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            "created_timestamp must be a timezone-aware datetime"
        ) from exc
    if value.tzinfo is None or offset is None:
        raise ValueError("created_timestamp must be a timezone-aware datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            "created_timestamp must be a timezone-aware datetime"
        ) from exc


@dataclass(frozen=True)
class PaperAccountIdentity:
    """Stable account creation identity before any ledger event exists."""

    account_id: str
    display_name: str
    base_currency: str
    created_by: str
    created_timestamp: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "account_id",
            _normalize_bounded_string(
                self.account_id,
                "account_id",
                MAX_PAPER_ACCOUNT_ID_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "display_name",
            _normalize_bounded_string(
                self.display_name,
                "display_name",
                MAX_PAPER_ACCOUNT_DISPLAY_NAME_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "base_currency",
            _normalize_base_currency(self.base_currency),
        )
        object.__setattr__(
            self,
            "created_by",
            _normalize_bounded_string(
                self.created_by,
                "created_by",
                MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_utc_datetime(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible identity."""
        return {
            "schema_version": PAPER_ACCOUNT_IDENTITY_SCHEMA_VERSION,
            "account_id": self.account_id,
            "display_name": self.display_name,
            "base_currency": self.base_currency,
            "created_by": self.created_by,
            "created_timestamp": self.created_timestamp.isoformat(),
        }


@dataclass(frozen=True)
class PaperAccountReference:
    """Compact identity-only pointer with no mutable account state."""

    account_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "account_id",
            _normalize_bounded_string(
                self.account_id,
                "account_id",
                MAX_PAPER_ACCOUNT_ID_LENGTH,
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible reference."""
        return {
            "schema_version": PAPER_ACCOUNT_REFERENCE_SCHEMA_VERSION,
            "account_id": self.account_id,
        }


def create_paper_account_identity(
    *,
    account_id: str,
    display_name: str,
    base_currency: str,
    created_by: str,
    created_timestamp: datetime,
) -> PaperAccountIdentity:
    """Create one validated stable Paper Account identity."""
    return PaperAccountIdentity(
        account_id=account_id,
        display_name=display_name,
        base_currency=base_currency,
        created_by=created_by,
        created_timestamp=created_timestamp,
    )


def create_paper_account_reference(
    identity_or_account_id: PaperAccountIdentity | str,
) -> PaperAccountReference:
    """Create a compact reference from an identity or exact account ID."""
    if type(identity_or_account_id) is PaperAccountIdentity:
        account_id = identity_or_account_id.account_id
    elif isinstance(identity_or_account_id, str):
        account_id = identity_or_account_id
    else:
        raise ValueError(
            "identity_or_account_id must be a PaperAccountIdentity or string"
        )
    return PaperAccountReference(account_id=account_id)
