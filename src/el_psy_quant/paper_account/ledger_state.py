"""Complete pure cash-plus-position Paper Account ledger state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from el_psy_quant.paper_account._shared import (
    money_from_decimal,
    quantity_from_decimal,
)
from el_psy_quant.paper_account.cash_ledger import PaperCashLedgerEntry
from el_psy_quant.paper_account.cash_state import (
    PaperAccountCashState,
    _create_state,
    _validate_state,
    _verify_command,
)
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.events import (
    PaperAccountEvent,
    _create_event,
    _position_adjustment_details,
)
from el_psy_quant.paper_account.identity import PaperAccountIdentity
from el_psy_quant.paper_account.lifecycle import PaperAccountLifecycleStatus
from el_psy_quant.paper_account.position_commands import (
    PostPaperPositionAdjustmentCommand,
    _normalize_position_symbol,
)
from el_psy_quant.paper_account.position_ledger import (
    PaperPositionLedgerEntry,
    _create_position_ledger_entry,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)

PAPER_ACCOUNT_POSITION_SCHEMA_VERSION = 1
PAPER_ACCOUNT_LEDGER_STATE_SCHEMA_VERSION = 1
PAPER_ACCOUNT_LEDGER_EVENT_BUNDLE_SCHEMA_VERSION = 1

_AVERAGE_UNIT_COST_QUANTUM = Decimal("0.00000001")
_POSITION_ARITHMETIC_PRECISION = 100
_POSITION_DECIMAL_CONTEXT = Context(
    prec=_POSITION_ARITHMETIC_PRECISION,
    rounding=ROUND_HALF_EVEN,
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(
        "positions, ledger state, and bundles are derived by domain functions"
    )


def _canonical_decimal(value: Decimal) -> str:
    canonical = format(value, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"", "-0"}:
        return "0"
    return canonical


def _add_exact(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_POSITION_DECIMAL_CONTEXT):
        return left + right


def _derive_average_unit_cost(
    *,
    quantity: PaperQuantity,
    aggregate_cost_basis: PaperMoney,
) -> tuple[str | None, bool]:
    if quantity.decimal_value == 0:
        return None, False
    with localcontext(_POSITION_DECIMAL_CONTEXT):
        quotient = aggregate_cost_basis.decimal_value / quantity.decimal_value
        rounded = quotient.quantize(
            _AVERAGE_UNIT_COST_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
        is_rounded = (
            rounded * quantity.decimal_value
            != aggregate_cost_basis.decimal_value
        )
    return _canonical_decimal(rounded), is_rounded


@dataclass(frozen=True, init=False)
class PaperAccountPosition:
    """One exact current long-only position derived from immutable postings."""

    symbol: str
    quantity: PaperQuantity
    aggregate_cost_basis: PaperMoney
    average_unit_cost: str | None
    average_unit_cost_is_rounded: bool

    __init__ = _reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return deterministic display information and exact authorities."""
        return {
            "schema_version": PAPER_ACCOUNT_POSITION_SCHEMA_VERSION,
            "symbol": self.symbol,
            "quantity": self.quantity.to_json_value(),
            "aggregate_cost_basis": (
                self.aggregate_cost_basis.to_json_value()
            ),
            "average_unit_cost": self.average_unit_cost,
            "average_unit_cost_is_rounded": (
                self.average_unit_cost_is_rounded
            ),
        }


def _create_position(
    *,
    symbol: str,
    quantity: PaperQuantity,
    aggregate_cost_basis: PaperMoney,
) -> PaperAccountPosition:
    normalized_symbol = _normalize_position_symbol(symbol)
    if normalized_symbol != symbol:
        raise ValueError("position symbol must already be normalized")
    if type(quantity) is not PaperQuantity:
        raise ValueError("position quantity must be PaperQuantity")
    if type(aggregate_cost_basis) is not PaperMoney:
        raise ValueError("position aggregate cost basis must be PaperMoney")
    if quantity.decimal_value < 0:
        raise ValueError("position quantity must not be negative")
    if aggregate_cost_basis.decimal_value < 0:
        raise ValueError("position aggregate cost basis must not be negative")
    if (
        quantity.decimal_value == 0
        and aggregate_cost_basis.decimal_value != 0
    ):
        raise ValueError(
            "zero position quantity requires zero aggregate cost basis"
        )
    average, is_rounded = _derive_average_unit_cost(
        quantity=quantity,
        aggregate_cost_basis=aggregate_cost_basis,
    )
    result = object.__new__(PaperAccountPosition)
    object.__setattr__(result, "symbol", normalized_symbol)
    object.__setattr__(result, "quantity", quantity)
    object.__setattr__(
        result,
        "aggregate_cost_basis",
        aggregate_cost_basis,
    )
    object.__setattr__(result, "average_unit_cost", average)
    object.__setattr__(
        result,
        "average_unit_cost_is_rounded",
        is_rounded,
    )
    return result


