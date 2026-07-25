"""Strict records, errors, and canonical helpers for Paper Account storage."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PaperAccountEvent,
    PaperAccountIdentity,
    PaperAccountLedgerEventBundle,
    PaperAccountLifecycleStatus,
    PaperAccountProjection,
    PaperAccountReconciliation,
    PaperAccountSnapshot,
    PaperCashLedgerEntry,
    PaperPositionLedgerEntry,
)
from el_psy_quant.paper_account._shared import (
    normalize_bounded_string,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.ledger_replay import (
    PaperAccountLedgerHistoryBundle,
)

PAPER_ACCOUNT_RECORD_SCHEMA_VERSION = 1
PAPER_ACCOUNT_PERSISTENCE_RECORD_SCHEMA_VERSION = 1

PaperAccountProjectionStatus = Literal[
    "current", "reconciliation_required"
]
SUPPORTED_PAPER_ACCOUNT_PROJECTION_STATUSES = (
    "current",
    "reconciliation_required",
)


class PaperAccountNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account not found")


class PaperAccountIdempotencyConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account idempotency key conflicts")


class PaperAccountVersionConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account version conflicts with current head")


class PaperAccountConcurrencyConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account concurrent mutation lost")


class PaperAccountProjectionReconciliationRequiredError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account projection requires reconciliation")


class PaperAccountPersistenceCorruptionError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account persistence is corrupt")


class PaperAccountOperationConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account operation conflicts with existing evidence")


class PaperAccountApprovedEvidenceError(Exception):
    def __init__(self) -> None:
        super().__init__("approved portfolio-review evidence is unavailable or invalid")


class PaperAccountStorageBusyError(Exception):
    def __init__(self) -> None:
        super().__init__("paper account storage is busy")


class PaperAccountFrozenError(ValueError):
    def __init__(self) -> None:
        super().__init__("paper account is frozen")


class PaperAccountClosedError(ValueError):
    def __init__(self) -> None:
        super().__init__("paper account is closed")


@dataclass(frozen=True)
class PaperAccountRecord:
    """Compact durable account identity and current immutable-ledger head."""

    record_schema_version: Literal[1]
    account_identity: PaperAccountIdentity
    lifecycle_status: PaperAccountLifecycleStatus
    head_version: int
    head_event_id: str
    head_chain_digest: str
    projection_status: PaperAccountProjectionStatus
    updated_timestamp: datetime
    closed_timestamp: datetime | None

    def __post_init__(self) -> None:
        if self.record_schema_version != PAPER_ACCOUNT_RECORD_SCHEMA_VERSION:
            raise ValueError("unsupported Paper Account record schema version")
        if type(self.account_identity) is not PaperAccountIdentity:
            raise ValueError("account_identity must be PaperAccountIdentity")
        rebuilt = PaperAccountIdentity(
            account_id=self.account_identity.account_id,
            display_name=self.account_identity.display_name,
            base_currency=self.account_identity.base_currency,
            created_by=self.account_identity.created_by,
            created_timestamp=self.account_identity.created_timestamp,
        )
        if rebuilt.to_dict() != self.account_identity.to_dict():
            raise ValueError("account identity is not canonical")
        if self.lifecycle_status not in ("active", "frozen", "closed"):
            raise ValueError("unsupported account lifecycle status")
        if type(self.head_version) is not int or self.head_version <= 0:
            raise ValueError("head_version must be an exact positive integer")
        normalize_bounded_string(
            self.head_event_id,
            field_name="head_event_id",
            maximum_length=512,
        )
        validate_digest(self.head_chain_digest, "head_chain_digest")
        if self.projection_status not in (
            SUPPORTED_PAPER_ACCOUNT_PROJECTION_STATUSES
        ):
            raise ValueError("unsupported projection status")
        updated = _exact_utc(self.updated_timestamp, "updated_timestamp")
        if updated < self.account_identity.created_timestamp:
            raise ValueError("updated timestamp precedes account creation")
        if self.lifecycle_status == "closed":
            if self.closed_timestamp is None:
                raise ValueError("closed account requires closed_timestamp")
            closed = _exact_utc(self.closed_timestamp, "closed_timestamp")
            if (
                closed < self.account_identity.created_timestamp
                or closed > updated
            ):
                raise ValueError("closed_timestamp is outside account history")
        elif self.closed_timestamp is not None:
            raise ValueError("non-closed account cannot have closed_timestamp")

    @property
    def account_id(self) -> str:
        return self.account_identity.account_id


@dataclass(frozen=True)
class PaperAccountCreationKeyRecord:
    record_schema_version: Literal[1]
    creation_idempotency_key: str
    creation_request_digest: str
    account_id: str
    creation_event_id: str
    created_timestamp: datetime

    def __post_init__(self) -> None:
        if self.record_schema_version != 1:
            raise ValueError("unsupported creation-key schema version")
        _exact_string(
            self.creation_idempotency_key,
            "creation_idempotency_key",
            MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
        )
        validate_digest(
            self.creation_request_digest,
            "creation_request_digest",
        )
        _exact_string(self.account_id, "account_id", 512)
        _exact_string(self.creation_event_id, "creation_event_id", 512)
        _exact_utc(self.created_timestamp, "created_timestamp")


@dataclass(frozen=True)
class PaperAccountCommandResult:
    """One accepted account event and its exact reconstructed current state."""

    account: PaperAccountRecord
    event: PaperAccountEvent
    projection: PaperAccountProjection
    history: tuple[PaperAccountLedgerHistoryBundle, ...]
    replayed: bool


@dataclass(frozen=True)
class PaperAccountSnapshotResult:
    snapshot: PaperAccountSnapshot
    replayed: bool


@dataclass(frozen=True)
class PaperAccountReconciliationResult:
    reconciliation: PaperAccountReconciliation
    replayed: bool


@dataclass(frozen=True)
class PaperAccountListPage:
    """One bounded keyset-ordered page of compact account records."""

    items: tuple[PaperAccountRecord, ...]
    has_more: bool


@dataclass(frozen=True)
class PaperAccountLedgerPageItem:
    """One independently validated immutable event and its ordered postings."""

    event: PaperAccountEvent
    cash_postings: tuple[PaperCashLedgerEntry, ...]
    position_postings: tuple[PaperPositionLedgerEntry, ...]


@dataclass(frozen=True)
class PaperAccountLedgerPage:
    """One bounded contiguous page from immutable account history."""

    items: tuple[PaperAccountLedgerPageItem, ...]
    has_more: bool


def _exact_string(value: object, field_name: str, maximum_length: int) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact string")
    normalized = normalize_bounded_string(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )
    if normalized != value:
        raise ValueError(f"{field_name} must already be normalized")
    return value


def _exact_utc(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    elif value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field_name} must already use UTC")
    normalized = normalize_utc_datetime(value, field_name=field_name)
    if normalized.tzinfo is not timezone.utc:
        raise ValueError(f"{field_name} must normalize exactly to UTC")
    return normalized


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON constants are forbidden")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object keys are forbidden")
        result[key] = value
    return result


def canonical_json(value: object) -> str:
    """Serialize one canonical JSON value without float aliases."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def load_canonical_json(payload: object) -> object:
    """Load only exact canonical JSON with unique keys."""
    if type(payload) is not str:
        raise ValueError("persisted JSON payload must be a string")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("persisted JSON payload is invalid") from exc
    if canonical_json(value) != payload:
        raise ValueError("persisted JSON payload is not canonical")
    return value


