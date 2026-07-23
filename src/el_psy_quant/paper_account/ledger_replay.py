"""Fail-closed replay of the complete Paper Account cash and position ledger."""

from __future__ import annotations

import hashlib
from typing import Iterable, TypeAlias

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    money_from_decimal,
    normalize_bounded_string,
    quantity_from_decimal,
    validate_digest,
)
from el_psy_quant.paper_account.cash_state import (
    PaperAccountEventBundle,
    _signed_cash_movement,
    _validate_state,
)
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.events import (
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    PaperAccountEvent,
    _PositionAdjustmentPostedDetails,
    _event_digest_payload,
)
from el_psy_quant.paper_account.identity import PaperAccountIdentity
from el_psy_quant.paper_account.ledger_state import (
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperAccountPosition,
    _add_exact,
    _create_ledger_state,
    _create_position,
    _validate_ledger_state,
)
from el_psy_quant.paper_account.position_commands import (
    SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES,
    PostPaperPositionAdjustmentCommand,
    _normalize_position_symbol,
)
from el_psy_quant.paper_account.position_ledger import (
    PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION,
    PaperPositionLedgerEntry,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)
from el_psy_quant.paper_account.replay import (
    _validate_entry,
    _validate_event_header,
    _validate_money,
    _verify_cash_command,
    _verify_creation_command,
    _verify_evidence_command,
    _verify_lifecycle_command,
)

PaperAccountLedgerHistoryBundle: TypeAlias = (
    PaperAccountEventBundle | PaperAccountLedgerEventBundle
)


def _validate_quantity(
    value: object,
    field_name: str,
) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} is not canonical PaperQuantity"
        ) from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is not canonical PaperQuantity")
    return value


def _validate_position_entry(
    entry: object,
    *,
    event: PaperAccountEvent,
) -> PaperPositionLedgerEntry:
    if type(entry) is not PaperPositionLedgerEntry:
        raise ValueError("history contains an invalid position entry")
    if entry.account_id != event.account_id or entry.event_id != event.event_id:
        raise ValueError("position entry identity does not match its event")
    if type(entry.entry_index) is not int or entry.entry_index != 0:
        raise ValueError("position entry_index must be the exact integer zero")
    if (
        normalize_bounded_string(
            entry.position_entry_id,
            field_name="position_entry_id",
            maximum_length=512,
        )
        != entry.position_entry_id
    ):
        raise ValueError("position entry ID is not normalized")
    try:
        normalized_symbol = _normalize_position_symbol(entry.symbol)
    except ValueError as exc:
        raise ValueError("position entry symbol is invalid") from exc
    if normalized_symbol != entry.symbol:
        raise ValueError("position entry symbol is not normalized")
    if entry.adjustment_category not in (
        SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES
    ):
        raise ValueError("position entry category is invalid")
    _validate_quantity(entry.signed_quantity_delta, "signed_quantity_delta")
    _validate_money(entry.signed_cost_basis_delta, "signed_cost_basis_delta")
    if (
        entry.signed_quantity_delta.decimal_value == 0
        and entry.signed_cost_basis_delta.decimal_value == 0
    ):
        raise ValueError("position entry deltas must not both be zero")
    validate_digest(entry.entry_digest, "entry_digest")
    expected_payload = {
        "schema_version": PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION,
        "position_entry_id": entry.position_entry_id,
        "account_id": entry.account_id,
        "event_id": entry.event_id,
        "entry_index": entry.entry_index,
        "symbol": entry.symbol,
        "signed_quantity_delta": (
            entry.signed_quantity_delta.to_json_value()
        ),
        "signed_cost_basis_delta": (
            entry.signed_cost_basis_delta.to_json_value()
        ),
        "adjustment_category": entry.adjustment_category,
    }
    if canonical_digest(expected_payload) != entry.entry_digest:
        raise ValueError("position entry digest does not match its payload")
    return entry


def _verify_position_command(
    event: PaperAccountEvent,
) -> tuple[
    _PositionAdjustmentPostedDetails,
    PostPaperPositionAdjustmentCommand,
]:
    if type(event.details) is not _PositionAdjustmentPostedDetails:
        raise ValueError("position_adjustment_posted details are invalid")
    if event.reason is None or event.expected_account_version is None:
        raise ValueError("position adjustment event metadata is incomplete")
    details = event.details
    _validate_quantity(
        details.signed_quantity_delta,
        "signed_quantity_delta",
    )
    _validate_money(
        details.signed_cost_basis_delta,
        "signed_cost_basis_delta",
    )
    try:
        command = PostPaperPositionAdjustmentCommand(
            account_id=event.account_id,
            expected_account_version=event.expected_account_version,
            command_idempotency_key=event.command_idempotency_key,
            actor=event.actor,
            reason=event.reason,
            symbol=details.symbol,
            adjustment_category=details.adjustment_category,
            signed_quantity_delta=details.signed_quantity_delta,
            signed_cost_basis_delta=details.signed_cost_basis_delta,
            effective_timestamp_utc=event.effective_timestamp_utc,
        )
    except ValueError as exc:
        raise ValueError("position adjustment event meaning is invalid") from exc
    if command.symbol != details.symbol:
        raise ValueError("position adjustment event symbol is not normalized")
    if command.command_digest != event.command_digest:
        raise ValueError("position command digest does not match event meaning")
    return details, command