def _validate_position(position: object) -> PaperAccountPosition:
    if type(position) is not PaperAccountPosition:
        raise ValueError("state contains an invalid position")
    if type(position.average_unit_cost_is_rounded) is not bool:
        raise ValueError(
            "position average_unit_cost_is_rounded must be a boolean"
        )
    try:
        rebuilt_quantity = PaperQuantity.parse(position.quantity.canonical)
        rebuilt_cost = PaperMoney.parse(position.aggregate_cost_basis.canonical)
        rebuilt = _create_position(
            symbol=position.symbol,
            quantity=rebuilt_quantity,
            aggregate_cost_basis=rebuilt_cost,
        )
    except (AttributeError, ValueError) as exc:
        raise ValueError("state contains a non-canonical position") from exc
    if rebuilt.quantity.decimal_value == 0:
        if position.average_unit_cost is not None:
            raise ValueError(
                "zero-quantity position average_unit_cost must be None"
            )
        if position.average_unit_cost_is_rounded is not False:
            raise ValueError(
                "zero-quantity position average cost cannot be rounded"
            )
    else:
        if type(position.average_unit_cost) is not str:
            raise ValueError(
                "positive-quantity position average_unit_cost must be a string"
            )
        if position.average_unit_cost != rebuilt.average_unit_cost:
            raise ValueError(
                "position average_unit_cost is not the canonical derived value"
            )
        if (
            position.average_unit_cost_is_rounded
            is not rebuilt.average_unit_cost_is_rounded
        ):
            raise ValueError(
                "position average_unit_cost_is_rounded does not match "
                "the derived value"
            )
    if (
        rebuilt != position
        or rebuilt.quantity.decimal_value.as_tuple()
        != position.quantity.decimal_value.as_tuple()
        or rebuilt.aggregate_cost_basis.decimal_value.as_tuple()
        != position.aggregate_cost_basis.decimal_value.as_tuple()
    ):
        raise ValueError("state contains a non-canonical position")
    if position.quantity.decimal_value <= 0:
        raise ValueError("current positions must have positive quantity")
    return position


@dataclass(frozen=True, init=False)
class PaperAccountLedgerState:
    """Complete rebuildable cash-plus-position state at one event head."""

    account_identity: PaperAccountIdentity
    lifecycle_status: PaperAccountLifecycleStatus
    cash_balance: PaperMoney
    available_cash: PaperMoney
    positions: tuple[PaperAccountPosition, ...]
    approved_portfolio_reviews: tuple[
        ApprovedPortfolioReviewReference, ...
    ]
    head_version: int
    head_event_id: str
    head_chain_digest: str

    __init__ = _reject_public_construction

    def to_cash_state(self) -> PaperAccountCashState:
        """Return the explicit incomplete Sprint 181 cash compatibility view."""
        return _create_state(
            account_identity=self.account_identity,
            lifecycle_status=self.lifecycle_status,
            cash_balance=self.cash_balance,
            approved_portfolio_reviews=self.approved_portfolio_reviews,
            head_version=self.head_version,
            head_event_id=self.head_event_id,
            head_chain_digest=self.head_chain_digest,
        )

    def to_dict(self) -> dict[str, object]:
        """Return exact deterministic JSON-compatible complete ledger state."""
        return {
            "schema_version": PAPER_ACCOUNT_LEDGER_STATE_SCHEMA_VERSION,
            "account_identity": self.account_identity.to_dict(),
            "lifecycle_status": self.lifecycle_status,
            "cash_balance": self.cash_balance.to_json_value(),
            "available_cash": self.available_cash.to_json_value(),
            "positions": [position.to_dict() for position in self.positions],
            "approved_portfolio_reviews": [
                reference.to_dict()
                for reference in self.approved_portfolio_reviews
            ],
            "head_version": self.head_version,
            "head_event_id": self.head_event_id,
            "head_chain_digest": self.head_chain_digest,
        }