def exact_dict(
    value: object,
    *,
    fields: tuple[str, ...],
) -> dict[str, object]:
    if type(value) is not dict or tuple(sorted(value)) != tuple(sorted(fields)):
        raise ValueError("persisted JSON object fields are invalid")
    return value


def exact_list(value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError("persisted JSON value must be a list")
    return value


def history_event(
    bundle: PaperAccountLedgerHistoryBundle,
) -> PaperAccountEvent:
    if type(bundle) is PaperAccountLedgerEventBundle:
        return bundle.event
    return bundle.event


__all__ = [
    "PAPER_ACCOUNT_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "PAPER_ACCOUNT_RECORD_SCHEMA_VERSION",
    "PaperAccountApprovedEvidenceError",
    "PaperAccountCommandResult",
    "PaperAccountConcurrencyConflictError",
    "PaperAccountCreationKeyRecord",
    "PaperAccountClosedError",
    "PaperAccountFrozenError",
    "PaperAccountIdempotencyConflictError",
    "PaperAccountLedgerPage",
    "PaperAccountLedgerPageItem",
    "PaperAccountListPage",
    "PaperAccountNotFoundError",
    "PaperAccountOperationConflictError",
    "PaperAccountPersistenceCorruptionError",
    "PaperAccountProjectionReconciliationRequiredError",
    "PaperAccountProjectionStatus",
    "PaperAccountReconciliationResult",
    "PaperAccountRecord",
    "PaperAccountSnapshotResult",
    "PaperAccountStorageBusyError",
    "PaperAccountVersionConflictError",
    "SUPPORTED_PAPER_ACCOUNT_PROJECTION_STATUSES",
]
