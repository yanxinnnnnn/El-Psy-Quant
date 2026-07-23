"""Pure cash-only Paper Account state derivation and command application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    money_from_decimal,
    normalize_utc_datetime,
    validate_digest,
)
from el_psy_quant.paper_account.cash_commands import (
    PostPaperCashMovementCommand,
)
from el_psy_quant.paper_account.cash_ledger import (
    PaperCashLedgerEntry,
    _create_cash_ledger_entry,
)
from el_psy_quant.paper_account.commands import (
    ClosePaperAccountCommand,
    CreatePaperAccountCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    ReactivatePaperAccountCommand,
)
from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.events import (
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    PaperAccountEvent,
    _account_created_details,
    _cash_movement_details,
    _create_event,
    _evidence_linked_details,
    _lifecycle_changed_details,
)
from el_psy_quant.paper_account.identity import PaperAccountIdentity
from el_psy_quant.paper_account.lifecycle import (
    SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES,
    PaperAccountCloseEligibility,
    PaperAccountLifecycleStatus,
    validate_paper_account_lifecycle_transition,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)

PAPER_ACCOUNT_CASH_STATE_SCHEMA_VERSION = 1
PAPER_ACCOUNT_EVENT_BUNDLE_SCHEMA_VERSION = 1


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("cash state and event bundles are derived by domain functions")


@dataclass(frozen=True, init=False)
class PaperAccountCashState:
    """Rebuildable cash-only state; not the complete M31 account projection."""

    account_identity: PaperAccountIdentity
    lifecycle_status: PaperAccountLifecycleStatus
    cash_balance: PaperMoney
    available_cash: PaperMoney
    approved_portfolio_reviews: tuple[
        ApprovedPortfolioReviewReference, ...
    ]
    head_version: int
    head_event_id: str
    head_chain_digest: str

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return exact JSON-compatible derived cash-only state."""
        return {
            "schema_version": PAPER_ACCOUNT_CASH_STATE_SCHEMA_VERSION,
            "account_identity": self.account_identity.to_dict(),
            "lifecycle_status": self.lifecycle_status,
            "cash_balance": self.cash_balance.to_json_value(),
            "available_cash": self.available_cash.to_json_value(),
            "approved_portfolio_reviews": [
                reference.to_dict()
                for reference in self.approved_portfolio_reviews
            ],
            "head_version": self.head_version,
            "head_event_id": self.head_event_id,
            "head_chain_digest": self.head_chain_digest,
        }


@dataclass(frozen=True, init=False)
class PaperAccountEventBundle:
    """One event, its zero-or-one cash posting, and resulting derived state."""

    event: PaperAccountEvent
    cash_entries: tuple[PaperCashLedgerEntry, ...]
    resulting_state: PaperAccountCashState

    __init__ = _reject_public_construction

    @property
    def cash_entry(self) -> PaperCashLedgerEntry | None:
        """Return the single cash entry when this event is financial."""
        return self.cash_entries[0] if self.cash_entries else None

    def to_dict(self) -> dict[str, object]:
        """Return one deterministic JSON-compatible in-memory bundle."""
        return {
            "schema_version": PAPER_ACCOUNT_EVENT_BUNDLE_SCHEMA_VERSION,
            "event": self.event.to_dict(),
            "cash_entries": [entry.to_dict() for entry in self.cash_entries],
            "resulting_state": self.resulting_state.to_dict(),
        }


def _verify_command(command: object) -> None:
    to_dict = getattr(command, "to_dict", None)
    if not callable(to_dict):
        raise ValueError("command must provide a canonical export")
    payload = to_dict()
    if not isinstance(payload, dict):
        raise ValueError("command export must be a dictionary")
    exported_digest = payload.pop("command_digest", None)
    actual_digest = getattr(command, "command_digest", None)
    if (
        exported_digest != actual_digest
        or actual_digest != canonical_digest(payload)
    ):
        raise ValueError("command digest does not match its canonical payload")
    validate_digest(actual_digest, "command_digest")


