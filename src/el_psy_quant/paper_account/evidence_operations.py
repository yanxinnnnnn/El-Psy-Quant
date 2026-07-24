"""Pure non-mutating Paper Account evidence-operation commands."""

from __future__ import annotations

from dataclasses import dataclass, field

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    validate_digest,
)
from el_psy_quant.paper_account.commands import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
)
from el_psy_quant.paper_account.events import MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
)

PAPER_ACCOUNT_EVIDENCE_OPERATION_COMMAND_SCHEMA_VERSION = 1


def _exact_normalized_string(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalize_bounded_string(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )


def _expected_version(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(
            "expected_account_version must be an exact positive integer"
        )
    return value


def _exact_digest(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return validate_digest(value, field_name)


def _command_payload(
    *,
    command_type: str,
    account_id: str,
    expected_account_version: int,
    expected_head_event_id: str,
    expected_head_chain_digest: str,
    operation_idempotency_key: str,
    actor: str,
    reason: str,
) -> dict[str, object]:
    return {
        "schema_version": (
            PAPER_ACCOUNT_EVIDENCE_OPERATION_COMMAND_SCHEMA_VERSION
        ),
        "command_type": command_type,
        "account_id": account_id,
        "expected_account_version": expected_account_version,
        "expected_head_event_id": expected_head_event_id,
        "expected_head_chain_digest": expected_head_chain_digest,
        "operation_idempotency_key": operation_idempotency_key,
        "actor": actor,
        "reason": reason,
    }


def _normalize_command(command: object, *, command_type: str) -> None:
    object.__setattr__(
        command,
        "account_id",
        _exact_normalized_string(
            getattr(command, "account_id"),
            field_name="account_id",
            maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
        ),
    )
    object.__setattr__(
        command,
        "expected_account_version",
        _expected_version(getattr(command, "expected_account_version")),
    )
    object.__setattr__(
        command,
        "expected_head_event_id",
        _exact_normalized_string(
            getattr(command, "expected_head_event_id"),
            field_name="expected_head_event_id",
            maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
        ),
    )
    object.__setattr__(
        command,
        "expected_head_chain_digest",
        _exact_digest(
            getattr(command, "expected_head_chain_digest"),
            "expected_head_chain_digest",
        ),
    )
    object.__setattr__(
        command,
        "operation_idempotency_key",
        _exact_normalized_string(
            getattr(command, "operation_idempotency_key"),
            field_name="operation_idempotency_key",
            maximum_length=(
                MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH
            ),
        ),
    )
    object.__setattr__(
        command,
        "actor",
        _exact_normalized_string(
            getattr(command, "actor"),
            field_name="actor",
            maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
        ),
    )
    object.__setattr__(
        command,
        "reason",
        _exact_normalized_string(
            getattr(command, "reason"),
            field_name="reason",
            maximum_length=MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
        ),
    )
    payload = _command_payload(
        command_type=command_type,
        account_id=getattr(command, "account_id"),
        expected_account_version=getattr(
            command, "expected_account_version"
        ),
        expected_head_event_id=getattr(command, "expected_head_event_id"),
        expected_head_chain_digest=getattr(
            command, "expected_head_chain_digest"
        ),
        operation_idempotency_key=getattr(
            command, "operation_idempotency_key"
        ),
        actor=getattr(command, "actor"),
        reason=getattr(command, "reason"),
    )
    object.__setattr__(command, "command_digest", canonical_digest(payload))


@dataclass(frozen=True)
class CreatePaperAccountSnapshotCommand:
    """Request derived snapshot evidence at one exact account head."""

    account_id: str
    expected_account_version: int
    expected_head_event_id: str
    expected_head_chain_digest: str
    operation_idempotency_key: str
    actor: str
    reason: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _normalize_command(self, command_type="create_paper_account_snapshot")

    def _payload_without_digest(self) -> dict[str, object]:
        return _command_payload(
            command_type="create_paper_account_snapshot",
            account_id=self.account_id,
            expected_account_version=self.expected_account_version,
            expected_head_event_id=self.expected_head_event_id,
            expected_head_chain_digest=self.expected_head_chain_digest,
            operation_idempotency_key=self.operation_idempotency_key,
            actor=self.actor,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and digest."""
        payload = self._payload_without_digest()
        payload["command_digest"] = self.command_digest
        return payload


@dataclass(frozen=True)
class ReconcilePaperAccountProjectionCommand:
    """Request comparison evidence without repairing the candidate."""

    account_id: str
    expected_account_version: int
    expected_head_event_id: str
    expected_head_chain_digest: str
    operation_idempotency_key: str
    actor: str
    reason: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _normalize_command(
            self,
            command_type="reconcile_paper_account_projection",
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return _command_payload(
            command_type="reconcile_paper_account_projection",
            account_id=self.account_id,
            expected_account_version=self.expected_account_version,
            expected_head_event_id=self.expected_head_event_id,
            expected_head_chain_digest=self.expected_head_chain_digest,
            operation_idempotency_key=self.operation_idempotency_key,
            actor=self.actor,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and digest."""
        payload = self._payload_without_digest()
        payload["command_digest"] = self.command_digest
        return payload


def create_paper_account_snapshot_command(
    *,
    account_id: str,
    expected_account_version: int,
    expected_head_event_id: str,
    expected_head_chain_digest: str,
    operation_idempotency_key: str,
    actor: str,
    reason: str,
) -> CreatePaperAccountSnapshotCommand:
    """Create a normalized non-mutating snapshot operation command."""
    return CreatePaperAccountSnapshotCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        expected_head_event_id=expected_head_event_id,
        expected_head_chain_digest=expected_head_chain_digest,
        operation_idempotency_key=operation_idempotency_key,
        actor=actor,
        reason=reason,
    )


def create_reconcile_paper_account_projection_command(
    *,
    account_id: str,
    expected_account_version: int,
    expected_head_event_id: str,
    expected_head_chain_digest: str,
    operation_idempotency_key: str,
    actor: str,
    reason: str,
) -> ReconcilePaperAccountProjectionCommand:
    """Create a normalized non-mutating reconciliation command."""
    return ReconcilePaperAccountProjectionCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        expected_head_event_id=expected_head_event_id,
        expected_head_chain_digest=expected_head_chain_digest,
        operation_idempotency_key=operation_idempotency_key,
        actor=actor,
        reason=reason,
    )


def _validate_operation_command(
    command: object,
    expected_type: type[
        CreatePaperAccountSnapshotCommand
        | ReconcilePaperAccountProjectionCommand
    ],
) -> None:
    if type(command) is not expected_type:
        raise ValueError(f"command must be {expected_type.__name__}")
    try:
        rebuilt = expected_type(
            account_id=command.account_id,
            expected_account_version=command.expected_account_version,
            expected_head_event_id=command.expected_head_event_id,
            expected_head_chain_digest=command.expected_head_chain_digest,
            operation_idempotency_key=command.operation_idempotency_key,
            actor=command.actor,
            reason=command.reason,
        )
    except (AttributeError, ValueError) as exc:
        raise ValueError("operation command is invalid") from exc
    _exact_digest(command.command_digest, "command_digest")
    if rebuilt.to_dict() != command.to_dict():
        raise ValueError("command digest does not match its canonical payload")