def _create_ledger_state(
    *,
    account_identity: PaperAccountIdentity,
    lifecycle_status: PaperAccountLifecycleStatus,
    cash_balance: PaperMoney,
    positions: tuple[PaperAccountPosition, ...],
    approved_portfolio_reviews: tuple[
        ApprovedPortfolioReviewReference, ...
    ],
    head_version: int,
    head_event_id: str,
    head_chain_digest: str,
) -> PaperAccountLedgerState:
    result = object.__new__(PaperAccountLedgerState)
    object.__setattr__(result, "account_identity", account_identity)
    object.__setattr__(result, "lifecycle_status", lifecycle_status)
    object.__setattr__(result, "cash_balance", cash_balance)
    object.__setattr__(result, "available_cash", cash_balance)
    object.__setattr__(result, "positions", positions)
    object.__setattr__(
        result,
        "approved_portfolio_reviews",
        approved_portfolio_reviews,
    )
    object.__setattr__(result, "head_version", head_version)
    object.__setattr__(result, "head_event_id", head_event_id)
    object.__setattr__(result, "head_chain_digest", head_chain_digest)
    return result


def _validate_ledger_state(state: object) -> PaperAccountLedgerState:
    if type(state) is not PaperAccountLedgerState:
        raise ValueError("state must be PaperAccountLedgerState")
    try:
        cash_view = state.to_cash_state()
        _validate_state(cash_view)
    except (AttributeError, ValueError) as exc:
        raise ValueError("ledger state cash/header values are invalid") from exc
    if type(state.positions) is not tuple:
        raise ValueError("state positions must use immutable tuple ordering")
    symbols: list[str] = []
    for position in state.positions:
        validated = _validate_position(position)
        symbols.append(validated.symbol)
    if symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
        raise ValueError(
            "state positions must be unique and ordered by normalized symbol"
        )
    return state


