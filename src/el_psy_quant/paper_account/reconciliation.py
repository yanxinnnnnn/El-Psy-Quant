"""Immutable Paper Account projection-reconciliation evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.commands import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
)
from el_psy_quant.paper_account.evidence_operations import (
    ReconcilePaperAccountProjectionCommand,
    _validate_operation_command,
)
from el_psy_quant.paper_account.events import MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
)
from el_psy_quant.paper_account.ledger_replay import (
    PaperAccountLedgerHistoryBundle,
)
from el_psy_quant.paper_account.projection import (
    SUPPORTED_PAPER_ACCOUNT_PROJECTION_MISMATCH_CODES,
    PaperAccountProjection,
    PaperAccountProjectionMismatchCode,
    verify_paper_account_projection,
)

PAPER_ACCOUNT_RECONCILIATION_SCHEMA_VERSION = 1
MAX_PAPER_ACCOUNT_RECONCILIATION_ID_LENGTH = 512

PaperAccountReconciliationOutcome = Literal["matched", "mismatched"]
SUPPORTED_PAPER_ACCOUNT_RECONCILIATION_OUTCOMES = (
    "matched",
    "mismatched",
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(
        "reconciliations are created by the trusted reconciliation operation"
    )


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
class PaperAccountReconciliation:
    """Derived immutable comparison evidence with no repair authority."""

    reconciliation_id: str
    account_id: str
    operation_idempotency_key: str
    operation_command_digest: str
    created_by: str
    recorded_timestamp_utc: datetime
    reason: str
    outcome: PaperAccountReconciliationOutcome
    mismatch_codes: tuple[PaperAccountProjectionMismatchCode, ...]
    authoritative_account_version: int
    authoritative_event_id: str
    authoritative_chain_digest: str
    authoritative_projection_digest: str
    candidate_account_version: int
    candidate_event_id: str
    candidate_chain_digest: str
    candidate_projection_digest: str
    reconciliation_digest: str

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the deeply validated reconciliation artifact export."""
        _validate_reconciliation(self)
        payload = _reconciliation_payload_without_digest(self)
        payload["reconciliation_digest"] = self.reconciliation_digest
        return payload


def _reconciliation_payload_without_digest(
    artifact: PaperAccountReconciliation,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_ACCOUNT_RECONCILIATION_SCHEMA_VERSION,
        "reconciliation_id": artifact.reconciliation_id,
        "account_id": artifact.account_id,
        "operation_idempotency_key": artifact.operation_idempotency_key,
        "operation_command_digest": artifact.operation_command_digest,
        "created_by": artifact.created_by,
        "recorded_timestamp_utc": artifact.recorded_timestamp_utc.isoformat(),
        "reason": artifact.reason,
        "outcome": artifact.outcome,
        "mismatch_codes": list(artifact.mismatch_codes),
        "authoritative_account_version": artifact.authoritative_account_version,
        "authoritative_event_id": artifact.authoritative_event_id,
        "authoritative_chain_digest": artifact.authoritative_chain_digest,
        "authoritative_projection_digest": (
            artifact.authoritative_projection_digest
        ),
        "candidate_account_version": artifact.candidate_account_version,
        "candidate_event_id": artifact.candidate_event_id,
        "candidate_chain_digest": artifact.candidate_chain_digest,
        "candidate_projection_digest": artifact.candidate_projection_digest,
    }


