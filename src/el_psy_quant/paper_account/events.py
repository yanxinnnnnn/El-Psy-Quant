"""Immutable ordered Paper Account event headers and digest chains."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.cash_commands import (
    PostPaperCashMovementType,
)
from el_psy_quant.paper_account.cash_ledger import PaperCashLedgerEntry
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountIdentity,
)
from el_psy_quant.paper_account.lifecycle import PaperAccountLifecycleStatus
from el_psy_quant.paper_account.position_commands import (
    PaperPositionAdjustmentCategory,
)
from el_psy_quant.paper_account.position_ledger import (
    PaperPositionLedgerEntry,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)

PAPER_ACCOUNT_EVENT_SCHEMA_VERSION = 1
MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH = 512

# Semantic seed: "el-psy-quant:paper-account-chain-genesis:v1".
PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST = hashlib.sha256(
    b"el-psy-quant:paper-account-chain-genesis:v1"
).hexdigest()

PaperAccountEventType = Literal[
    "account_created",
    "cash_movement_posted",
    "position_adjustment_posted",
    "execution_fill_posted",
    "portfolio_review_evidence_linked",
    "account_frozen",
    "account_reactivated",
    "account_closed",
]

SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES = (
    "account_created",
    "cash_movement_posted",
    "position_adjustment_posted",
    "execution_fill_posted",
    "portfolio_review_evidence_linked",
    "account_frozen",
    "account_reactivated",
    "account_closed",
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("account events are created by trusted command factories")


@dataclass(frozen=True, init=False)
class _AccountCreatedDetails:
    account_identity: PaperAccountIdentity
    initial_cash: PaperMoney

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "account_created",
            "account_identity": self.account_identity.to_dict(),
            "initial_cash": self.initial_cash.to_json_value(),
            "initial_lifecycle_status": "active",
        }


@dataclass(frozen=True, init=False)
class _CashMovementPostedDetails:
    movement_type: PostPaperCashMovementType
    requested_amount: PaperMoney

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "cash_movement_posted",
            "movement_type": self.movement_type,
            "requested_amount": self.requested_amount.to_json_value(),
        }


@dataclass(frozen=True, init=False)
class _PositionAdjustmentPostedDetails:
    symbol: str
    adjustment_category: PaperPositionAdjustmentCategory
    signed_quantity_delta: PaperQuantity
    signed_cost_basis_delta: PaperMoney

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "position_adjustment_posted",
            "symbol": self.symbol,
            "adjustment_category": self.adjustment_category,
            "signed_quantity_delta": (
                self.signed_quantity_delta.to_json_value()
            ),
            "signed_cost_basis_delta": (
                self.signed_cost_basis_delta.to_json_value()
            ),
        }


@dataclass(frozen=True, init=False)
class _ExecutionFillPostedDetails:
    execution_order_id: str
    execution_order_digest: str
    execution_attempt_id: str
    execution_attempt_digest: str
    execution_fill_id: str
    execution_fill_digest: str
    instrument_id: str
    side: str
    fill_quantity: PaperQuantity
    gross_notional: PaperMoney
    total_charges: PaperMoney
    signed_cash_delta: PaperMoney
    signed_position_quantity_delta: PaperQuantity
    signed_position_cost_basis_delta: PaperMoney

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "execution_fill_posted",
            "execution_order_id": self.execution_order_id,
            "execution_order_digest": self.execution_order_digest,
            "execution_attempt_id": self.execution_attempt_id,
            "execution_attempt_digest": self.execution_attempt_digest,
            "execution_fill_id": self.execution_fill_id,
            "execution_fill_digest": self.execution_fill_digest,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "fill_quantity": self.fill_quantity.to_json_value(),
            "gross_notional": self.gross_notional.to_json_value(),
            "total_charges": self.total_charges.to_json_value(),
            "signed_cash_delta": self.signed_cash_delta.to_json_value(),
            "signed_position_quantity_delta": (
                self.signed_position_quantity_delta.to_json_value()
            ),
            "signed_position_cost_basis_delta": (
                self.signed_position_cost_basis_delta.to_json_value()
            ),
        }


@dataclass(frozen=True, init=False)
class _PortfolioReviewEvidenceLinkedDetails:
    approved_portfolio_review: ApprovedPortfolioReviewReference

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "portfolio_review_evidence_linked",
            "approved_portfolio_review": (
                self.approved_portfolio_review.to_dict()
            ),
        }


@dataclass(frozen=True, init=False)
class _LifecycleChangedDetails:
    source_status: PaperAccountLifecycleStatus
    target_status: PaperAccountLifecycleStatus

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "details_type": "lifecycle_changed",
            "source_status": self.source_status,
            "target_status": self.target_status,
        }


_PaperAccountEventDetails: TypeAlias = (
    _AccountCreatedDetails
    | _CashMovementPostedDetails
    | _PositionAdjustmentPostedDetails
    | _ExecutionFillPostedDetails
    | _PortfolioReviewEvidenceLinkedDetails
    | _LifecycleChangedDetails
)


@dataclass(frozen=True, init=False)
class PaperAccountEvent:
    """One immutable ordered account event with posting and chain digests."""

    event_id: str
    account_id: str
    sequence_number: int
    account_version: int
    event_type: PaperAccountEventType
    command_idempotency_key: str
    command_digest: str
    expected_account_version: int | None
    actor: str
    reason: str | None
    recorded_timestamp_utc: datetime
    effective_timestamp_utc: datetime | None
    previous_chain_digest: str
    details: _PaperAccountEventDetails
    event_digest: str
    chain_digest: str

    __init__ = _reject_public_construction

    def _header_without_result_digests(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_ACCOUNT_EVENT_SCHEMA_VERSION,
            "event_id": self.event_id,
            "account_id": self.account_id,
            "sequence_number": self.sequence_number,
            "account_version": self.account_version,
            "event_type": self.event_type,
            "command_idempotency_key": self.command_idempotency_key,
            "command_digest": self.command_digest,
            "expected_account_version": self.expected_account_version,
            "actor": self.actor,
            "reason": self.reason,
            "recorded_timestamp_utc": (
                self.recorded_timestamp_utc.isoformat()
            ),
            "effective_timestamp_utc": (
                self.effective_timestamp_utc.isoformat()
                if self.effective_timestamp_utc is not None
                else None
            ),
            "previous_chain_digest": self.previous_chain_digest,
        }

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible event header and details."""
        payload = self._header_without_result_digests()
        payload["details"] = self.details.to_dict()
        payload["event_digest"] = self.event_digest
        payload["chain_digest"] = self.chain_digest
        return payload


