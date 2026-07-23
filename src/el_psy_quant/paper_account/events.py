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
from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountIdentity,
)
from el_psy_quant.paper_account.lifecycle import PaperAccountLifecycleStatus
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
    "portfolio_review_evidence_linked",
    "account_frozen",
    "account_reactivated",
    "account_closed",
]

SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES = (
    "account_created",
    "cash_movement_posted",
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
) -> dict[str, object]:
    return {
        "event_header": event._header_without_result_digests(),
        "event_details": event.details.to_dict(),
        "cash_entries": [entry.to_dict() for entry in cash_entries],
    }


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
    if (
        isinstance(sequence_number, bool)
        or not isinstance(sequence_number, int)
        or sequence_number <= 0
    ):
        raise ValueError("sequence_number must be a positive integer")
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
    event_digest = canonical_digest(_event_digest_payload(result, cash_entries))
    object.__setattr__(result, "event_digest", event_digest)
    chain_digest = hashlib.sha256(
        (previous_chain_digest + event_digest).encode("ascii")
    ).hexdigest()
    object.__setattr__(result, "chain_digest", chain_digest)
    return result