def _create_state(
    *,
    account_identity: PaperAccountIdentity,
    lifecycle_status: PaperAccountLifecycleStatus,
    cash_balance: PaperMoney,
    approved_portfolio_reviews: tuple[
        ApprovedPortfolioReviewReference, ...
    ],
    head_version: int,
    head_event_id: str,
    head_chain_digest: str,
) -> PaperAccountCashState:
    result = object.__new__(PaperAccountCashState)
    object.__setattr__(result, "account_identity", account_identity)
    object.__setattr__(result, "lifecycle_status", lifecycle_status)
    object.__setattr__(result, "cash_balance", cash_balance)
    object.__setattr__(result, "available_cash", cash_balance)
    object.__setattr__(
        result,
        "approved_portfolio_reviews",
        approved_portfolio_reviews,
    )
    object.__setattr__(result, "head_version", head_version)
    object.__setattr__(result, "head_event_id", head_event_id)
    object.__setattr__(result, "head_chain_digest", head_chain_digest)
    return result


def _create_bundle(
    *,
    event: PaperAccountEvent,
    cash_entries: tuple[PaperCashLedgerEntry, ...],
    resulting_state: PaperAccountCashState,
) -> PaperAccountEventBundle:
    result = object.__new__(PaperAccountEventBundle)
    object.__setattr__(result, "event", event)
    object.__setattr__(result, "cash_entries", cash_entries)
    object.__setattr__(result, "resulting_state", resulting_state)
    return result


def _validate_state(state: PaperAccountCashState) -> None:
    if type(state) is not PaperAccountCashState:
        raise ValueError("state must be PaperAccountCashState")
    if type(state.account_identity) is not PaperAccountIdentity:
        raise ValueError("state account identity is invalid")
    if state.lifecycle_status not in SUPPORTED_PAPER_ACCOUNT_LIFECYCLE_STATUSES:
        raise ValueError("state lifecycle status is invalid")
    if (
        type(state.cash_balance) is not PaperMoney
        or type(state.available_cash) is not PaperMoney
    ):
        raise ValueError("state cash values must be PaperMoney")
    if state.cash_balance != state.available_cash:
        raise ValueError("available_cash must equal cash_balance")
    if state.cash_balance.decimal_value < 0:
        raise ValueError("cash balance must not be negative")
    if (
        isinstance(state.head_version, bool)
        or not isinstance(state.head_version, int)
        or state.head_version <= 0
    ):
        raise ValueError("state head version must be a positive integer")
    validate_digest(state.head_chain_digest, "head_chain_digest")
    decision_ids: set[str] = set()
    for reference in state.approved_portfolio_reviews:
        if type(reference) is not ApprovedPortfolioReviewReference:
            raise ValueError("state contains an invalid evidence reference")
        if reference.decision_id in decision_ids:
            raise ValueError("state contains duplicate evidence decision IDs")
        decision_ids.add(reference.decision_id)


def _require_current_command(
    state: PaperAccountCashState,
    *,
    account_id: str,
    expected_account_version: int,
) -> None:
    _validate_state(state)
    if account_id != state.account_identity.account_id:
        raise ValueError("command account_id does not match current state")
    if expected_account_version != state.head_version:
        raise ValueError("expected_account_version does not match current state")