def _account_created_details(
    identity: PaperAccountIdentity,
    initial_cash: PaperMoney,
) -> _AccountCreatedDetails:
    result = object.__new__(_AccountCreatedDetails)
    object.__setattr__(result, "account_identity", identity)
    object.__setattr__(result, "initial_cash", initial_cash)
    return result


def _cash_movement_details(
    movement_type: PostPaperCashMovementType,
    requested_amount: PaperMoney,
) -> _CashMovementPostedDetails:
    result = object.__new__(_CashMovementPostedDetails)
    object.__setattr__(result, "movement_type", movement_type)
    object.__setattr__(result, "requested_amount", requested_amount)
    return result


def _evidence_linked_details(
    reference: ApprovedPortfolioReviewReference,
) -> _PortfolioReviewEvidenceLinkedDetails:
    result = object.__new__(_PortfolioReviewEvidenceLinkedDetails)
    object.__setattr__(result, "approved_portfolio_review", reference)
    return result


def _position_adjustment_details(
    *,
    symbol: str,
    adjustment_category: PaperPositionAdjustmentCategory,
    signed_quantity_delta: PaperQuantity,
    signed_cost_basis_delta: PaperMoney,
) -> _PositionAdjustmentPostedDetails:
    result = object.__new__(_PositionAdjustmentPostedDetails)
    object.__setattr__(result, "symbol", symbol)
    object.__setattr__(
        result,
        "adjustment_category",
        adjustment_category,
    )
    object.__setattr__(
        result,
        "signed_quantity_delta",
        signed_quantity_delta,
    )
    object.__setattr__(
        result,
        "signed_cost_basis_delta",
        signed_cost_basis_delta,
    )
    return result


def _execution_fill_posted_details(
    *,
    execution_order_id: str,
    execution_order_digest: str,
    execution_attempt_id: str,
    execution_attempt_digest: str,
    execution_fill_id: str,
    execution_fill_digest: str,
    instrument_id: str,
    side: str,
    fill_quantity: PaperQuantity,
    gross_notional: PaperMoney,
    total_charges: PaperMoney,
    signed_cash_delta: PaperMoney,
    signed_position_quantity_delta: PaperQuantity,
    signed_position_cost_basis_delta: PaperMoney,
) -> _ExecutionFillPostedDetails:
    result = object.__new__(_ExecutionFillPostedDetails)
    for field_name, value in locals().items():
        if field_name != "result":
            object.__setattr__(result, field_name, value)
    return result


