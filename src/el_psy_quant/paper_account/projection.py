"""Deterministic complete Paper Account projection and verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Literal

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
    validate_digest,
)
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.events import MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH
from el_psy_quant.paper_account.identity import (
    PaperAccountIdentity,
)
from el_psy_quant.paper_account.ledger_replay import (
    PaperAccountLedgerHistoryBundle,
    replay_paper_account_ledger,
)
from el_psy_quant.paper_account.ledger_state import (
    PaperAccountPosition,
    _create_position,
    _validate_position,
)
from el_psy_quant.paper_account.lifecycle import (
    SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES,
    PaperAccountLifecycleStatus,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)

PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION = 1
PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION = 1
PAPER_ACCOUNT_PROJECTION_VERIFICATION_SCHEMA_VERSION = 1

PaperAccountProjectionVerificationStatus = Literal[
    "current", "reconciliation_required"
]
PaperAccountProjectionMismatchCode = Literal[
    "source_account_version_mismatch",
    "source_event_id_mismatch",
    "source_chain_digest_mismatch",
    "identity_mismatch",
    "lifecycle_status_mismatch",
    "cash_balance_mismatch",
    "available_cash_mismatch",
    "positions_mismatch",
    "evidence_references_mismatch",
]

SUPPORTED_PAPER_ACCOUNT_PROJECTION_VERIFICATION_STATUSES = (
    "current",
    "reconciliation_required",
)
SUPPORTED_PAPER_ACCOUNT_PROJECTION_MISMATCH_CODES = (
    "source_account_version_mismatch",
    "source_event_id_mismatch",
    "source_chain_digest_mismatch",
    "identity_mismatch",
    "lifecycle_status_mismatch",
    "cash_balance_mismatch",
    "available_cash_mismatch",
    "positions_mismatch",
    "evidence_references_mismatch",
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("projections are derived by trusted replay functions")


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


def _validate_money(value: object, field_name: str) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    if type(value.canonical) is not str or type(value.decimal_value) is not Decimal:
        raise ValueError(f"{field_name} must be canonical PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be canonical PaperMoney") from exc
    if rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple():
        raise ValueError(f"{field_name} must be canonical PaperMoney")
    return value


def _validate_quantity(value: object) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError("position quantity must be PaperQuantity")
    if type(value.canonical) is not str or type(value.decimal_value) is not Decimal:
        raise ValueError("position quantity must be canonical PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except ValueError as exc:
        raise ValueError("position quantity must be canonical PaperQuantity") from exc
    if rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple():
        raise ValueError("position quantity must be canonical PaperQuantity")
    return value


def _validate_identity(identity: object) -> PaperAccountIdentity:
    if type(identity) is not PaperAccountIdentity:
        raise ValueError("projection account identity is invalid")
    for field_name in ("account_id", "display_name", "base_currency", "created_by"):
        if type(getattr(identity, field_name)) is not str:
            raise ValueError("projection account identity scalar types are invalid")
    if type(identity.created_timestamp) is not datetime:
        raise ValueError("projection account identity timestamp is invalid")
    if identity.created_timestamp.tzinfo is not timezone.utc:
        raise ValueError("projection account identity timestamp must be UTC")
    try:
        rebuilt = PaperAccountIdentity(
            account_id=identity.account_id,
            display_name=identity.display_name,
            base_currency=identity.base_currency,
            created_by=identity.created_by,
            created_timestamp=identity.created_timestamp,
        )
    except ValueError as exc:
        raise ValueError("projection account identity is invalid") from exc
    if rebuilt.to_dict() != identity.to_dict():
        raise ValueError("projection account identity is not canonical")
    return identity


def _reference_sort_key(
    reference: ApprovedPortfolioReviewReference,
) -> tuple[str, str, str, str]:
    return (
        reference.decision_id,
        reference.review_id,
        reference.source_id,
        reference.decision_digest,
    )


def _validate_reference(
    reference: object,
) -> ApprovedPortfolioReviewReference:
    if type(reference) is not ApprovedPortfolioReviewReference:
        raise ValueError("projection contains an invalid evidence reference")
    for field_name in ("review_id", "source_id", "decision_id"):
        _exact_normalized(
            getattr(reference, field_name),
            field_name=field_name,
            maximum_length=512,
        )
    for field_name in (
        "source_digest",
        "analysis_digest",
        "decision_digest",
    ):
        _exact_digest(getattr(reference, field_name), field_name)
    if type(reference.outcome) is not str or reference.outcome != "approved":
        raise ValueError("projection evidence outcome must be approved")
    return reference


@dataclass(frozen=True, init=False)
class PaperAccountPositionProjection:
    """One exact derived position cache payload."""

    symbol: str
    quantity: PaperQuantity
    aggregate_cost_basis: PaperMoney
    average_unit_cost: str | None
    average_unit_cost_is_rounded: bool

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return one strictly validated JSON-compatible position."""
        _validate_position_projection(self)
        return _position_payload(self)