def _bundle_records(
    bundle: object,
) -> tuple[
    PaperAccountEvent,
    tuple[object, ...],
    tuple[object, ...],
    object,
]:
    if type(bundle) is PaperAccountEventBundle:
        return (
            bundle.event,
            bundle.cash_entries,
            (),
            bundle.resulting_state,
        )
    if type(bundle) is PaperAccountLedgerEventBundle:
        return (
            bundle.event,
            bundle.cash_entries,
            bundle.position_entries,
            bundle.resulting_state,
        )
    raise ValueError("history contains an invalid event bundle")


def replay_paper_account_ledger(
    bundles: Iterable[PaperAccountLedgerHistoryBundle],
) -> PaperAccountLedgerState:
    """Rebuild complete state from one immutable mixed event chain."""
    history = tuple(bundles)
    if not history:
        raise ValueError("paper account history must not be empty")

    account_identity: PaperAccountIdentity | None = None
    lifecycle_status = "active"
    cash_balance = PaperMoney.parse("0")
    positions: dict[str, PaperAccountPosition] = {}
    references: tuple[ApprovedPortfolioReviewReference, ...] = ()
    previous_chain_digest = PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST
    seen_event_ids: set[str] = set()
    seen_cash_entry_ids: set[str] = set()
    seen_position_entry_ids: set[str] = set()
    seen_decision_ids: set[str] = set()
    rebuilt_state: PaperAccountLedgerState | None = None

    for sequence_number, raw_bundle in enumerate(history, start=1):
        event, raw_cash_entries, raw_position_entries, supplied_state = (
            _bundle_records(raw_bundle)
        )
        _validate_event_header(
            event,
            sequence_number=sequence_number,
            account_id=(
                account_identity.account_id
                if account_identity is not None
                else None
            ),
            previous_chain_digest=previous_chain_digest,
        )
        if event.event_id in seen_event_ids:
            raise ValueError("event IDs must be unique")
        seen_event_ids.add(event.event_id)
        if lifecycle_status == "closed":
            raise ValueError("no event may follow a closed account")
        if type(raw_cash_entries) is not tuple:
            raise ValueError("cash entries must use immutable tuple ordering")
        if type(raw_position_entries) is not tuple:
            raise ValueError(
                "position entries must use immutable tuple ordering"
            )
        cash_entries = raw_cash_entries
        position_entries = raw_position_entries

        if sequence_number == 1:
            if event.event_type != "account_created":
                raise ValueError("the first event must be account_created")
            if len(cash_entries) != 1 or position_entries:
                raise ValueError(
                    "account creation requires one cash entry and no "
                    "position entries"
                )
            details = _verify_creation_command(event)
            account_identity = details.account_identity
            entry = cash_entries[0]
            _validate_entry(
                entry,  # type: ignore[arg-type]
                event=event,
                base_currency=account_identity.base_currency,
            )
            if (
                entry.movement_type != "initial_cash"
                or entry.signed_amount != details.initial_cash
                or entry.signed_amount.decimal_value < 0
            ):
                raise ValueError("initial cash entry meaning is invalid")
            cash_balance = details.initial_cash
        else:
            if event.event_type == "account_created":
                raise ValueError("account_created may appear only once")
            if account_identity is None:
                raise ValueError("account identity was not established")

            if event.event_type == "cash_movement_posted":
                if position_entries:
                    raise ValueError(
                        "cash events cannot contain position entries"
                    )
                if lifecycle_status != "active":
                    raise ValueError(
                        "cash movements require an active account"
                    )
                if len(cash_entries) != 1:
                    raise ValueError("cash movement requires one cash entry")
                details, command = _verify_cash_command(event)
                entry = cash_entries[0]
                _validate_entry(
                    entry,  # type: ignore[arg-type]
                    event=event,
                    base_currency=account_identity.base_currency,
                )
                expected_signed = _signed_cash_movement(command)
                if (
                    entry.movement_type != details.movement_type
                    or entry.signed_amount != expected_signed
                ):
                    raise ValueError("cash entry movement meaning is invalid")
                cash_balance = money_from_decimal(
                    _add_exact(
                        cash_balance.decimal_value,
                        entry.signed_amount.decimal_value,
                    )
                )
                if cash_balance.decimal_value < 0:
                    raise ValueError(
                        "cash became negative during ledger replay"
                    )
            elif event.event_type == "position_adjustment_posted":
                if cash_entries:
                    raise ValueError(
                        "position events cannot contain cash entries"
                    )
                if lifecycle_status != "active":
                    raise ValueError(
                        "position adjustments require an active account"
                    )
                if len(position_entries) != 1:
                    raise ValueError(
                        "position adjustment requires one position entry"
                    )
                details, command = _verify_position_command(event)
                entry = _validate_position_entry(
                    position_entries[0],
                    event=event,
                )
                if (
                    entry.symbol != details.symbol
                    or entry.adjustment_category
                    != details.adjustment_category
                    or entry.signed_quantity_delta
                    != details.signed_quantity_delta
                    or entry.signed_cost_basis_delta
                    != details.signed_cost_basis_delta
                    or command.symbol != entry.symbol
                ):
                    raise ValueError(
                        "position entry meaning does not match its event"
                    )
                prior = positions.get(entry.symbol)
                prior_quantity = (
                    prior.quantity.decimal_value
                    if prior is not None
                    else PaperQuantity.parse("0").decimal_value
                )
                prior_cost = (
                    prior.aggregate_cost_basis.decimal_value
                    if prior is not None
                    else PaperMoney.parse("0").decimal_value
                )
                quantity = quantity_from_decimal(
                    _add_exact(
                        prior_quantity,
                        entry.signed_quantity_delta.decimal_value,
                    )
                )
                cost = money_from_decimal(
                    _add_exact(
                        prior_cost,
                        entry.signed_cost_basis_delta.decimal_value,
                    )
                )
                if quantity.decimal_value < 0:
                    raise ValueError(
                        "position quantity became negative during replay"
                    )
                if cost.decimal_value < 0:
                    raise ValueError(
                        "aggregate cost basis became negative during replay"
                    )
                if (
                    quantity.decimal_value == 0
                    and cost.decimal_value != 0
                ):
                    raise ValueError(
                        "zero quantity has non-zero aggregate cost basis"
                    )
                if quantity.decimal_value == 0:
                    positions.pop(entry.symbol, None)
                else:
                    positions[entry.symbol] = _create_position(
                        symbol=entry.symbol,
                        quantity=quantity,
                        aggregate_cost_basis=cost,
                    )
            elif event.event_type == "portfolio_review_evidence_linked":
                if cash_entries or position_entries:
                    raise ValueError(
                        "evidence-link events cannot contain postings"
                    )
                if lifecycle_status != "active":
                    raise ValueError(
                        "evidence links require an active account"
                    )
                reference = _verify_evidence_command(event)
                if reference.decision_id in seen_decision_ids:
                    raise ValueError(
                        "evidence decision IDs must not be duplicated"
                    )
                seen_decision_ids.add(reference.decision_id)
                references = (*references, reference)
            else:
                if cash_entries or position_entries:
                    raise ValueError(
                        "lifecycle events cannot contain postings"
                    )
                target_status = _verify_lifecycle_command(
                    event,
                    lifecycle_status,
                )
                if target_status == "closed":
                    if cash_balance.decimal_value != 0:
                        raise ValueError(
                            "closed event requires zero replayed cash"
                        )
                    if positions:
                        raise ValueError(
                            "closed event requires no current positions"
                        )
                lifecycle_status = target_status

        for entry in cash_entries:
            cash_entry_id = entry.cash_entry_id
            if cash_entry_id in seen_cash_entry_ids:
                raise ValueError("cash entry IDs must be unique")
            seen_cash_entry_ids.add(cash_entry_id)
        for entry in position_entries:
            position_entry_id = entry.position_entry_id
            if position_entry_id in seen_position_entry_ids:
                raise ValueError("position entry IDs must be unique")
            seen_position_entry_ids.add(position_entry_id)

        if canonical_digest(
            _event_digest_payload(
                event,
                cash_entries,  # type: ignore[arg-type]
                position_entries,  # type: ignore[arg-type]
            )
        ) != event.event_digest:
            raise ValueError("event digest does not match event and postings")
        expected_chain = hashlib.sha256(
            (previous_chain_digest + event.event_digest).encode("ascii")
        ).hexdigest()
        if expected_chain != event.chain_digest:
            raise ValueError("event chain digest does not match")

        if account_identity is None:
            raise ValueError("account identity was not established")
        ordered_positions = tuple(
            positions[symbol] for symbol in sorted(positions)
        )
        rebuilt_state = _create_ledger_state(
            account_identity=account_identity,
            lifecycle_status=lifecycle_status,  # type: ignore[arg-type]
            cash_balance=cash_balance,
            positions=ordered_positions,
            approved_portfolio_reviews=references,
            head_version=sequence_number,
            head_event_id=event.event_id,
            head_chain_digest=event.chain_digest,
        )
        if type(raw_bundle) is PaperAccountEventBundle:
            try:
                _validate_state(supplied_state)
            except ValueError as exc:
                raise ValueError(
                    f"bundle resulting cash state is invalid: {exc}"
                ) from exc
            if supplied_state != rebuilt_state.to_cash_state():
                raise ValueError(
                    "bundle resulting cash state does not match records"
                )
        else:
            try:
                _validate_ledger_state(supplied_state)
            except ValueError as exc:
                raise ValueError(
                    f"bundle resulting ledger state is invalid: {exc}"
                ) from exc
            if supplied_state != rebuilt_state:
                raise ValueError(
                    "bundle resulting ledger state does not match records"
                )
        previous_chain_digest = event.chain_digest

    if rebuilt_state is None:
        raise ValueError("paper account history must not be empty")
    return rebuilt_state
