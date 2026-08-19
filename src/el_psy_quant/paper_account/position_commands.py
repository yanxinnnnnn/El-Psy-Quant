"""Pure immutable Paper Account position-adjustment commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from el_psy_quant.data import normalize_symbol
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
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
)

MAX_PAPER_POSITION_SYMBOL_LENGTH = 128

PaperPositionAdjustmentCategory = Literal[
    "opening_balance",
    "manual_correction",
    "corporate_action",
    "other",
    "execution_fill",
]

SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES = (
    "opening_balance",
    "manual_correction",
    "corporate_action",
    "other",
    "execution_fill",
)

SUPPORTED_POST_PAPER_POSITION_ADJUSTMENT_CATEGORIES = (
    "opening_balance",
    "manual_correction",
    "corporate_action",
    "other",
)


def _normalize_adjustment_category(
    value: object,
) -> PaperPositionAdjustmentCategory:
    if value not in SUPPORTED_POST_PAPER_POSITION_ADJUSTMENT_CATEGORIES:
        supported = ", ".join(
            SUPPORTED_POST_PAPER_POSITION_ADJUSTMENT_CATEGORIES
        )
        raise ValueError(f"adjustment_category must be one of: {supported}")
    return value  # type: ignore[return-value]


def _normalize_position_symbol(value: object) -> str:
    try:
        normalized = normalize_symbol(value)  # type: ignore[arg-type]
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("symbol must be a non-empty string") from exc
    if len(normalized) > MAX_PAPER_POSITION_SYMBOL_LENGTH:
        raise ValueError(
            "symbol must be at most "
            f"{MAX_PAPER_POSITION_SYMBOL_LENGTH} characters"
        )
    return normalized


@dataclass(frozen=True)
class PostPaperPositionAdjustmentCommand:
    """Request one explicit signed position and aggregate-cost adjustment."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    symbol: str
    adjustment_category: PaperPositionAdjustmentCategory
    signed_quantity_delta: PaperQuantity
    signed_cost_basis_delta: PaperMoney
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
        object.__setattr__(self, "symbol", _normalize_position_symbol(self.symbol))
        object.__setattr__(
            self,
            "adjustment_category",
            _normalize_adjustment_category(self.adjustment_category),
        )
        if type(self.signed_quantity_delta) is not PaperQuantity:
            raise ValueError("signed_quantity_delta must be PaperQuantity")
        if type(self.signed_cost_basis_delta) is not PaperMoney:
            raise ValueError("signed_cost_basis_delta must be PaperMoney")
        if (
            self.signed_quantity_delta.decimal_value == 0
            and self.signed_cost_basis_delta.decimal_value == 0
        ):
            raise ValueError(
                "at least one position adjustment delta must be non-zero"
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
            "command_type": "post_paper_position_adjustment",
            "account_id": self.account_id,
            "expected_account_version": self.expected_account_version,
            "command_idempotency_key": self.command_idempotency_key,
            "actor": self.actor,
            "reason": self.reason,
            "symbol": self.symbol,
            "adjustment_category": self.adjustment_category,
            "signed_quantity_delta": (
                self.signed_quantity_delta.to_json_value()
            ),
            "signed_cost_basis_delta": (
                self.signed_cost_basis_delta.to_json_value()
            ),
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


def create_post_paper_position_adjustment_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
    symbol: str,
    adjustment_category: PaperPositionAdjustmentCategory,
    signed_quantity_delta: PaperQuantity,
    signed_cost_basis_delta: PaperMoney,
    effective_timestamp_utc: datetime | None = None,
) -> PostPaperPositionAdjustmentCommand:
    """Create one validated position adjustment without applying it."""
    return PostPaperPositionAdjustmentCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
        symbol=symbol,
        adjustment_category=adjustment_category,
        signed_quantity_delta=signed_quantity_delta,
        signed_cost_basis_delta=signed_cost_basis_delta,
        effective_timestamp_utc=effective_timestamp_utc,
    )