def _position_payload(
    position: PaperAccountPositionProjection,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION,
        "symbol": position.symbol,
        "quantity": position.quantity.to_json_value(),
        "aggregate_cost_basis": position.aggregate_cost_basis.to_json_value(),
        "average_unit_cost": position.average_unit_cost,
        "average_unit_cost_is_rounded": position.average_unit_cost_is_rounded,
    }


def _create_position_projection(
    position: PaperAccountPosition,
) -> PaperAccountPositionProjection:
    _validate_position(position)
    result = object.__new__(PaperAccountPositionProjection)
    for field_name in (
        "symbol",
        "quantity",
        "aggregate_cost_basis",
        "average_unit_cost",
        "average_unit_cost_is_rounded",
    ):
        object.__setattr__(result, field_name, getattr(position, field_name))
    return result


def _validate_position_projection(
    position: object,
) -> PaperAccountPositionProjection:
    if type(position) is not PaperAccountPositionProjection:
        raise ValueError("projection contains an invalid position")
    _validate_quantity(position.quantity)
    _validate_money(position.aggregate_cost_basis, "aggregate_cost_basis")
    if type(position.average_unit_cost_is_rounded) is not bool:
        raise ValueError("average_unit_cost_is_rounded must be an exact boolean")
    try:
        rebuilt = _create_position(
            symbol=position.symbol,
            quantity=PaperQuantity.parse(position.quantity.canonical),
            aggregate_cost_basis=PaperMoney.parse(
                position.aggregate_cost_basis.canonical
            ),
        )
        _validate_position(rebuilt)
    except (AttributeError, ValueError) as exc:
        raise ValueError("projection position is not canonical") from exc
    if (
        position.symbol != rebuilt.symbol
        or position.average_unit_cost != rebuilt.average_unit_cost
        or position.average_unit_cost_is_rounded
        is not rebuilt.average_unit_cost_is_rounded
        or position.quantity.decimal_value.as_tuple()
        != rebuilt.quantity.decimal_value.as_tuple()
        or position.aggregate_cost_basis.decimal_value.as_tuple()
        != rebuilt.aggregate_cost_basis.decimal_value.as_tuple()
    ):
        raise ValueError("projection position is not canonical")
    return position


@dataclass(frozen=True, init=False)
class PaperAccountProjection:
    """Complete rebuildable cache payload at one immutable ledger head."""

    account_identity: PaperAccountIdentity
    lifecycle_status: PaperAccountLifecycleStatus
    cash_balance: PaperMoney
    available_cash: PaperMoney
    positions: tuple[PaperAccountPositionProjection, ...]
    approved_portfolio_reviews: tuple[ApprovedPortfolioReviewReference, ...]
    source_account_version: int
    source_event_id: str
    source_chain_digest: str
    projection_digest: str

    __init__ = _reject_public_construction

    @property
    def account_id(self) -> str:
        """Return the stable account ID for compact callers."""
        return self.account_identity.account_id

    def to_dict(self) -> dict[str, object]:
        """Return the deeply validated canonical projection export."""
        _validate_projection(self)
        payload = _projection_payload_without_digest(self)
        payload["projection_digest"] = self.projection_digest
        return payload


def _projection_payload_without_digest(
    projection: PaperAccountProjection,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION,
        "account_identity": projection.account_identity.to_dict(),
        "lifecycle_status": projection.lifecycle_status,
        "cash_balance": projection.cash_balance.to_json_value(),
        "available_cash": projection.available_cash.to_json_value(),
        "positions": [_position_payload(item) for item in projection.positions],
        "approved_portfolio_reviews": [
            item.to_dict() for item in projection.approved_portfolio_reviews
        ],
        "source_account_version": projection.source_account_version,
        "source_event_id": projection.source_event_id,
        "source_chain_digest": projection.source_chain_digest,
    }