def _validate_reconciliation(
    artifact: object,
) -> PaperAccountReconciliation:
    if type(artifact) is not PaperAccountReconciliation:
        raise ValueError("artifact must be PaperAccountReconciliation")
    _exact_normalized(
        artifact.reconciliation_id,
        field_name="reconciliation_id",
        maximum_length=MAX_PAPER_ACCOUNT_RECONCILIATION_ID_LENGTH,
    )
    _exact_normalized(
        artifact.account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    _exact_normalized(
        artifact.operation_idempotency_key,
        field_name="operation_idempotency_key",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )
    _exact_normalized(
        artifact.created_by,
        field_name="created_by",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    _exact_normalized(
        artifact.reason,
        field_name="reason",
        maximum_length=MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
    )
    if (
        type(artifact.outcome) is not str
        or artifact.outcome not in SUPPORTED_PAPER_ACCOUNT_RECONCILIATION_OUTCOMES
    ):
        raise ValueError("reconciliation outcome is invalid")
    if type(artifact.mismatch_codes) is not tuple:
        raise ValueError("mismatch codes must use immutable tuple ordering")
    indexes: list[int] = []
    for code in artifact.mismatch_codes:
        if type(code) is not str:
            raise ValueError("mismatch codes must be exact strings")
        try:
            indexes.append(
                SUPPORTED_PAPER_ACCOUNT_PROJECTION_MISMATCH_CODES.index(code)
            )
        except ValueError as exc:
            raise ValueError("reconciliation mismatch code is invalid") from exc
    if indexes != sorted(set(indexes)):
        raise ValueError("mismatch codes must be ordered and deduplicated")
    if (artifact.outcome == "matched") is bool(artifact.mismatch_codes):
        raise ValueError("reconciliation outcome and mismatch codes disagree")
    for field_name in (
        "authoritative_account_version",
        "candidate_account_version",
    ):
        value = getattr(artifact, field_name)
        if type(value) is not int or value <= 0:
            raise ValueError(f"{field_name} must be an exact positive integer")
    for field_name in ("authoritative_event_id", "candidate_event_id"):
        _exact_normalized(
            getattr(artifact, field_name),
            field_name=field_name,
            maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
        )
    for field_name in (
        "authoritative_chain_digest",
        "authoritative_projection_digest",
        "candidate_chain_digest",
        "candidate_projection_digest",
        "operation_command_digest",
        "reconciliation_digest",
    ):
        _exact_digest(getattr(artifact, field_name), field_name)
    _exact_utc(artifact.recorded_timestamp_utc)
    try:
        command = ReconcilePaperAccountProjectionCommand(
            account_id=artifact.account_id,
            expected_account_version=artifact.authoritative_account_version,
            expected_head_event_id=artifact.authoritative_event_id,
            expected_head_chain_digest=artifact.authoritative_chain_digest,
            operation_idempotency_key=artifact.operation_idempotency_key,
            actor=artifact.created_by,
            reason=artifact.reason,
        )
    except ValueError as exc:
        raise ValueError("reconciliation operation metadata is invalid") from exc
    if command.command_digest != artifact.operation_command_digest:
        raise ValueError("reconciliation command digest does not match metadata")
    if canonical_digest(_reconciliation_payload_without_digest(artifact)) != (
        artifact.reconciliation_digest
    ):
        raise ValueError(
            "reconciliation digest does not match its canonical payload"
        )
    return artifact


def reconcile_paper_account_projection(
    history: Iterable[PaperAccountLedgerHistoryBundle],
    candidate_projection: PaperAccountProjection,
    command: ReconcilePaperAccountProjectionCommand,
    *,
    reconciliation_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountReconciliation:
    """Record matched/mismatched evidence without changing the candidate."""
    _validate_operation_command(command, ReconcilePaperAccountProjectionCommand)
    normalized_id = normalize_bounded_string(
        reconciliation_id,
        field_name="reconciliation_id",
        maximum_length=MAX_PAPER_ACCOUNT_RECONCILIATION_ID_LENGTH,
    )
    recorded = normalize_utc_datetime(
        recorded_timestamp_utc,
        field_name="recorded_timestamp_utc",
    )
    verification = verify_paper_account_projection(history, candidate_projection)
    if (
        command.account_id != candidate_projection.account_id
        or command.expected_account_version
        != verification.authoritative_account_version
        or command.expected_head_event_id != verification.authoritative_event_id
        or command.expected_head_chain_digest
        != verification.authoritative_chain_digest
    ):
        raise ValueError(
            "reconciliation command anchors do not match replayed head"
        )

    result = object.__new__(PaperAccountReconciliation)
    object.__setattr__(result, "reconciliation_id", normalized_id)
    object.__setattr__(result, "account_id", command.account_id)
    object.__setattr__(
        result, "operation_idempotency_key", command.operation_idempotency_key
    )
    object.__setattr__(result, "operation_command_digest", command.command_digest)
    object.__setattr__(result, "created_by", command.actor)
    object.__setattr__(result, "recorded_timestamp_utc", recorded)
    object.__setattr__(result, "reason", command.reason)
    object.__setattr__(
        result,
        "outcome",
        "matched" if verification.status == "current" else "mismatched",
    )
    object.__setattr__(result, "mismatch_codes", verification.mismatch_codes)
    for field_name in (
        "authoritative_account_version",
        "authoritative_event_id",
        "authoritative_chain_digest",
        "authoritative_projection_digest",
        "candidate_account_version",
        "candidate_event_id",
        "candidate_chain_digest",
        "candidate_projection_digest",
    ):
        object.__setattr__(result, field_name, getattr(verification, field_name))
    object.__setattr__(
        result,
        "reconciliation_digest",
        canonical_digest(_reconciliation_payload_without_digest(result)),
    )
    _validate_reconciliation(result)
    return result
