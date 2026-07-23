"""Pure immutable cash-movement command contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
)
from el_psy_quant.paper_account.commands import (
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
    PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
)
from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
)

PostPaperCashMovementType = Literal[
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
]

SUPPORTED_POST_PAPER_CASH_MOVEMENT_TYPES = (
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
)


def _normalize_movement_type(value: object) -> PostPaperCashMovementType:
    if value not in SUPPORTED_POST_PAPER_CASH_MOVEMENT_TYPES:
        supported = ", ".join(SUPPORTED_POST_PAPER_CASH_MOVEMENT_TYPES)
        raise ValueError(f"movement_type must be one of: {supported}")
    return value  # type: ignore[return-value]


@dataclass(frozen=True)
class PostPaperCashMovementCommand:
    """Request one explicit post-creation cash movement."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    movement_type: PostPaperCashMovementType
    requested_amount: PaperMoney
    effective_timestamp_utc: datetime | None = None
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "account_id",
            normalize_bounded_string(
                self.account_id,
                field_name="account_id",
                maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
            ),
        )
        if (
            type(self.expected_account_version) is not int
            or self.expected_account_version <= 0
        ):
            raise ValueError(
                "expected_account_version must be a positive integer"
            )
        object.__setattr__(
            self,
            "command_idempotency_key",
            normalize_bounded_string(
                self.command_idempotency_key,
                field_name="command_idempotency_key",
                maximum_length=(
                    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH
                ),
            ),
        )
        object.__setattr__(
            self,
            "actor",
            normalize_bounded_string(
                self.actor,
                field_name="actor",
                maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "reason",
            normalize_bounded_string(
                self.reason,
                field_name="reason",
                maximum_length=MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "movement_type",
            _normalize_movement_type(self.movement_type),
        )
        if type(self.requested_amount) is not PaperMoney:
            raise ValueError("requested_amount must be PaperMoney")
        amount = self.requested_amount.decimal_value
        if self.movement_type == "manual_adjustment":
            if amount == 0:
                raise ValueError(
                    "manual_adjustment requested_amount must be non-zero"
                )
        elif amount <= 0:
            raise ValueError(
                f"{self.movement_type} requested_amount must be positive"
            )
        if self.effective_timestamp_utc is not None:
            object.__setattr__(
                self,
                "effective_timestamp_utc",
                normalize_utc_datetime(
                    self.effective_timestamp_utc,
                    field_name="effective_timestamp_utc",
                ),
            )
        object.__setattr__(
            self,
            "command_digest",
            canonical_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
            "command_type": "post_paper_cash_movement",
            "account_id": self.account_id,
            "expected_account_version": self.expected_account_version,
            "command_idempotency_key": self.command_idempotency_key,
            "actor": self.actor,
            "reason": self.reason,
            "movement_type": self.movement_type,
            "requested_amount": self.requested_amount.to_json_value(),
            "effective_timestamp_utc": (
                self.effective_timestamp_utc.isoformat()
                if self.effective_timestamp_utc is not None
                else None
            ),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        payload = self._payload_without_digest()
        payload["command_digest"] = self.command_digest
        return payload


def create_post_paper_cash_movement_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
    movement_type: PostPaperCashMovementType,
    requested_amount: PaperMoney,
    effective_timestamp_utc: datetime | None = None,
) -> PostPaperCashMovementCommand:
    """Create one validated cash movement command without applying it."""
    return PostPaperCashMovementCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
        movement_type=movement_type,
        requested_amount=requested_amount,
        effective_timestamp_utc=effective_timestamp_utc,
    )