def _lifecycle_changed_details(
    source_status: PaperAccountLifecycleStatus,
    target_status: PaperAccountLifecycleStatus,
) -> _LifecycleChangedDetails:
    result = object.__new__(_LifecycleChangedDetails)
    object.__setattr__(result, "source_status", source_status)
    object.__setattr__(result, "target_status", target_status)
    return result


def _event_digest_payload(
    event: PaperAccountEvent,
    cash_entries: tuple[PaperCashLedgerEntry, ...],
    position_entries: tuple[PaperPositionLedgerEntry, ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_header": event._header_without_result_digests(),
        "event_details": event.details.to_dict(),
        "cash_entries": [entry.to_dict() for entry in cash_entries],
    }
    if event.event_type in {
        "position_adjustment_posted",
        "execution_fill_posted",
    }:
        payload["position_entries"] = [
            entry.to_dict() for entry in position_entries
        ]
    return payload


def _create_event(
    *,
    event_id: str,
    account_id: str,
    sequence_number: int,
    event_type: PaperAccountEventType,
    command_idempotency_key: str,
    command_digest: str,
    expected_account_version: int | None,
    actor: str,
    reason: str | None,
    recorded_timestamp_utc: datetime,
    effective_timestamp_utc: datetime | None,
    previous_chain_digest: str,
    details: _PaperAccountEventDetails,
    cash_entries: tuple[PaperCashLedgerEntry, ...],
    position_entries: tuple[PaperPositionLedgerEntry, ...] = (),
) -> PaperAccountEvent:
    normalized_event_id = normalize_bounded_string(
        event_id,
        field_name="event_id",
        maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
    )
    normalized_account_id = normalize_bounded_string(
        account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    if type(sequence_number) is not int or sequence_number <= 0:
        raise ValueError("sequence_number must be a positive integer")
    if sequence_number == 1:
        if expected_account_version is not None:
            raise ValueError(
                "creation expected_account_version must be None"
            )
    elif (
        type(expected_account_version) is not int
        or expected_account_version <= 0
        or expected_account_version != sequence_number - 1
    ):
        raise ValueError(
            "expected_account_version must be the exact prior integer version"
        )
    if event_type not in SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES:
        raise ValueError("unsupported Paper Account event type")
    normalized_actor = normalize_bounded_string(
        actor,
        field_name="actor",
        maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )
    normalized_recorded = normalize_utc_datetime(
        recorded_timestamp_utc,
        field_name="recorded_timestamp_utc",
    )
    normalized_effective = (
        normalize_utc_datetime(
            effective_timestamp_utc,
            field_name="effective_timestamp_utc",
        )
        if effective_timestamp_utc is not None
        else None
    )
    validate_digest(command_digest, "command_digest")
    validate_digest(previous_chain_digest, "previous_chain_digest")

    result = object.__new__(PaperAccountEvent)
    object.__setattr__(result, "event_id", normalized_event_id)
    object.__setattr__(result, "account_id", normalized_account_id)
    object.__setattr__(result, "sequence_number", sequence_number)
    object.__setattr__(result, "account_version", sequence_number)
    object.__setattr__(result, "event_type", event_type)
    object.__setattr__(
        result,
        "command_idempotency_key",
        command_idempotency_key,
    )
    object.__setattr__(result, "command_digest", command_digest)
    object.__setattr__(
        result,
        "expected_account_version",
        expected_account_version,
    )
    object.__setattr__(result, "actor", normalized_actor)
    object.__setattr__(result, "reason", reason)
    object.__setattr__(
        result,
        "recorded_timestamp_utc",
        normalized_recorded,
    )
    object.__setattr__(
        result,
        "effective_timestamp_utc",
        normalized_effective,
    )
    object.__setattr__(
        result,
        "previous_chain_digest",
        previous_chain_digest,
    )
    object.__setattr__(result, "details", details)
    event_digest = canonical_digest(
        _event_digest_payload(result, cash_entries, position_entries)
    )
    object.__setattr__(result, "event_digest", event_digest)
    chain_digest = hashlib.sha256(
        (previous_chain_digest + event_digest).encode("ascii")
    ).hexdigest()
    object.__setattr__(result, "chain_digest", chain_digest)
    return result