def _create_projection(
    *,
    account_identity: PaperAccountIdentity,
    lifecycle_status: PaperAccountLifecycleStatus,
    cash_balance: PaperMoney,
    available_cash: PaperMoney,
    positions: tuple[PaperAccountPositionProjection, ...],
    approved_portfolio_reviews: tuple[ApprovedPortfolioReviewReference, ...],
    source_account_version: int,
    source_event_id: str,
    source_chain_digest: str,
) -> PaperAccountProjection:
    result = object.__new__(PaperAccountProjection)
    object.__setattr__(result, "account_identity", account_identity)
    object.__setattr__(result, "lifecycle_status", lifecycle_status)
    object.__setattr__(result, "cash_balance", cash_balance)
    object.__setattr__(result, "available_cash", available_cash)
    object.__setattr__(result, "positions", positions)
    object.__setattr__(
        result, "approved_portfolio_reviews", approved_portfolio_reviews
    )
    object.__setattr__(result, "source_account_version", source_account_version)
    object.__setattr__(result, "source_event_id", source_event_id)
    object.__setattr__(result, "source_chain_digest", source_chain_digest)
    object.__setattr__(
        result,
        "projection_digest",
        canonical_digest(_projection_payload_without_digest(result)),
    )
    _validate_projection(result)
    return result


def _validate_projection(projection: object) -> PaperAccountProjection:
    if type(projection) is not PaperAccountProjection:
        raise ValueError("candidate projection must be PaperAccountProjection")
    _validate_identity(projection.account_identity)
    if (
        type(projection.lifecycle_status) is not str
        or projection.lifecycle_status
        not in SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES
    ):
        raise ValueError("projection lifecycle status is invalid")
    cash = _validate_money(projection.cash_balance, "cash_balance")
    available = _validate_money(projection.available_cash, "available_cash")
    if cash.canonical != available.canonical:
        raise ValueError("projection available_cash must equal cash_balance")
    if cash.decimal_value < 0:
        raise ValueError("projection cash balance must not be negative")
    if type(projection.positions) is not tuple:
        raise ValueError("projection positions must use immutable tuple ordering")
    symbols = [
        _validate_position_projection(item).symbol for item in projection.positions
    ]
    if symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
        raise ValueError(
            "projection positions must be unique and ordered by normalized symbol"
        )
    if type(projection.approved_portfolio_reviews) is not tuple:
        raise ValueError(
            "projection evidence references must use immutable tuple ordering"
        )
    references = [
        _validate_reference(item)
        for item in projection.approved_portfolio_reviews
    ]
    keys = [_reference_sort_key(item) for item in references]
    decision_ids = [item.decision_id for item in references]
    if keys != sorted(keys) or len(decision_ids) != len(set(decision_ids)):
        raise ValueError(
            "projection evidence references must be unique and ordered"
        )
    if (
        type(projection.source_account_version) is not int
        or projection.source_account_version <= 0
    ):
        raise ValueError("source_account_version must be an exact positive integer")
    _exact_normalized(
        projection.source_event_id,
        field_name="source_event_id",
        maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
    )
    _exact_digest(projection.source_chain_digest, "source_chain_digest")
    _exact_digest(projection.projection_digest, "projection_digest")
    if canonical_digest(
        _projection_payload_without_digest(projection)
    ) != projection.projection_digest:
        raise ValueError("projection digest does not match its canonical payload")
    return projection


def rebuild_paper_account_projection(
    history: Iterable[PaperAccountLedgerHistoryBundle],
) -> PaperAccountProjection:
    """Rebuild one complete projection only through authoritative replay."""
    state = replay_paper_account_ledger(history)
    positions = tuple(_create_position_projection(item) for item in state.positions)
    references = tuple(
        sorted(state.approved_portfolio_reviews, key=_reference_sort_key)
    )
    return _create_projection(
        account_identity=state.account_identity,
        lifecycle_status=state.lifecycle_status,
        cash_balance=state.cash_balance,
        available_cash=state.available_cash,
        positions=positions,
        approved_portfolio_reviews=references,
        source_account_version=state.head_version,
        source_event_id=state.head_event_id,
        source_chain_digest=state.head_chain_digest,
    )