@dataclass(frozen=True, init=False)
class PaperAccountLedgerEventBundle:
    """One event, its posting groups, and resulting complete ledger state."""

    event: PaperAccountEvent
    cash_entries: tuple[PaperCashLedgerEntry, ...]
    position_entries: tuple[PaperPositionLedgerEntry, ...]
    resulting_state: PaperAccountLedgerState

    __init__ = _reject_public_construction

    @property
    def cash_entry(self) -> PaperCashLedgerEntry | None:
        """Return a single cash posting when one exists."""
        return self.cash_entries[0] if self.cash_entries else None

    @property
    def position_entry(self) -> PaperPositionLedgerEntry | None:
        """Return a single position posting when one exists."""
        return self.position_entries[0] if self.position_entries else None

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible in-memory bundle."""
        return {
            "schema_version": (
                PAPER_ACCOUNT_LEDGER_EVENT_BUNDLE_SCHEMA_VERSION
            ),
            "event": self.event.to_dict(),
            "cash_entries": [entry.to_dict() for entry in self.cash_entries],
            "position_entries": [
                entry.to_dict() for entry in self.position_entries
            ],
            "resulting_state": self.resulting_state.to_dict(),
        }


def _create_ledger_bundle(
    *,
    event: PaperAccountEvent,
    cash_entries: tuple[PaperCashLedgerEntry, ...],
    position_entries: tuple[PaperPositionLedgerEntry, ...],
    resulting_state: PaperAccountLedgerState,
) -> PaperAccountLedgerEventBundle:
    result = object.__new__(PaperAccountLedgerEventBundle)
    object.__setattr__(result, "event", event)
    object.__setattr__(result, "cash_entries", cash_entries)
    object.__setattr__(result, "position_entries", position_entries)
    object.__setattr__(result, "resulting_state", resulting_state)
    return result


def apply_paper_position_adjustment(
    state: PaperAccountLedgerState,
    command: PostPaperPositionAdjustmentCommand,
    *,
    event_id: str,
    position_entry_id: str,
    recorded_timestamp_utc: datetime,
) -> PaperAccountLedgerEventBundle:
    """Apply one exact active-account position adjustment without persistence."""
    if type(command) is not PostPaperPositionAdjustmentCommand:
        raise ValueError(
            "command must be PostPaperPositionAdjustmentCommand"
        )
    _verify_command(command)
    try:
        rebuilt_quantity = PaperQuantity.parse(
            command.signed_quantity_delta.canonical
        )
        rebuilt_cost = PaperMoney.parse(
            command.signed_cost_basis_delta.canonical
        )
        if (
            rebuilt_quantity.decimal_value.as_tuple()
            != command.signed_quantity_delta.decimal_value.as_tuple()
            or rebuilt_cost.decimal_value.as_tuple()
            != command.signed_cost_basis_delta.decimal_value.as_tuple()
        ):
            raise ValueError("position command values are not canonical")
        rebuilt_command = PostPaperPositionAdjustmentCommand(
            account_id=command.account_id,
            expected_account_version=command.expected_account_version,
            command_idempotency_key=command.command_idempotency_key,
            actor=command.actor,
            reason=command.reason,
            symbol=command.symbol,
            adjustment_category=command.adjustment_category,
            signed_quantity_delta=command.signed_quantity_delta,
            signed_cost_basis_delta=command.signed_cost_basis_delta,
            effective_timestamp_utc=command.effective_timestamp_utc,
        )
    except (AttributeError, ValueError) as exc:
        raise ValueError("position command values are invalid") from exc
    if rebuilt_command != command:
        raise ValueError("position command values are not canonical")
    _validate_ledger_state(state)
    if command.account_id != state.account_identity.account_id:
        raise ValueError("command account_id does not match current state")
    if command.expected_account_version != state.head_version:
        raise ValueError(
            "expected_account_version does not match current state"
        )
    if state.lifecycle_status != "active":
        raise ValueError("position mutations require an active account")

    existing = {position.symbol: position for position in state.positions}
    prior = existing.get(command.symbol)
    prior_quantity = (
        prior.quantity.decimal_value if prior is not None else Decimal("0")
    )
    prior_cost = (
        prior.aggregate_cost_basis.decimal_value
        if prior is not None
        else Decimal("0")
    )
    resulting_quantity = quantity_from_decimal(
        _add_exact(
            prior_quantity,
            command.signed_quantity_delta.decimal_value,
        )
    )
    resulting_cost = money_from_decimal(
        _add_exact(
            prior_cost,
            command.signed_cost_basis_delta.decimal_value,
        )
    )
    if resulting_quantity.decimal_value < 0:
        raise ValueError("position adjustment would make quantity negative")
    if resulting_cost.decimal_value < 0:
        raise ValueError(
            "position adjustment would make aggregate cost basis negative"
        )
    if (
        resulting_quantity.decimal_value == 0
        and resulting_cost.decimal_value != 0
    ):
        raise ValueError(
            "zero position quantity requires zero aggregate cost basis"
        )

    if resulting_quantity.decimal_value == 0:
        existing.pop(command.symbol, None)
    else:
        existing[command.symbol] = _create_position(
            symbol=command.symbol,
            quantity=resulting_quantity,
            aggregate_cost_basis=resulting_cost,
        )
    positions = tuple(existing[symbol] for symbol in sorted(existing))

    entry = _create_position_ledger_entry(
        position_entry_id=position_entry_id,
        account_id=state.account_identity.account_id,
        event_id=event_id,
        symbol=command.symbol,
        signed_quantity_delta=command.signed_quantity_delta,
        signed_cost_basis_delta=command.signed_cost_basis_delta,
        adjustment_category=command.adjustment_category,
    )
    position_entries = (entry,)
    next_version = state.head_version + 1
    event = _create_event(
        event_id=event_id,
        account_id=state.account_identity.account_id,
        sequence_number=next_version,
        event_type="position_adjustment_posted",
        command_idempotency_key=command.command_idempotency_key,
        command_digest=command.command_digest,
        expected_account_version=command.expected_account_version,
        actor=command.actor,
        reason=command.reason,
        recorded_timestamp_utc=recorded_timestamp_utc,
        effective_timestamp_utc=command.effective_timestamp_utc,
        previous_chain_digest=state.head_chain_digest,
        details=_position_adjustment_details(
            symbol=command.symbol,
            adjustment_category=command.adjustment_category,
            signed_quantity_delta=command.signed_quantity_delta,
            signed_cost_basis_delta=command.signed_cost_basis_delta,
        ),
        cash_entries=(),
        position_entries=position_entries,
    )
    next_state = _create_ledger_state(
        account_identity=state.account_identity,
        lifecycle_status=state.lifecycle_status,
        cash_balance=state.cash_balance,
        positions=positions,
        approved_portfolio_reviews=state.approved_portfolio_reviews,
        head_version=next_version,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_ledger_bundle(
        event=event,
        cash_entries=(),
        position_entries=position_entries,
        resulting_state=next_state,
    )