def create_paper_account_event_bundle(
    command: CreatePaperAccountCommand,
    *,
    event_id: str,
    cash_entry_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountEventBundle:
    """Apply account creation to one immutable event and initial-cash posting."""
    if type(command) is not CreatePaperAccountCommand:
        raise ValueError("command must be CreatePaperAccountCommand")
    _verify_command(command)
    identity = command.account_identity
    if command.actor != identity.created_by:
        raise ValueError("creation actor must match account_identity.created_by")
    recorded = normalize_utc_datetime(
        recorded_timestamp_utc,
        field_name="recorded_timestamp_utc",
    )
    if recorded != identity.created_timestamp:
        raise ValueError(
            "creation recorded timestamp must match identity created_timestamp"
        )

    entry = _create_cash_ledger_entry(
        cash_entry_id=cash_entry_id,
        account_id=identity.account_id,
        event_id=event_id,
        movement_type="initial_cash",
        currency=identity.base_currency,
        signed_amount=command.initial_cash,
    )
    entries = (entry,)
    event = _create_event(
        event_id=event_id,
        account_id=identity.account_id,
        sequence_number=1,
        event_type="account_created",
        command_idempotency_key=command.command_idempotency_key,
        command_digest=command.command_digest,
        expected_account_version=None,
        actor=command.actor,
        reason=None,
        recorded_timestamp_utc=recorded,
        effective_timestamp_utc=None,
        previous_chain_digest=PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
        details=_account_created_details(identity, command.initial_cash),
        cash_entries=entries,
    )
    state = _create_state(
        account_identity=identity,
        lifecycle_status="active",
        cash_balance=command.initial_cash,
        approved_portfolio_reviews=(),
        head_version=1,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_bundle(
        event=event,
        cash_entries=entries,
        resulting_state=state,
    )


def _signed_cash_movement(command: PostPaperCashMovementCommand) -> PaperMoney:
    amount = command.requested_amount.decimal_value
    if command.movement_type in {
        "withdrawal",
        "fee",
        "commission",
        "tax",
    }:
        amount = -amount
    return money_from_decimal(amount)


def apply_paper_cash_movement(
    state: PaperAccountCashState,
    command: PostPaperCashMovementCommand,
    *,
    event_id: str,
    cash_entry_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountEventBundle:
    """Apply one active-account cash command without persistence."""
    if type(command) is not PostPaperCashMovementCommand:
        raise ValueError("command must be PostPaperCashMovementCommand")
    _verify_command(command)
    _require_current_command(
        state,
        account_id=command.account_id,
        expected_account_version=command.expected_account_version,
    )
    if state.lifecycle_status != "active":
        raise ValueError("cash mutations require an active account")

    signed_amount = _signed_cash_movement(command)
    resulting_balance = money_from_decimal(
        state.cash_balance.decimal_value + signed_amount.decimal_value
    )
    if resulting_balance.decimal_value < 0:
        raise ValueError("cash movement would make cash negative")

    entry = _create_cash_ledger_entry(
        cash_entry_id=cash_entry_id,
        account_id=state.account_identity.account_id,
        event_id=event_id,
        movement_type=command.movement_type,
        currency=state.account_identity.base_currency,
        signed_amount=signed_amount,
    )
    entries = (entry,)
    next_version = state.head_version + 1
    event = _create_event(
        event_id=event_id,
        account_id=state.account_identity.account_id,
        sequence_number=next_version,
        event_type="cash_movement_posted",
        command_idempotency_key=command.command_idempotency_key,
        command_digest=command.command_digest,
        expected_account_version=command.expected_account_version,
        actor=command.actor,
        reason=command.reason,
        recorded_timestamp_utc=recorded_timestamp_utc,
        effective_timestamp_utc=command.effective_timestamp_utc,
        previous_chain_digest=state.head_chain_digest,
        details=_cash_movement_details(
            command.movement_type,
            command.requested_amount,
        ),
        cash_entries=entries,
    )
    next_state = _create_state(
        account_identity=state.account_identity,
        lifecycle_status=state.lifecycle_status,
        cash_balance=resulting_balance,
        approved_portfolio_reviews=state.approved_portfolio_reviews,
        head_version=next_version,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_bundle(
        event=event,
        cash_entries=entries,
        resulting_state=next_state,
    )


def apply_approved_portfolio_review_link(
    state: PaperAccountCashState,
    command: LinkApprovedPortfolioReviewCommand,
    *,
    event_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountEventBundle:
    """Apply one governance-only evidence link with no financial posting."""
    if type(command) is not LinkApprovedPortfolioReviewCommand:
        raise ValueError(
            "command must be LinkApprovedPortfolioReviewCommand"
        )
    _verify_command(command)
    _require_current_command(
        state,
        account_id=command.account_id,
        expected_account_version=command.expected_account_version,
    )
    if state.lifecycle_status != "active":
        raise ValueError("evidence links require an active account")
    reference = command.approved_portfolio_review
    if any(
        existing.decision_id == reference.decision_id
        for existing in state.approved_portfolio_reviews
    ):
        raise ValueError(
            "approved portfolio-review decision is already linked"
        )

    next_version = state.head_version + 1
    event = _create_event(
        event_id=event_id,
        account_id=state.account_identity.account_id,
        sequence_number=next_version,
        event_type="portfolio_review_evidence_linked",
        command_idempotency_key=command.command_idempotency_key,
        command_digest=command.command_digest,
        expected_account_version=command.expected_account_version,
        actor=command.actor,
        reason=command.reason,
        recorded_timestamp_utc=recorded_timestamp_utc,
        effective_timestamp_utc=None,
        previous_chain_digest=state.head_chain_digest,
        details=_evidence_linked_details(reference),
        cash_entries=(),
    )
    next_state = _create_state(
        account_identity=state.account_identity,
        lifecycle_status=state.lifecycle_status,
        cash_balance=state.cash_balance,
        approved_portfolio_reviews=(
            *state.approved_portfolio_reviews,
            reference,
        ),
        head_version=next_version,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_bundle(
        event=event,
        cash_entries=(),
        resulting_state=next_state,
    )


_LifecycleCommand = (
    FreezePaperAccountCommand
    | ReactivatePaperAccountCommand
    | ClosePaperAccountCommand
)


def apply_paper_account_lifecycle_command(
    state: PaperAccountCashState,
    command: _LifecycleCommand,
    *,
    event_id: str,
    recorded_timestamp_utc: datetime,
    close_eligibility: PaperAccountCloseEligibility | None = None,
) -> PaperAccountEventBundle:
    """Apply one exact lifecycle transition with no financial posting."""
    command_types = (
        FreezePaperAccountCommand,
        ReactivatePaperAccountCommand,
        ClosePaperAccountCommand,
    )
    if type(command) not in command_types:
        raise ValueError("command must be a supported lifecycle command")
    _verify_command(command)
    _require_current_command(
        state,
        account_id=command.account_id,
        expected_account_version=command.expected_account_version,
    )

    if type(command) is FreezePaperAccountCommand:
        target: PaperAccountLifecycleStatus = "frozen"
        event_type = "account_frozen"
    elif type(command) is ReactivatePaperAccountCommand:
        target = "active"
        event_type = "account_reactivated"
    else:
        target = "closed"
        event_type = "account_closed"
        if state.cash_balance.decimal_value != 0:
            raise ValueError("closing requires current derived cash to be zero")

    validate_paper_account_lifecycle_transition(
        state.lifecycle_status,
        target,
        close_eligibility=close_eligibility,
    )
    next_version = state.head_version + 1
    event = _create_event(
        event_id=event_id,
        account_id=state.account_identity.account_id,
        sequence_number=next_version,
        event_type=event_type,  # type: ignore[arg-type]
        command_idempotency_key=command.command_idempotency_key,
        command_digest=command.command_digest,
        expected_account_version=command.expected_account_version,
        actor=command.actor,
        reason=command.reason,
        recorded_timestamp_utc=recorded_timestamp_utc,
        effective_timestamp_utc=None,
        previous_chain_digest=state.head_chain_digest,
        details=_lifecycle_changed_details(
            state.lifecycle_status,
            target,
        ),
        cash_entries=(),
    )
    next_state = _create_state(
        account_identity=state.account_identity,
        lifecycle_status=target,
        cash_balance=state.cash_balance,
        approved_portfolio_reviews=state.approved_portfolio_reviews,
        head_version=next_version,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_bundle(
        event=event,
        cash_entries=(),
        resulting_state=next_state,
    )