@dataclass(frozen=True, init=False)
class PaperAccountProjectionVerification:
    """Immutable comparison result that never repairs its candidate."""

    status: PaperAccountProjectionVerificationStatus
    mismatch_codes: tuple[PaperAccountProjectionMismatchCode, ...]
    authoritative_account_version: int
    authoritative_event_id: str
    authoritative_chain_digest: str
    authoritative_projection_digest: str
    candidate_account_version: int
    candidate_event_id: str
    candidate_chain_digest: str
    candidate_projection_digest: str

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return deterministic verification evidence."""
        return {
            "schema_version": PAPER_ACCOUNT_PROJECTION_VERIFICATION_SCHEMA_VERSION,
            "status": self.status,
            "mismatch_codes": list(self.mismatch_codes),
            "authoritative_account_version": self.authoritative_account_version,
            "authoritative_event_id": self.authoritative_event_id,
            "authoritative_chain_digest": self.authoritative_chain_digest,
            "authoritative_projection_digest": self.authoritative_projection_digest,
            "candidate_account_version": self.candidate_account_version,
            "candidate_event_id": self.candidate_event_id,
            "candidate_chain_digest": self.candidate_chain_digest,
            "candidate_projection_digest": self.candidate_projection_digest,
        }


def _create_verification(
    authoritative: PaperAccountProjection,
    candidate: PaperAccountProjection,
    mismatch_codes: tuple[PaperAccountProjectionMismatchCode, ...],
) -> PaperAccountProjectionVerification:
    result = object.__new__(PaperAccountProjectionVerification)
    status: PaperAccountProjectionVerificationStatus = (
        "current" if not mismatch_codes else "reconciliation_required"
    )
    object.__setattr__(result, "status", status)
    object.__setattr__(result, "mismatch_codes", mismatch_codes)
    object.__setattr__(
        result, "authoritative_account_version", authoritative.source_account_version
    )
    object.__setattr__(result, "authoritative_event_id", authoritative.source_event_id)
    object.__setattr__(
        result, "authoritative_chain_digest", authoritative.source_chain_digest
    )
    object.__setattr__(
        result, "authoritative_projection_digest", authoritative.projection_digest
    )
    object.__setattr__(
        result, "candidate_account_version", candidate.source_account_version
    )
    object.__setattr__(result, "candidate_event_id", candidate.source_event_id)
    object.__setattr__(result, "candidate_chain_digest", candidate.source_chain_digest)
    object.__setattr__(
        result, "candidate_projection_digest", candidate.projection_digest
    )
    return result


def verify_paper_account_projection(
    history: Iterable[PaperAccountLedgerHistoryBundle],
    candidate_projection: PaperAccountProjection,
) -> PaperAccountProjectionVerification:
    """Compare a valid candidate with replay without mutating or repairing it."""
    candidate = _validate_projection(candidate_projection)
    authoritative = rebuild_paper_account_projection(history)
    if candidate.account_id != authoritative.account_id:
        raise ValueError("candidate projection belongs to a different account")

    comparisons = (
        (
            "source_account_version_mismatch",
            candidate.source_account_version
            != authoritative.source_account_version,
        ),
        (
            "source_event_id_mismatch",
            candidate.source_event_id != authoritative.source_event_id,
        ),
        (
            "source_chain_digest_mismatch",
            candidate.source_chain_digest != authoritative.source_chain_digest,
        ),
        (
            "identity_mismatch",
            candidate.account_identity != authoritative.account_identity,
        ),
        (
            "lifecycle_status_mismatch",
            candidate.lifecycle_status != authoritative.lifecycle_status,
        ),
        (
            "cash_balance_mismatch",
            candidate.cash_balance != authoritative.cash_balance,
        ),
        (
            "available_cash_mismatch",
            candidate.available_cash != authoritative.available_cash,
        ),
        ("positions_mismatch", candidate.positions != authoritative.positions),
        (
            "evidence_references_mismatch",
            candidate.approved_portfolio_reviews
            != authoritative.approved_portfolio_reviews,
        ),
    )
    mismatch_codes = tuple(
        code for code, mismatched in comparisons if mismatched
    )
    return _create_verification(
        authoritative,
        candidate,
        mismatch_codes,  # type: ignore[arg-type]
    )
