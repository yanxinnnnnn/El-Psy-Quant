"""Strict Paper Account row/domain mapping and history reconstruction."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from el_psy_quant.paper_account import (
    PAPER_ACCOUNT_EVENT_SCHEMA_VERSION,
    PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST,
    PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION,
    PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION,
    PAPER_ACCOUNT_RECONCILIATION_SCHEMA_VERSION,
    PAPER_ACCOUNT_SNAPSHOT_SCHEMA_VERSION,
    PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION,
    PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION,
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    CreatePaperAccountCommand,
    FreezePaperAccountCommand,
    PaperAccountCloseEligibility,
    PaperAccountIdentity,
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperAccountProjection,
    PaperAccountReconciliation,
    PaperAccountSnapshot,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    PostPaperPositionAdjustmentCommand,
    ReactivatePaperAccountCommand,
    apply_approved_portfolio_review_link,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_link_approved_portfolio_review_command,
    create_paper_account_event_bundle,
    replay_paper_account_ledger,
    validate_paper_account_lifecycle_transition,
)
from el_psy_quant.paper_account.cash_state import _signed_cash_movement
from el_psy_quant.paper_account.execution_settlement import (
    _apply_paper_execution_fill_settlement,
)
from el_psy_quant.paper_account.cash_ledger import _create_cash_ledger_entry
from el_psy_quant.paper_account.events import (
    _account_created_details,
    _cash_movement_details,
    _create_event,
    _evidence_linked_details,
    _execution_fill_posted_details,
    _lifecycle_changed_details,
    _position_adjustment_details,
)
from el_psy_quant.paper_account.ledger_state import (
    _create_ledger_bundle,
    _create_ledger_state,
    _create_position,
)
from el_psy_quant.paper_account.position_ledger import (
    _create_position_ledger_entry,
)
from el_psy_quant.paper_account.projection import (
    _create_position_projection,
    _create_projection,
    _validate_projection,
    _validate_reference,
)
from el_psy_quant.paper_account.reconciliation import (
    _validate_reconciliation,
)
from el_psy_quant.paper_account.snapshot import _validate_snapshot
from el_psy_quant.persistence.paper_account_model import (
    PaperAccountEventRow,
    PaperAccountPositionProjectionRow,
    PaperAccountProjectionRow,
    PaperAccountReconciliationRow,
    PaperAccountRow,
    PaperAccountSnapshotRow,
    PaperCashLedgerEntryRow,
    PaperPositionLedgerEntryRow,
)
from el_psy_quant.persistence.paper_accounts import (
    PaperAccountLedgerPageItem,
    PaperAccountPersistenceCorruptionError,
    PaperAccountRecord,
    _exact_string,
    _exact_utc,
    canonical_json,
    exact_dict,
    exact_list,
    load_canonical_json,
)


def _corruption(exc: Exception) -> PaperAccountPersistenceCorruptionError:
    return PaperAccountPersistenceCorruptionError()


def _int(value: object, field_name: str, *, positive: bool = False) -> int:
    if type(value) is not int or (positive and value <= 0):
        raise ValueError(f"{field_name} must be an exact integer")
    return value


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _int(value, field_name, positive=True)


def _identity_from_payload(payload: object) -> PaperAccountIdentity:
    root = exact_dict(
        payload,
        fields=(
            "schema_version",
            "account_id",
            "display_name",
            "base_currency",
            "created_by",
            "created_timestamp",
        ),
    )
    if _int(root["schema_version"], "identity schema version") != 1:
        raise ValueError("unsupported identity schema version")
    timestamp = root["created_timestamp"]
    if type(timestamp) is not str:
        raise ValueError("identity timestamp must be an ISO string")
    parsed = datetime.fromisoformat(timestamp)
    identity = PaperAccountIdentity(
        account_id=cast(str, root["account_id"]),
        display_name=cast(str, root["display_name"]),
        base_currency=cast(str, root["base_currency"]),
        created_by=cast(str, root["created_by"]),
        created_timestamp=parsed,
    )
    if identity.to_dict() != root:
        raise ValueError("identity payload is not canonical")
    return identity


def _reference_from_payload(
    payload: object,
) -> ApprovedPortfolioReviewReference:
    root = exact_dict(
        payload,
        fields=(
            "schema_version",
            "review_id",
            "source_id",
            "source_digest",
            "analysis_digest",
            "decision_id",
            "decision_digest",
            "outcome",
        ),
    )
    if _int(root["schema_version"], "reference schema version") != 1:
        raise ValueError("unsupported reference schema version")
    reference = object.__new__(ApprovedPortfolioReviewReference)
    for field_name in (
        "review_id",
        "source_id",
        "source_digest",
        "analysis_digest",
        "decision_id",
        "decision_digest",
        "outcome",
    ):
        object.__setattr__(reference, field_name, root[field_name])
    validated = _validate_reference(reference)
    if validated.to_dict() != root:
        raise ValueError("approved reference payload is not canonical")
    return validated


def account_record_from_row(row: PaperAccountRow) -> PaperAccountRecord:
    try:
        if _int(row.record_schema_version, "record_schema_version") != 1:
            raise ValueError("unsupported account row schema")
        identity = PaperAccountIdentity(
            account_id=row.account_id,
            display_name=row.display_name,
            base_currency=row.base_currency,
            created_by=row.created_by,
            created_timestamp=_exact_utc(
                row.created_timestamp, "created_timestamp"
            ),
        )
        return PaperAccountRecord(
            record_schema_version=1,
            account_identity=identity,
            lifecycle_status=cast(object, row.lifecycle_status),  # type: ignore[arg-type]
            head_version=_int(row.head_version, "head_version", positive=True),
            head_event_id=_exact_string(
                row.head_event_id, "head_event_id", 512
            ),
            head_chain_digest=row.head_chain_digest,
            projection_status=cast(object, row.projection_status),  # type: ignore[arg-type]
            updated_timestamp=_exact_utc(
                row.updated_timestamp, "updated_timestamp"
            ),
            closed_timestamp=(
                None
                if row.closed_timestamp is None
                else _exact_utc(row.closed_timestamp, "closed_timestamp")
            ),
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


def account_row_from_record(record: PaperAccountRecord) -> PaperAccountRow:
    if type(record) is not PaperAccountRecord:
        raise ValueError("record must be PaperAccountRecord")
    return PaperAccountRow(
        record_schema_version=record.record_schema_version,
        account_id=record.account_id,
        display_name=record.account_identity.display_name,
        base_currency=record.account_identity.base_currency,
        lifecycle_status=record.lifecycle_status,
        head_version=record.head_version,
        head_event_id=record.head_event_id,
        head_chain_digest=record.head_chain_digest,
        projection_status=record.projection_status,
        created_by=record.account_identity.created_by,
        created_timestamp=record.account_identity.created_timestamp,
        updated_timestamp=record.updated_timestamp,
        closed_timestamp=record.closed_timestamp,
    )


def _cash_from_row(row: PaperCashLedgerEntryRow):
    if _int(row.record_schema_version, "cash record schema") != 1:
        raise ValueError("unsupported cash row schema")
    if (
        _int(row.entry_schema_version, "cash entry schema")
        != PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION
    ):
        raise ValueError("unsupported cash entry schema")
    if _int(row.entry_index, "cash entry index") != 0:
        raise ValueError("cash entry index must be zero")
    entry = _create_cash_ledger_entry(
        cash_entry_id=row.cash_entry_id,
        account_id=row.account_id,
        event_id=row.event_id,
        movement_type=cast(object, row.movement_type),  # type: ignore[arg-type]
        currency=row.currency,
        signed_amount=PaperMoney.parse(row.signed_amount),
    )
    if entry.entry_digest != row.entry_digest:
        raise ValueError("cash entry digest mismatch")
    return entry


def _position_from_row(row: PaperPositionLedgerEntryRow):
    if _int(row.record_schema_version, "position record schema") != 1:
        raise ValueError("unsupported position row schema")
    if (
        _int(row.entry_schema_version, "position entry schema")
        != PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION
    ):
        raise ValueError("unsupported position entry schema")
    if _int(row.entry_index, "position entry index") != 0:
        raise ValueError("position entry index must be zero")
    entry = _create_position_ledger_entry(
        position_entry_id=row.position_entry_id,
        account_id=row.account_id,
        event_id=row.event_id,
        symbol=row.symbol,
        signed_quantity_delta=PaperQuantity.parse(
            row.signed_quantity_delta
        ),
        signed_cost_basis_delta=PaperMoney.parse(
            row.signed_cost_basis_delta
        ),
        adjustment_category=cast(  # type: ignore[arg-type]
            object, row.adjustment_category
        ),
    )
    if entry.entry_digest != row.entry_digest:
        raise ValueError("position entry digest mismatch")
    return entry


def _event_export(row: PaperAccountEventRow, details: dict[str, object]):
    return {
        "schema_version": row.event_schema_version,
        "event_id": row.event_id,
        "account_id": row.account_id,
        "sequence_number": row.sequence_number,
        "account_version": row.account_version,
        "event_type": row.event_type,
        "command_idempotency_key": row.command_idempotency_key,
        "command_digest": row.command_digest,
        "expected_account_version": row.expected_account_version,
        "actor": row.actor,
        "reason": row.reason,
        "recorded_timestamp_utc": _exact_utc(
            row.recorded_timestamp, "recorded_timestamp"
        ).isoformat(),
        "effective_timestamp_utc": (
            None
            if row.effective_timestamp is None
            else _exact_utc(
                row.effective_timestamp, "effective_timestamp"
            ).isoformat()
        ),
        "previous_chain_digest": row.previous_chain_digest,
        "details": details,
        "event_digest": row.event_digest,
        "chain_digest": row.chain_digest,
    }


def _full_state(
    *,
    cash_state,
    positions,
) -> PaperAccountLedgerState:
    return _create_ledger_state(
        account_identity=cash_state.account_identity,
        lifecycle_status=cash_state.lifecycle_status,
        cash_balance=cash_state.cash_balance,
        positions=positions,
        approved_portfolio_reviews=cash_state.approved_portfolio_reviews,
        head_version=cash_state.head_version,
        head_event_id=cash_state.head_event_id,
        head_chain_digest=cash_state.head_chain_digest,
    )


def _ledger_bundle_from_cash(bundle, positions):
    state = _full_state(
        cash_state=bundle.resulting_state,
        positions=positions,
    )
    return _create_ledger_bundle(
        event=bundle.event,
        cash_entries=bundle.cash_entries,
        position_entries=(),
        resulting_state=state,
    )


def reconstruct_history_page_items(
    *,
    account: PaperAccountRecord,
    event_rows: tuple[PaperAccountEventRow, ...],
    cash_rows: tuple[PaperCashLedgerEntryRow, ...],
    position_rows: tuple[PaperPositionLedgerEntryRow, ...],
    expected_first_sequence: int,
    previous_chain_digest: str,
) -> tuple[PaperAccountLedgerPageItem, ...]:
    """Validate one bounded page without replaying an unbounded prefix."""
    try:
        if type(expected_first_sequence) is not int or expected_first_sequence <= 0:
            raise ValueError("expected first sequence must be positive")
        cash_by_event: dict[str, list[PaperCashLedgerEntryRow]] = {}
        for row in cash_rows:
            cash_by_event.setdefault(row.event_id, []).append(row)
        positions_by_event: dict[str, list[PaperPositionLedgerEntryRow]] = {}
        for row in position_rows:
            positions_by_event.setdefault(row.event_id, []).append(row)

        result: list[PaperAccountLedgerPageItem] = []
        prior_chain = previous_chain_digest
        for expected_sequence, row in enumerate(
            event_rows,
            start=expected_first_sequence,
        ):
            if _int(row.record_schema_version, "event record schema") != 1:
                raise ValueError("unsupported event record schema")
            if (
                _int(row.event_schema_version, "event schema")
                != PAPER_ACCOUNT_EVENT_SCHEMA_VERSION
            ):
                raise ValueError("unsupported event schema")
            if (
                _int(row.sequence_number, "sequence_number", positive=True)
                != expected_sequence
                or _int(row.account_version, "account_version", positive=True)
                != expected_sequence
            ):
                raise ValueError("event page sequence is not contiguous")
            if row.account_id != account.account_id:
                raise ValueError("event belongs to a different account")
            if row.previous_chain_digest != prior_chain:
                raise ValueError("event page chain anchor is invalid")

            details_value = load_canonical_json(row.details_payload)
            if type(details_value) is not dict:
                raise ValueError("event details must be an object")
            details = cast(dict[str, object], details_value)
            recorded = _exact_utc(
                row.recorded_timestamp,
                "recorded_timestamp",
            )
            effective = (
                None
                if row.effective_timestamp is None
                else _exact_utc(
                    row.effective_timestamp,
                    "effective_timestamp",
                )
            )
            mapped_cash = tuple(
                _cash_from_row(item)
                for item in sorted(
                    cash_by_event.pop(row.event_id, []),
                    key=lambda item: item.entry_index,
                )
            )
            mapped_positions = tuple(
                _position_from_row(item)
                for item in sorted(
                    positions_by_event.pop(row.event_id, []),
                    key=lambda item: item.entry_index,
                )
            )

            if row.event_type == "account_created":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "account_identity",
                        "initial_cash",
                        "initial_lifecycle_status",
                    ),
                )
                identity = _identity_from_payload(root["account_identity"])
                initial_cash = PaperMoney.parse(cast(str, root["initial_cash"]))
                if (
                    expected_sequence != 1
                    or prior_chain != PAPER_ACCOUNT_GENESIS_CHAIN_DIGEST
                    or root["details_type"] != "account_created"
                    or root["initial_lifecycle_status"] != "active"
                    or row.reason is not None
                    or effective is not None
                    or row.expected_account_version is not None
                    or len(mapped_cash) != 1
                    or mapped_positions
                    or identity != account.account_identity
                    or mapped_cash[0].signed_amount != initial_cash
                ):
                    raise ValueError("creation event page shape is invalid")
                command = CreatePaperAccountCommand(
                    account_identity=identity,
                    initial_cash=initial_cash,
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                )
                event_details = _account_created_details(identity, initial_cash)
            elif row.event_type == "cash_movement_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "movement_type",
                        "requested_amount",
                    ),
                )
                requested_amount = PaperMoney.parse(
                    cast(str, root["requested_amount"])
                )
                command = PostPaperCashMovementCommand(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=cast(str, row.reason),
                    movement_type=cast(  # type: ignore[arg-type]
                        object,
                        root["movement_type"],
                    ),
                    requested_amount=requested_amount,
                    effective_timestamp_utc=effective,
                )
                if (
                    root["details_type"] != "cash_movement_posted"
                    or row.reason is None
                    or len(mapped_cash) != 1
                    or mapped_positions
                    or mapped_cash[0].signed_amount
                    != _signed_cash_movement(command)
                ):
                    raise ValueError("cash event page shape is invalid")
                event_details = _cash_movement_details(
                    command.movement_type,
                    command.requested_amount,
                )
            elif row.event_type == "position_adjustment_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "symbol",
                        "adjustment_category",
                        "signed_quantity_delta",
                        "signed_cost_basis_delta",
                    ),
                )
                command = PostPaperPositionAdjustmentCommand(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=cast(str, row.reason),
                    symbol=cast(str, root["symbol"]),
                    adjustment_category=cast(  # type: ignore[arg-type]
                        object,
                        root["adjustment_category"],
                    ),
                    signed_quantity_delta=PaperQuantity.parse(
                        cast(str, root["signed_quantity_delta"])
                    ),
                    signed_cost_basis_delta=PaperMoney.parse(
                        cast(str, root["signed_cost_basis_delta"])
                    ),
                    effective_timestamp_utc=effective,
                )
                if (
                    root["details_type"] != "position_adjustment_posted"
                    or row.reason is None
                    or mapped_cash
                    or len(mapped_positions) != 1
                    or mapped_positions[0].symbol != command.symbol
                    or mapped_positions[0].adjustment_category
                    != command.adjustment_category
                    or mapped_positions[0].signed_quantity_delta
                    != command.signed_quantity_delta
                    or mapped_positions[0].signed_cost_basis_delta
                    != command.signed_cost_basis_delta
                ):
                    raise ValueError("position event page shape is invalid")
                event_details = _position_adjustment_details(
                    symbol=command.symbol,
                    adjustment_category=command.adjustment_category,
                    signed_quantity_delta=command.signed_quantity_delta,
                    signed_cost_basis_delta=command.signed_cost_basis_delta,
                )
            elif row.event_type == "portfolio_review_evidence_linked":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "approved_portfolio_review",
                    ),
                )
                reference = _reference_from_payload(
                    root["approved_portfolio_review"]
                )
                command = create_link_approved_portfolio_review_command(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=cast(str, row.reason),
                    approved_portfolio_review=reference,
                )
                if (
                    root["details_type"]
                    != "portfolio_review_evidence_linked"
                    or row.reason is None
                    or effective is not None
                    or mapped_cash
                    or mapped_positions
                ):
                    raise ValueError("evidence event page shape is invalid")
                event_details = _evidence_linked_details(reference)
            elif row.event_type == "execution_fill_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "execution_order_id",
                        "execution_order_digest",
                        "execution_attempt_id",
                        "execution_attempt_digest",
                        "execution_fill_id",
                        "execution_fill_digest",
                        "instrument_id",
                        "side",
                        "fill_quantity",
                        "gross_notional",
                        "total_charges",
                        "signed_cash_delta",
                        "signed_position_quantity_delta",
                        "signed_position_cost_basis_delta",
                    ),
                )
                event_details = _execution_fill_posted_details(
                    execution_order_id=cast(str, root["execution_order_id"]),
                    execution_order_digest=cast(str, root["execution_order_digest"]),
                    execution_attempt_id=cast(str, root["execution_attempt_id"]),
                    execution_attempt_digest=cast(
                        str, root["execution_attempt_digest"]
                    ),
                    execution_fill_id=cast(str, root["execution_fill_id"]),
                    execution_fill_digest=cast(str, root["execution_fill_digest"]),
                    instrument_id=cast(str, root["instrument_id"]),
                    side=cast(str, root["side"]),
                    fill_quantity=PaperQuantity.parse(cast(str, root["fill_quantity"])),
                    gross_notional=PaperMoney.parse(cast(str, root["gross_notional"])),
                    total_charges=PaperMoney.parse(cast(str, root["total_charges"])),
                    signed_cash_delta=PaperMoney.parse(
                        cast(str, root["signed_cash_delta"])
                    ),
                    signed_position_quantity_delta=PaperQuantity.parse(
                        cast(str, root["signed_position_quantity_delta"])
                    ),
                    signed_position_cost_basis_delta=PaperMoney.parse(
                        cast(str, root["signed_position_cost_basis_delta"])
                    ),
                )
                if (
                    root["details_type"] != "execution_fill_posted"
                    or row.command_idempotency_key
                    != f"paper-execution-fill:{event_details.execution_fill_id}"
                    or row.actor != "paper_execution"
                    or row.reason is not None
                    or effective is None
                    or len(mapped_cash) != 1
                    or len(mapped_positions) != 1
                    or mapped_cash[0].movement_type != "execution_settlement"
                    or mapped_cash[0].currency != account.account_identity.base_currency
                    or mapped_cash[0].signed_amount != event_details.signed_cash_delta
                    or mapped_positions[0].symbol != event_details.instrument_id
                    or mapped_positions[0].adjustment_category != "execution_fill"
                    or mapped_positions[0].signed_quantity_delta
                    != event_details.signed_position_quantity_delta
                    or mapped_positions[0].signed_cost_basis_delta
                    != event_details.signed_position_cost_basis_delta
                ):
                    raise ValueError("execution settlement event page shape is invalid")
            else:
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "source_status",
                        "target_status",
                    ),
                )
                source_status = cast(str, root["source_status"])
                target_status = cast(str, root["target_status"])
                command_type: type[
                    FreezePaperAccountCommand
                    | ReactivatePaperAccountCommand
                    | ClosePaperAccountCommand
                ]
                if row.event_type == "account_frozen":
                    command_type = FreezePaperAccountCommand
                    expected_target = "frozen"
                elif row.event_type == "account_reactivated":
                    command_type = ReactivatePaperAccountCommand
                    expected_target = "active"
                elif row.event_type == "account_closed":
                    command_type = ClosePaperAccountCommand
                    expected_target = "closed"
                else:
                    raise ValueError("unsupported event type")
                if (
                    root["details_type"] != "lifecycle_changed"
                    or target_status != expected_target
                    or row.reason is None
                    or effective is not None
                    or mapped_cash
                    or mapped_positions
                ):
                    raise ValueError("lifecycle event page shape is invalid")
                validate_paper_account_lifecycle_transition(
                    source_status,
                    target_status,
                    close_eligibility=(
                        PaperAccountCloseEligibility(True, True, True)
                        if target_status == "closed"
                        else None
                    ),
                )
                command = command_type(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=row.reason,
                )
                event_details = _lifecycle_changed_details(
                    cast(object, source_status),  # type: ignore[arg-type]
                    cast(object, target_status),  # type: ignore[arg-type]
                )

            if (
                row.event_type != "execution_fill_posted"
                and command.command_digest != row.command_digest
            ):
                raise ValueError("event command digest is invalid")
            event = _create_event(
                event_id=row.event_id,
                account_id=row.account_id,
                sequence_number=row.sequence_number,
                event_type=cast(object, row.event_type),  # type: ignore[arg-type]
                command_idempotency_key=row.command_idempotency_key,
                command_digest=row.command_digest,
                expected_account_version=row.expected_account_version,
                actor=row.actor,
                reason=row.reason,
                recorded_timestamp_utc=recorded,
                effective_timestamp_utc=effective,
                previous_chain_digest=row.previous_chain_digest,
                details=event_details,
                cash_entries=mapped_cash,
                position_entries=mapped_positions,
            )
            if event.to_dict() != _event_export(row, details):
                raise ValueError("persisted event page does not match domain event")
            result.append(
                PaperAccountLedgerPageItem(
                    event=event,
                    cash_postings=mapped_cash,
                    position_postings=mapped_positions,
                )
            )
            prior_chain = event.chain_digest

        if cash_by_event or positions_by_event:
            raise ValueError("orphan page postings exist")
        return tuple(result)
    except PaperAccountPersistenceCorruptionError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


def reconstruct_history(
    *,
    account: PaperAccountRecord,
    event_rows: tuple[PaperAccountEventRow, ...],
    cash_rows: tuple[PaperCashLedgerEntryRow, ...],
    position_rows: tuple[PaperPositionLedgerEntryRow, ...],
) -> tuple[PaperAccountLedgerEventBundle, ...]:
    """Reapply every persisted event through pure domain operations."""
    try:
        if not event_rows:
            raise ValueError("account history is missing")
        cash_by_event: dict[str, list[PaperCashLedgerEntryRow]] = {}
        for row in cash_rows:
            cash_by_event.setdefault(row.event_id, []).append(row)
        positions_by_event: dict[str, list[PaperPositionLedgerEntryRow]] = {}
        for row in position_rows:
            positions_by_event.setdefault(row.event_id, []).append(row)

        history: list[PaperAccountLedgerEventBundle] = []
        state: PaperAccountLedgerState | None = None
        event_ids: set[str] = set()
        for expected_sequence, row in enumerate(event_rows, start=1):
            if _int(row.record_schema_version, "event record schema") != 1:
                raise ValueError("unsupported event record schema")
            if (
                _int(row.event_schema_version, "event schema")
                != PAPER_ACCOUNT_EVENT_SCHEMA_VERSION
            ):
                raise ValueError("unsupported event schema")
            if (
                _int(row.sequence_number, "sequence_number", positive=True)
                != expected_sequence
                or _int(row.account_version, "account_version", positive=True)
                != expected_sequence
            ):
                raise ValueError("event sequence is not contiguous")
            if row.event_id in event_ids:
                raise ValueError("duplicate event ID")
            event_ids.add(row.event_id)
            if row.account_id != account.account_id:
                raise ValueError("event belongs to a different account")
            details_value = load_canonical_json(row.details_payload)
            if type(details_value) is not dict:
                raise ValueError("event details must be an object")
            details = cast(dict[str, object], details_value)
            recorded = _exact_utc(
                row.recorded_timestamp, "recorded_timestamp"
            )
            effective = (
                None
                if row.effective_timestamp is None
                else _exact_utc(
                    row.effective_timestamp,
                    "effective_timestamp",
                )
            )
            cash_group = sorted(
                cash_by_event.pop(row.event_id, []),
                key=lambda item: item.entry_index,
            )
            position_group = sorted(
                positions_by_event.pop(row.event_id, []),
                key=lambda item: item.entry_index,
            )

            if row.event_type == "account_created":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "account_identity",
                        "initial_cash",
                        "initial_lifecycle_status",
                    ),
                )
                if (
                    root["details_type"] != "account_created"
                    or root["initial_lifecycle_status"] != "active"
                    or row.reason is not None
                    or effective is not None
                    or row.expected_account_version is not None
                    or state is not None
                    or len(cash_group) != 1
                    or position_group
                ):
                    raise ValueError("creation event shape is invalid")
                identity = _identity_from_payload(root["account_identity"])
                command = CreatePaperAccountCommand(
                    account_identity=identity,
                    initial_cash=PaperMoney.parse(
                        cast(str, root["initial_cash"])
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                )
                raw = create_paper_account_event_bundle(
                    command,
                    event_id=row.event_id,
                    cash_entry_id=cash_group[0].cash_entry_id,
                    recorded_timestamp_utc=recorded,
                )
                bundle = _ledger_bundle_from_cash(raw, ())
            elif state is None:
                raise ValueError("non-creation event appears first")
            elif row.event_type == "cash_movement_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "movement_type",
                        "requested_amount",
                    ),
                )
                if (
                    root["details_type"] != "cash_movement_posted"
                    or row.reason is None
                    or len(cash_group) != 1
                    or position_group
                ):
                    raise ValueError("cash event shape is invalid")
                command = PostPaperCashMovementCommand(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=row.reason,
                    movement_type=cast(  # type: ignore[arg-type]
                        object, root["movement_type"]
                    ),
                    requested_amount=PaperMoney.parse(
                        cast(str, root["requested_amount"])
                    ),
                    effective_timestamp_utc=effective,
                )
                raw = apply_paper_cash_movement(
                    state.to_cash_state(),
                    command,
                    event_id=row.event_id,
                    cash_entry_id=cash_group[0].cash_entry_id,
                    recorded_timestamp_utc=recorded,
                )
                bundle = _ledger_bundle_from_cash(raw, state.positions)
            elif row.event_type == "position_adjustment_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "symbol",
                        "adjustment_category",
                        "signed_quantity_delta",
                        "signed_cost_basis_delta",
                    ),
                )
                if (
                    root["details_type"] != "position_adjustment_posted"
                    or row.reason is None
                    or cash_group
                    or len(position_group) != 1
                ):
                    raise ValueError("position event shape is invalid")
                command = PostPaperPositionAdjustmentCommand(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=row.reason,
                    symbol=cast(str, root["symbol"]),
                    adjustment_category=cast(  # type: ignore[arg-type]
                        object, root["adjustment_category"]
                    ),
                    signed_quantity_delta=PaperQuantity.parse(
                        cast(str, root["signed_quantity_delta"])
                    ),
                    signed_cost_basis_delta=PaperMoney.parse(
                        cast(str, root["signed_cost_basis_delta"])
                    ),
                    effective_timestamp_utc=effective,
                )
                bundle = apply_paper_position_adjustment(
                    state,
                    command,
                    event_id=row.event_id,
                    position_entry_id=position_group[0].position_entry_id,
                    recorded_timestamp_utc=recorded,
                )
            elif row.event_type == "portfolio_review_evidence_linked":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "approved_portfolio_review",
                    ),
                )
                if (
                    root["details_type"]
                    != "portfolio_review_evidence_linked"
                    or row.reason is None
                    or effective is not None
                    or cash_group
                    or position_group
                ):
                    raise ValueError("evidence-link event shape is invalid")
                command = create_link_approved_portfolio_review_command(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=row.reason,
                    approved_portfolio_review=_reference_from_payload(
                        root["approved_portfolio_review"]
                    ),
                )
                raw = apply_approved_portfolio_review_link(
                    state.to_cash_state(),
                    command,
                    event_id=row.event_id,
                    recorded_timestamp_utc=recorded,
                )
                bundle = _ledger_bundle_from_cash(raw, state.positions)
            elif row.event_type == "execution_fill_posted":
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "execution_order_id",
                        "execution_order_digest",
                        "execution_attempt_id",
                        "execution_attempt_digest",
                        "execution_fill_id",
                        "execution_fill_digest",
                        "instrument_id",
                        "side",
                        "fill_quantity",
                        "gross_notional",
                        "total_charges",
                        "signed_cash_delta",
                        "signed_position_quantity_delta",
                        "signed_position_cost_basis_delta",
                    ),
                )
                if (
                    root["details_type"] != "execution_fill_posted"
                    or row.reason is not None
                    or effective is None
                    or len(cash_group) != 1
                    or len(position_group) != 1
                ):
                    raise ValueError("execution settlement event shape is invalid")
                bundle = _apply_paper_execution_fill_settlement(
                    state,
                    execution_order_id=cast(str, root["execution_order_id"]),
                    execution_order_digest=cast(str, root["execution_order_digest"]),
                    execution_attempt_id=cast(str, root["execution_attempt_id"]),
                    execution_attempt_digest=cast(
                        str, root["execution_attempt_digest"]
                    ),
                    execution_fill_id=cast(str, root["execution_fill_id"]),
                    execution_fill_digest=cast(str, root["execution_fill_digest"]),
                    instrument_id=cast(str, root["instrument_id"]),
                    side=cast(str, root["side"]),
                    fill_quantity=PaperQuantity.parse(cast(str, root["fill_quantity"])),
                    gross_notional=PaperMoney.parse(cast(str, root["gross_notional"])),
                    total_charges=PaperMoney.parse(cast(str, root["total_charges"])),
                    effective_timestamp_utc=effective,
                    recorded_timestamp_utc=recorded,
                )
            else:
                root = exact_dict(
                    details,
                    fields=(
                        "details_type",
                        "source_status",
                        "target_status",
                    ),
                )
                command_type: type[
                    FreezePaperAccountCommand
                    | ReactivatePaperAccountCommand
                    | ClosePaperAccountCommand
                ]
                if row.event_type == "account_frozen":
                    command_type = FreezePaperAccountCommand
                    expected_target = "frozen"
                elif row.event_type == "account_reactivated":
                    command_type = ReactivatePaperAccountCommand
                    expected_target = "active"
                elif row.event_type == "account_closed":
                    command_type = ClosePaperAccountCommand
                    expected_target = "closed"
                else:
                    raise ValueError("unsupported event type")
                if (
                    root["details_type"] != "lifecycle_changed"
                    or root["source_status"] != state.lifecycle_status
                    or root["target_status"] != expected_target
                    or row.reason is None
                    or effective is not None
                    or cash_group
                    or position_group
                ):
                    raise ValueError("lifecycle event shape is invalid")
                command = command_type(
                    account_id=row.account_id,
                    expected_account_version=cast(
                        int,
                        _optional_int(
                            row.expected_account_version,
                            "expected_account_version",
                        ),
                    ),
                    command_idempotency_key=row.command_idempotency_key,
                    actor=row.actor,
                    reason=row.reason,
                )
                close_eligibility = (
                    PaperAccountCloseEligibility(
                        cash_is_zero=state.cash_balance.decimal_value == 0,
                        position_quantities_are_zero=not state.positions,
                        aggregate_cost_bases_are_zero=not state.positions,
                    )
                    if row.event_type == "account_closed"
                    else None
                )
                raw = apply_paper_account_lifecycle_command(
                    state.to_cash_state(),
                    command,
                    event_id=row.event_id,
                    recorded_timestamp_utc=recorded,
                    close_eligibility=close_eligibility,
                )
                bundle = _ledger_bundle_from_cash(raw, state.positions)

            computed_cash = bundle.cash_entries
            computed_positions = bundle.position_entries
            mapped_cash = tuple(_cash_from_row(item) for item in cash_group)
            mapped_positions = tuple(
                _position_from_row(item) for item in position_group
            )
            if computed_cash != mapped_cash or computed_positions != mapped_positions:
                raise ValueError("persisted postings do not match event meaning")
            if bundle.event.to_dict() != _event_export(row, details):
                raise ValueError("persisted event does not match domain event")
            history.append(bundle)
            state = bundle.resulting_state

        if cash_by_event or positions_by_event:
            raise ValueError("orphan account postings exist")
        replayed = replay_paper_account_ledger(history)
        if (
            replayed.account_identity != account.account_identity
            or replayed.lifecycle_status != account.lifecycle_status
            or replayed.head_version != account.head_version
            or replayed.head_event_id != account.head_event_id
            or replayed.head_chain_digest != account.head_chain_digest
        ):
            raise ValueError("account head differs from immutable ledger replay")
        return tuple(history)
    except PaperAccountPersistenceCorruptionError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


def _projection_from_payload(payload: object) -> PaperAccountProjection:
    root = exact_dict(
        payload,
        fields=(
            "schema_version",
            "account_identity",
            "lifecycle_status",
            "cash_balance",
            "available_cash",
            "positions",
            "approved_portfolio_reviews",
            "source_account_version",
            "source_event_id",
            "source_chain_digest",
            "projection_digest",
        ),
    )
    if (
        _int(root["schema_version"], "projection schema")
        != PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION
    ):
        raise ValueError("unsupported projection schema")
    positions = []
    for item in exact_list(root["positions"]):
        position = exact_dict(
            item,
            fields=(
                "schema_version",
                "symbol",
                "quantity",
                "aggregate_cost_basis",
                "average_unit_cost",
                "average_unit_cost_is_rounded",
            ),
        )
        if (
            _int(position["schema_version"], "position projection schema")
            != PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION
        ):
            raise ValueError("unsupported position projection schema")
        domain_position = _create_position(
            symbol=cast(str, position["symbol"]),
            quantity=PaperQuantity.parse(cast(str, position["quantity"])),
            aggregate_cost_basis=PaperMoney.parse(
                cast(str, position["aggregate_cost_basis"])
            ),
        )
        projected = _create_position_projection(domain_position)
        if projected.to_dict() != position:
            raise ValueError("position projection is inconsistent")
        positions.append(projected)
    references = tuple(
        _reference_from_payload(item)
        for item in exact_list(root["approved_portfolio_reviews"])
    )
    projection = _create_projection(
        account_identity=_identity_from_payload(root["account_identity"]),
        lifecycle_status=cast(object, root["lifecycle_status"]),  # type: ignore[arg-type]
        cash_balance=PaperMoney.parse(cast(str, root["cash_balance"])),
        available_cash=PaperMoney.parse(cast(str, root["available_cash"])),
        positions=tuple(positions),
        approved_portfolio_reviews=references,
        source_account_version=_int(
            root["source_account_version"],
            "source_account_version",
            positive=True,
        ),
        source_event_id=cast(str, root["source_event_id"]),
        source_chain_digest=cast(str, root["source_chain_digest"]),
    )
    if projection.projection_digest != root["projection_digest"]:
        raise ValueError("projection digest mismatch")
    return projection


def projection_from_rows(
    *,
    account: PaperAccountRecord,
    row: PaperAccountProjectionRow,
    position_rows: tuple[PaperAccountPositionProjectionRow, ...],
) -> PaperAccountProjection:
    try:
        if (
            _int(row.record_schema_version, "projection record schema") != 1
            or _int(row.projection_schema_version, "projection schema")
            != PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION
        ):
            raise ValueError("unsupported projection row schema")
        _exact_utc(row.updated_timestamp, "projection updated timestamp")
        references = load_canonical_json(
            row.approved_portfolio_reviews_payload
        )
        payload = {
            "schema_version": row.projection_schema_version,
            "account_identity": account.account_identity.to_dict(),
            "lifecycle_status": row.lifecycle_status,
            "cash_balance": row.cash_balance,
            "available_cash": row.available_cash,
            "positions": [],
            "approved_portfolio_reviews": references,
            "source_account_version": row.source_account_version,
            "source_event_id": row.source_event_id,
            "source_chain_digest": row.source_chain_digest,
            "projection_digest": row.projection_digest,
        }
        prior_symbol: str | None = None
        for position_row in position_rows:
            if (
                _int(
                    position_row.record_schema_version,
                    "position projection record schema",
                )
                != 1
                or _int(
                    position_row.position_projection_schema_version,
                    "position projection schema",
                )
                != PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION
                or position_row.account_id != account.account_id
                or type(position_row.average_unit_cost_is_rounded) is not bool
                or (
                    prior_symbol is not None
                    and position_row.symbol <= prior_symbol
                )
            ):
                raise ValueError("position projection row is invalid")
            prior_symbol = position_row.symbol
            cast(list[object], payload["positions"]).append(
                {
                    "schema_version": (
                        position_row.position_projection_schema_version
                    ),
                    "symbol": position_row.symbol,
                    "quantity": position_row.quantity,
                    "aggregate_cost_basis": position_row.aggregate_cost_basis,
                    "average_unit_cost": position_row.average_unit_cost,
                    "average_unit_cost_is_rounded": (
                        position_row.average_unit_cost_is_rounded
                    ),
                }
            )
        projection = _projection_from_payload(payload)
        if row.account_id != account.account_id:
            raise ValueError("projection belongs to another account")
        return projection
    except PaperAccountPersistenceCorruptionError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


def projection_rows(
    projection: PaperAccountProjection,
    *,
    updated_timestamp: datetime,
) -> tuple[
    PaperAccountProjectionRow,
    tuple[PaperAccountPositionProjectionRow, ...],
]:
    _validate_projection(projection)
    updated = _exact_utc(updated_timestamp, "updated_timestamp")
    parent = PaperAccountProjectionRow(
        record_schema_version=1,
        projection_schema_version=PAPER_ACCOUNT_PROJECTION_SCHEMA_VERSION,
        account_id=projection.account_id,
        lifecycle_status=projection.lifecycle_status,
        cash_balance=projection.cash_balance.canonical,
        available_cash=projection.available_cash.canonical,
        approved_portfolio_reviews_payload=canonical_json(
            [
                reference.to_dict()
                for reference in projection.approved_portfolio_reviews
            ]
        ),
        source_account_version=projection.source_account_version,
        source_event_id=projection.source_event_id,
        source_chain_digest=projection.source_chain_digest,
        projection_digest=projection.projection_digest,
        updated_timestamp=updated,
    )
    children = tuple(
        PaperAccountPositionProjectionRow(
            record_schema_version=1,
            position_projection_schema_version=(
                PAPER_ACCOUNT_POSITION_PROJECTION_SCHEMA_VERSION
            ),
            account_id=projection.account_id,
            symbol=position.symbol,
            quantity=position.quantity.canonical,
            aggregate_cost_basis=position.aggregate_cost_basis.canonical,
            average_unit_cost=position.average_unit_cost,
            average_unit_cost_is_rounded=(
                position.average_unit_cost_is_rounded
            ),
        )
        for position in projection.positions
    )
    return parent, children


def event_row(bundle: PaperAccountLedgerEventBundle) -> PaperAccountEventRow:
    event = bundle.event
    return PaperAccountEventRow(
        record_schema_version=1,
        event_schema_version=PAPER_ACCOUNT_EVENT_SCHEMA_VERSION,
        event_id=event.event_id,
        account_id=event.account_id,
        sequence_number=event.sequence_number,
        account_version=event.account_version,
        event_type=event.event_type,
        command_idempotency_key=event.command_idempotency_key,
        command_digest=event.command_digest,
        expected_account_version=event.expected_account_version,
        actor=event.actor,
        reason=event.reason,
        effective_timestamp=event.effective_timestamp_utc,
        recorded_timestamp=event.recorded_timestamp_utc,
        details_payload=canonical_json(event.details.to_dict()),
        previous_chain_digest=event.previous_chain_digest,
        event_digest=event.event_digest,
        chain_digest=event.chain_digest,
    )


def cash_rows(
    bundle: PaperAccountLedgerEventBundle,
) -> tuple[PaperCashLedgerEntryRow, ...]:
    return tuple(
        PaperCashLedgerEntryRow(
            record_schema_version=1,
            entry_schema_version=PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION,
            cash_entry_id=entry.cash_entry_id,
            account_id=entry.account_id,
            event_id=entry.event_id,
            entry_index=entry.entry_index,
            movement_type=entry.movement_type,
            currency=entry.currency,
            signed_amount=entry.signed_amount.canonical,
            entry_digest=entry.entry_digest,
        )
        for entry in bundle.cash_entries
    )


def position_rows(
    bundle: PaperAccountLedgerEventBundle,
) -> tuple[PaperPositionLedgerEntryRow, ...]:
    return tuple(
        PaperPositionLedgerEntryRow(
            record_schema_version=1,
            entry_schema_version=PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION,
            position_entry_id=entry.position_entry_id,
            account_id=entry.account_id,
            event_id=entry.event_id,
            entry_index=entry.entry_index,
            symbol=entry.symbol,
            signed_quantity_delta=entry.signed_quantity_delta.canonical,
            signed_cost_basis_delta=entry.signed_cost_basis_delta.canonical,
            adjustment_category=entry.adjustment_category,
            entry_digest=entry.entry_digest,
        )
        for entry in bundle.position_entries
    )


def snapshot_row(snapshot: PaperAccountSnapshot) -> PaperAccountSnapshotRow:
    _validate_snapshot(snapshot)
    return PaperAccountSnapshotRow(
        record_schema_version=1,
        snapshot_schema_version=PAPER_ACCOUNT_SNAPSHOT_SCHEMA_VERSION,
        snapshot_id=snapshot.snapshot_id,
        account_id=snapshot.account_id,
        account_version=snapshot.account_version,
        head_event_id=snapshot.head_event_id,
        head_chain_digest=snapshot.head_chain_digest,
        operation_idempotency_key=snapshot.operation_idempotency_key,
        operation_command_digest=snapshot.operation_command_digest,
        created_by=snapshot.created_by,
        recorded_timestamp=snapshot.recorded_timestamp_utc,
        reason=snapshot.reason,
        projection_payload=canonical_json(snapshot.projection.to_dict()),
        projection_digest=snapshot.projection.projection_digest,
        snapshot_digest=snapshot.snapshot_digest,
    )


def snapshot_from_row(row: PaperAccountSnapshotRow) -> PaperAccountSnapshot:
    try:
        if (
            _int(row.record_schema_version, "snapshot record schema") != 1
            or _int(row.snapshot_schema_version, "snapshot schema")
            != PAPER_ACCOUNT_SNAPSHOT_SCHEMA_VERSION
        ):
            raise ValueError("unsupported snapshot row schema")
        projection = _projection_from_payload(
            load_canonical_json(row.projection_payload)
        )
        if projection.projection_digest != row.projection_digest:
            raise ValueError("snapshot projection digest mismatch")
        snapshot = object.__new__(PaperAccountSnapshot)
        values = {
            "snapshot_id": row.snapshot_id,
            "account_id": row.account_id,
            "account_version": row.account_version,
            "head_event_id": row.head_event_id,
            "head_chain_digest": row.head_chain_digest,
            "operation_idempotency_key": row.operation_idempotency_key,
            "operation_command_digest": row.operation_command_digest,
            "created_by": row.created_by,
            "recorded_timestamp_utc": _exact_utc(
                row.recorded_timestamp, "recorded_timestamp"
            ),
            "reason": row.reason,
            "projection": projection,
            "snapshot_digest": row.snapshot_digest,
        }
        for field_name, value in values.items():
            object.__setattr__(snapshot, field_name, value)
        return _validate_snapshot(snapshot)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


def reconciliation_row(
    reconciliation: PaperAccountReconciliation,
) -> PaperAccountReconciliationRow:
    _validate_reconciliation(reconciliation)
    return PaperAccountReconciliationRow(
        record_schema_version=1,
        reconciliation_schema_version=(
            PAPER_ACCOUNT_RECONCILIATION_SCHEMA_VERSION
        ),
        reconciliation_id=reconciliation.reconciliation_id,
        account_id=reconciliation.account_id,
        operation_idempotency_key=(
            reconciliation.operation_idempotency_key
        ),
        operation_command_digest=reconciliation.operation_command_digest,
        created_by=reconciliation.created_by,
        recorded_timestamp=reconciliation.recorded_timestamp_utc,
        reason=reconciliation.reason,
        outcome=reconciliation.outcome,
        mismatch_codes_payload=canonical_json(
            list(reconciliation.mismatch_codes)
        ),
        authoritative_account_version=(
            reconciliation.authoritative_account_version
        ),
        authoritative_event_id=reconciliation.authoritative_event_id,
        authoritative_chain_digest=reconciliation.authoritative_chain_digest,
        authoritative_projection_digest=(
            reconciliation.authoritative_projection_digest
        ),
        candidate_account_version=reconciliation.candidate_account_version,
        candidate_event_id=reconciliation.candidate_event_id,
        candidate_chain_digest=reconciliation.candidate_chain_digest,
        candidate_projection_digest=reconciliation.candidate_projection_digest,
        reconciliation_digest=reconciliation.reconciliation_digest,
    )


def reconciliation_from_row(
    row: PaperAccountReconciliationRow,
) -> PaperAccountReconciliation:
    try:
        if (
            _int(row.record_schema_version, "reconciliation record schema") != 1
            or _int(row.reconciliation_schema_version, "reconciliation schema")
            != PAPER_ACCOUNT_RECONCILIATION_SCHEMA_VERSION
        ):
            raise ValueError("unsupported reconciliation row schema")
        codes = exact_list(load_canonical_json(row.mismatch_codes_payload))
        reconciliation = object.__new__(PaperAccountReconciliation)
        values = {
            "reconciliation_id": row.reconciliation_id,
            "account_id": row.account_id,
            "operation_idempotency_key": row.operation_idempotency_key,
            "operation_command_digest": row.operation_command_digest,
            "created_by": row.created_by,
            "recorded_timestamp_utc": _exact_utc(
                row.recorded_timestamp, "recorded_timestamp"
            ),
            "reason": row.reason,
            "outcome": row.outcome,
            "mismatch_codes": tuple(codes),
            "authoritative_account_version": (
                row.authoritative_account_version
            ),
            "authoritative_event_id": row.authoritative_event_id,
            "authoritative_chain_digest": row.authoritative_chain_digest,
            "authoritative_projection_digest": (
                row.authoritative_projection_digest
            ),
            "candidate_account_version": row.candidate_account_version,
            "candidate_event_id": row.candidate_event_id,
            "candidate_chain_digest": row.candidate_chain_digest,
            "candidate_projection_digest": row.candidate_projection_digest,
            "reconciliation_digest": row.reconciliation_digest,
        }
        for field_name, value in values.items():
            object.__setattr__(reconciliation, field_name, value)
        return _validate_reconciliation(reconciliation)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _corruption(exc) from exc


__all__ = [
    "account_record_from_row",
    "account_row_from_record",
    "cash_rows",
    "event_row",
    "position_rows",
    "projection_from_rows",
    "projection_rows",
    "reconciliation_from_row",
    "reconciliation_row",
    "reconstruct_history",
    "snapshot_from_row",
    "snapshot_row",
]
