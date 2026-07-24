"""Immutable Paper Account snapshot evidence derived from ledger replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.evidence_operations import (
    CreatePaperAccountSnapshotCommand,
    _validate_operation_command,
)
from el_psy_quant.paper_account.commands import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
)
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
)
from el_psy_quant.paper_account.ledger_replay import (
    PaperAccountLedgerHistoryBundle,
)
from el_psy_quant.paper_account.projection import (
    PaperAccountProjection,
    _validate_projection,
    rebuild_paper_account_projection,
)

PAPER_ACCOUNT_SNAPSHOT_SCHEMA_VERSION = 1
MAX_PAPER_ACCOUNT_SNAPSHOT_ID_LENGTH = 512


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("snapshots are created by the trusted snapshot operation")


def _exact_normalized(
    value: object, *, field_name: str, maximum_length: int
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = normalize_bounded_string(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )
    if normalized != value:
        raise ValueError(f"{field_name} must already be normalized")
    return value


def _exact_digest(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return validate_digest(value, field_name)


def _exact_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("recorded_timestamp_utc must be a datetime")
    normalized = normalize_utc_datetime(
        value,
        field_name="recorded_timestamp_utc",
    )
    if value.tzinfo is not timezone.utc or value.isoformat() != normalized.isoformat():
        raise ValueError("recorded_timestamp_utc must be normalized to UTC")
    return value


@dataclass(frozen=True, init=False)
class PaperAccountSnapshot:
    """Derived immutable evidence for one exact authoritative account head."""

    snapshot_id: str
    account_id: str
    account_version: int
    head_event_id: str
    head_chain_digest: str
    operation_idempotency_key: str
    operation_command_digest: str
    created_by: str
    recorded_timestamp_utc: datetime
    reason: str
    projection: PaperAccountProjection
    snapshot_digest: str

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the deeply validated canonical snapshot export."""
        _validate_snapshot(self)
        payload = _snapshot_payload_without_digest(self)
        payload["snapshot_digest"] = self.snapshot_digest
        return payload


def _snapshot_payload_without_digest(
    snapshot: PaperAccountSnapshot,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_ACCOUNT_SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "account_id": snapshot.account_id,
        "account_version": snapshot.account_version,
        "head_event_id": snapshot.head_event_id,
        "head_chain_digest": snapshot.head_chain_digest,
        "operation_idempotency_key": snapshot.operation_idempotency_key,
        "operation_command_digest": snapshot.operation_command_digest,
        "created_by": snapshot.created_by,
        "recorded_timestamp_utc": snapshot.recorded_timestamp_utc.isoformat(),
        "reason": snapshot.reason,
        "projection": snapshot.projection.to_dict(),
    }


def _validate_snapshot(snapshot: object) -> PaperAccountSnapshot:
    if type(snapshot) is not PaperAccountSnapshot:
        raise ValueError("snapshot must be PaperAccountSnapshot")
    _exact_normalized(
        snapshot.snapshot_id,
        field_name="snapshot_id",
        maximum_length=MAX_PAPER_ACCOUNT_SNAPSHOT_ID_LENGTH,
    )
    _exact_normalized(
        snapshot.account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    _exact_normalized(
        snapshot.operation_idempotency_key,
        field_name="operation_idempotency_key",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )
    _exact_normalized(
        snapshot.created_by,
        field_name="created_by",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    _exact_normalized(
        snapshot.reason,
        field_name="reason",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
    )
    if type(snapshot.account_version) is not int or snapshot.account_version <= 0:
        raise ValueError("account_version must be an exact positive integer")
    _exact_digest(snapshot.head_chain_digest, "head_chain_digest")
    _exact_digest(snapshot.operation_command_digest, "operation_command_digest")
    _exact_digest(snapshot.snapshot_digest, "snapshot_digest")
    _exact_utc(snapshot.recorded_timestamp_utc)
    projection = _validate_projection(snapshot.projection)
    if (
        snapshot.account_id != projection.account_id
        or snapshot.account_version != projection.source_account_version
        or snapshot.head_event_id != projection.source_event_id
        or snapshot.head_chain_digest != projection.source_chain_digest
    ):
        raise ValueError("snapshot anchors do not match embedded projection")
    try:
        command = CreatePaperAccountSnapshotCommand(
            account_id=snapshot.account_id,
            expected_account_version=snapshot.account_version,
            expected_head_event_id=snapshot.head_event_id,
            expected_head_chain_digest=snapshot.head_chain_digest,
            operation_idempotency_key=snapshot.operation_idempotency_key,
            actor=snapshot.created_by,
            reason=snapshot.reason,
        )
    except ValueError as exc:
        raise ValueError("snapshot operation metadata is invalid") from exc
    if command.command_digest != snapshot.operation_command_digest:
        raise ValueError("snapshot command digest does not match metadata")
    if canonical_digest(_snapshot_payload_without_digest(snapshot)) != (
        snapshot.snapshot_digest
    ):
        raise ValueError("snapshot digest does not match its canonical payload")
    return snapshot


def create_paper_account_snapshot(
    history: Iterable[PaperAccountLedgerHistoryBundle],
    command: CreatePaperAccountSnapshotCommand,
    *,
    snapshot_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountSnapshot:
    """Create immutable evidence without creating a ledger mutation."""
    _validate_operation_command(command, CreatePaperAccountSnapshotCommand)
    normalized_snapshot_id = normalize_bounded_string(
        snapshot_id,
        field_name="snapshot_id",
        maximum_length=MAX_PAPER_ACCOUNT_SNAPSHOT_ID_LENGTH,
    )
    recorded = normalize_utc_datetime(
        recorded_timestamp_utc,
        field_name="recorded_timestamp_utc",
    )
    projection = rebuild_paper_account_projection(history)
    if (
        command.account_id != projection.account_id
        or command.expected_account_version
        != projection.source_account_version
        or command.expected_head_event_id != projection.source_event_id
        or command.expected_head_chain_digest
        != projection.source_chain_digest
    ):
        raise ValueError("snapshot command anchors do not match replayed head")

    result = object.__new__(PaperAccountSnapshot)
    object.__setattr__(result, "snapshot_id", normalized_snapshot_id)
    object.__setattr__(result, "account_id", command.account_id)
    object.__setattr__(
        result, "account_version", command.expected_account_version
    )
    object.__setattr__(result, "head_event_id", command.expected_head_event_id)
    object.__setattr__(
        result, "head_chain_digest", command.expected_head_chain_digest
    )
    object.__setattr__(
        result, "operation_idempotency_key", command.operation_idempotency_key
    )
    object.__setattr__(result, "operation_command_digest", command.command_digest)
    object.__setattr__(result, "created_by", command.actor)
    object.__setattr__(result, "recorded_timestamp_utc", recorded)
    object.__setattr__(result, "reason", command.reason)
    object.__setattr__(result, "projection", projection)
    object.__setattr__(
        result,
        "snapshot_digest",
        canonical_digest(_snapshot_payload_without_digest(result)),
    )
    _validate_snapshot(result)
    return result
