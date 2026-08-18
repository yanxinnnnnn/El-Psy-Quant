"""Pure S210 Fill-to-M31 settlement and reconciliation evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.paper_account import (
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperQuantity,
    apply_paper_execution_fill_settlement,
    validate_paper_account_ledger_state,
    validate_paper_execution_fill_settlement_bundle,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.attempts import (
    PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
    PaperExecutionAttempt,
    PaperExecutionAttemptReference,
    _clone_attempt_reference,
    create_paper_execution_attempt_reference,
    validate_paper_execution_attempt,
    validate_paper_execution_attempt_reference,
)
from el_psy_quant.paper_execution.fills import (
    PaperExecutionFill,
    PaperExecutionFillReference,
    create_paper_execution_fill_reference,
    validate_paper_execution_fill,
    validate_paper_execution_fill_reference,
)
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrder,
    PaperExecutionOrderReference,
    _clone_order_reference,
    create_paper_execution_order_reference,
    validate_paper_execution_order,
    validate_paper_execution_order_reference,
)

EXECUTION_SETTLEMENT_LINK_SCHEMA_VERSION = 1
PAPER_EXECUTION_SETTLEMENT_RESULT_SCHEMA_VERSION = 1


@dataclass(frozen=True, init=False)
class ExecutionSettlementLink:
    """One-to-one reconciliation evidence; never financial authority."""

    schema_version: int
    settlement_link_id: str
    settlement_link_digest: str
    execution_order_reference: PaperExecutionOrderReference
    execution_attempt_reference: PaperExecutionAttemptReference
    execution_fill_reference: PaperExecutionFillReference
    account_id: str
    account_event_id: str
    account_event_digest: str
    account_chain_digest: str
    account_version: int
    cash_entry_id: str
    cash_entry_digest: str
    position_entry_id: str
    position_entry_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "settlement_link_id": self.settlement_link_id,
            "settlement_link_digest": self.settlement_link_digest,
            "execution_order_reference": (self.execution_order_reference.to_dict()),
            "execution_attempt_reference": (self.execution_attempt_reference.to_dict()),
            "execution_fill_reference": self.execution_fill_reference.to_dict(),
            "account_id": self.account_id,
            "account_event_id": self.account_event_id,
            "account_event_digest": self.account_event_digest,
            "account_chain_digest": self.account_chain_digest,
            "account_version": self.account_version,
            "cash_entry_id": self.cash_entry_id,
            "cash_entry_digest": self.cash_entry_digest,
            "position_entry_id": self.position_entry_id,
            "position_entry_digest": self.position_entry_digest,
        }


def _clone_fill_reference(
    value: PaperExecutionFillReference,
) -> PaperExecutionFillReference:
    valid = validate_paper_execution_fill_reference(value)
    result = object.__new__(PaperExecutionFillReference)
    object.__setattr__(result, "schema_version", valid.schema_version)
    object.__setattr__(result, "fill_id", valid.fill_id)
    object.__setattr__(result, "fill_digest", valid.fill_digest)
    return result


def _link_identity_payload(
    *,
    order_reference: PaperExecutionOrderReference,
    attempt_reference: PaperExecutionAttemptReference,
    fill_reference: PaperExecutionFillReference,
    account_id: str,
    account_event_id: str,
    account_version: int,
    cash_entry_id: str,
    cash_entry_digest: str,
    position_entry_id: str,
    position_entry_digest: str,
) -> dict[str, object]:
    # M31 event/chain digests include recorded audit time. They remain bound
    # on the link and are reconciled below, but are intentionally excluded
    # from the stable one-to-one identity.
    return {
        "schema_version": EXECUTION_SETTLEMENT_LINK_SCHEMA_VERSION,
        "execution_order_reference": order_reference.to_dict(),
        "execution_attempt_reference": attempt_reference.to_dict(),
        "execution_fill_reference": fill_reference.to_dict(),
        "account_id": account_id,
        "account_event_id": account_event_id,
        "account_version": account_version,
        "cash_entry_id": cash_entry_id,
        "cash_entry_digest": cash_entry_digest,
        "position_entry_id": position_entry_id,
        "position_entry_digest": position_entry_digest,
    }


def _create_link(
    *,
    order_reference: PaperExecutionOrderReference,
    attempt_reference: PaperExecutionAttemptReference,
    fill_reference: PaperExecutionFillReference,
    bundle: PaperAccountLedgerEventBundle,
) -> ExecutionSettlementLink:
    if (
        type(bundle) is not PaperAccountLedgerEventBundle
        or bundle.event.event_type != "execution_fill_posted"
        or len(bundle.cash_entries) != 1
        or len(bundle.position_entries) != 1
    ):
        raise ValueError("settlement link requires one exact M31 execution event")
    order_ref = _clone_order_reference(order_reference)
    attempt_ref = _clone_attempt_reference(attempt_reference)
    fill_ref = _clone_fill_reference(fill_reference)
    event = bundle.event
    cash = bundle.cash_entries[0]
    position = bundle.position_entries[0]
    payload = _link_identity_payload(
        order_reference=order_ref,
        attempt_reference=attempt_ref,
        fill_reference=fill_ref,
        account_id=event.account_id,
        account_event_id=event.event_id,
        account_version=event.account_version,
        cash_entry_id=cash.cash_entry_id,
        cash_entry_digest=cash.entry_digest,
        position_entry_id=position.position_entry_id,
        position_entry_digest=position.entry_digest,
    )
    digest = canonical_digest(payload)
    result = object.__new__(ExecutionSettlementLink)
    values = {
        "schema_version": EXECUTION_SETTLEMENT_LINK_SCHEMA_VERSION,
        "settlement_link_id": f"pes_{digest}",
        "settlement_link_digest": digest,
        "execution_order_reference": order_ref,
        "execution_attempt_reference": attempt_ref,
        "execution_fill_reference": fill_ref,
        "account_id": event.account_id,
        "account_event_id": event.event_id,
        "account_event_digest": event.event_digest,
        "account_chain_digest": event.chain_digest,
        "account_version": event.account_version,
        "cash_entry_id": cash.cash_entry_id,
        "cash_entry_digest": cash.entry_digest,
        "position_entry_id": position.position_entry_id,
        "position_entry_digest": position.entry_digest,
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def validate_execution_settlement_link(
    value: object,
) -> ExecutionSettlementLink:
    if type(value) is not ExecutionSettlementLink:
        raise ValueError("settlement link must be ExecutionSettlementLink")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != EXECUTION_SETTLEMENT_LINK_SCHEMA_VERSION
            or type(value.account_version) is not int
            or value.account_version < 2
        ):
            raise ValueError("settlement link metadata is invalid")
        order_ref = validate_paper_execution_order_reference(
            value.execution_order_reference
        )
        attempt_ref = validate_paper_execution_attempt_reference(
            value.execution_attempt_reference
        )
        fill_ref = validate_paper_execution_fill_reference(
            value.execution_fill_reference
        )
        for field_name in (
            "account_event_digest",
            "account_chain_digest",
            "cash_entry_digest",
            "position_entry_digest",
            "settlement_link_digest",
        ):
            validate_digest(getattr(value, field_name), field_name=field_name)
        for field_name in (
            "account_id",
            "account_event_id",
            "cash_entry_id",
            "position_entry_id",
        ):
            item = getattr(value, field_name)
            if not isinstance(item, str) or not item or item != item.strip():
                raise ValueError(f"{field_name} is invalid")
        payload = _link_identity_payload(
            order_reference=order_ref,
            attempt_reference=attempt_ref,
            fill_reference=fill_ref,
            account_id=value.account_id,
            account_event_id=value.account_event_id,
            account_version=value.account_version,
            cash_entry_id=value.cash_entry_id,
            cash_entry_digest=value.cash_entry_digest,
            position_entry_id=value.position_entry_id,
            position_entry_digest=value.position_entry_digest,
        )
        digest = canonical_digest(payload)
        if (
            digest != value.settlement_link_digest
            or value.settlement_link_id != f"pes_{digest}"
        ):
            raise ValueError("settlement link identity is invalid")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("execution settlement link is invalid") from exc
    return value


@dataclass(frozen=True, init=False)
class PaperExecutionSettlementResult:
    """One pure M31 event bundle and its M34 reconciliation link."""

    schema_version: int
    ledger_bundle: PaperAccountLedgerEventBundle
    settlement_link: ExecutionSettlementLink

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ledger_bundle": self.ledger_bundle.to_dict(),
            "settlement_link": self.settlement_link.to_dict(),
        }


def _current_quantity(
    state: PaperAccountLedgerState,
    instrument_id: str,
) -> PaperQuantity:
    return next(
        (
            position.quantity
            for position in state.positions
            if position.symbol == instrument_id
        ),
        PaperQuantity.parse("0"),
    )


def _preflight(
    *,
    order: PaperExecutionOrder,
    attempt: PaperExecutionAttempt,
    fill: PaperExecutionFill,
    account_state: PaperAccountLedgerState,
) -> tuple[
    PaperExecutionOrder,
    PaperExecutionAttempt,
    PaperExecutionFill,
    PaperAccountLedgerState,
    PaperExecutionOrderReference,
    PaperExecutionAttemptReference,
    PaperExecutionFillReference,
]:
    valid_order = validate_paper_execution_order(order)
    valid_attempt = validate_paper_execution_attempt(attempt)
    valid_fill = validate_paper_execution_fill(fill)
    state = validate_paper_account_ledger_state(account_state)
    order_ref = create_paper_execution_order_reference(valid_order)
    attempt_ref = create_paper_execution_attempt_reference(valid_attempt)
    fill_ref = create_paper_execution_fill_reference(valid_fill)
    risk = valid_attempt.risk_revalidation
    if not (
        valid_attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL
        and risk is not None
        and risk.outcome == "allow"
        and valid_attempt.consumed_event_reference is not None
        and valid_attempt.execution_order_reference == order_ref
        and valid_fill.execution_order_reference == order_ref
        and valid_fill.attempt_reference == attempt_ref
        and valid_fill.execution_event_reference
        == valid_attempt.consumed_event_reference
        and valid_fill.execution_price_evidence == risk.execution_price_evidence
        and valid_fill.cost_evidence == risk.cost_evidence
        and valid_fill.fill_quantity == risk.candidate_fill_quantity
        and valid_fill.side == valid_order.side
        and valid_fill.execution_event_reference.instrument_id
        == valid_order.instrument_id
    ):
        raise ValueError("Fill, Attempt, and Order authority is incompatible")
    if not (
        state.lifecycle_status == "active"
        and state.account_identity.account_id == valid_order.account_id
        and state.account_identity.base_currency
        == valid_order.account_handoff_reference.base_currency
        and risk.account_id == state.account_identity.account_id
        and risk.account_head_version == state.head_version
        and risk.account_head_event_id == state.head_event_id
        and risk.account_head_chain_digest == state.head_chain_digest
        and risk.available_cash == state.available_cash
        and risk.current_instrument_quantity
        == _current_quantity(state, valid_order.instrument_id)
    ):
        raise ValueError("M31 settlement authority is stale or incompatible")
    return (
        valid_order,
        valid_attempt,
        valid_fill,
        state,
        order_ref,
        attempt_ref,
        fill_ref,
    )


def settle_paper_execution_fill(
    *,
    order: PaperExecutionOrder,
    attempt: PaperExecutionAttempt,
    fill: PaperExecutionFill,
    account_state: PaperAccountLedgerState,
    recorded_timestamp_utc: datetime,
) -> PaperExecutionSettlementResult:
    """Settle one compatible Fill through M31 event/posting authority."""
    (
        valid_order,
        _valid_attempt,
        valid_fill,
        state,
        order_ref,
        attempt_ref,
        fill_ref,
    ) = _preflight(
        order=order,
        attempt=attempt,
        fill=fill,
        account_state=account_state,
    )
    costs = valid_fill.cost_evidence
    bundle = apply_paper_execution_fill_settlement(
        state,
        execution_order_id=order_ref.execution_order_id,
        execution_order_digest=order_ref.execution_order_digest,
        execution_attempt_id=attempt_ref.attempt_id,
        execution_attempt_digest=attempt_ref.attempt_digest,
        execution_fill_id=fill_ref.fill_id,
        execution_fill_digest=fill_ref.fill_digest,
        instrument_id=valid_order.instrument_id,
        side=valid_fill.side,
        fill_quantity=valid_fill.fill_quantity,
        gross_notional=costs.gross_notional,
        total_charges=costs.total_charges,
        effective_timestamp_utc=(valid_fill.execution_event_reference.event_time),
        recorded_timestamp_utc=recorded_timestamp_utc,
    )
    link = _create_link(
        order_reference=order_ref,
        attempt_reference=attempt_ref,
        fill_reference=fill_ref,
        bundle=bundle,
    )
    result = object.__new__(PaperExecutionSettlementResult)
    object.__setattr__(
        result,
        "schema_version",
        PAPER_EXECUTION_SETTLEMENT_RESULT_SCHEMA_VERSION,
    )
    object.__setattr__(result, "ledger_bundle", bundle)
    object.__setattr__(result, "settlement_link", link)
    return validate_paper_execution_settlement_result(result)


def validate_paper_execution_settlement_result(
    value: object,
) -> PaperExecutionSettlementResult:
    if type(value) is not PaperExecutionSettlementResult:
        raise ValueError("settlement result must be PaperExecutionSettlementResult")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_SETTLEMENT_RESULT_SCHEMA_VERSION
            or type(value.ledger_bundle) is not PaperAccountLedgerEventBundle
        ):
            raise ValueError("settlement result metadata is invalid")
        link = validate_execution_settlement_link(value.settlement_link)
        bundle = value.ledger_bundle
        if (
            bundle.event.event_type != "execution_fill_posted"
            or len(bundle.cash_entries) != 1
            or len(bundle.position_entries) != 1
        ):
            raise ValueError("settlement result bundle shape is invalid")
        cash = bundle.cash_entries[0]
        position = bundle.position_entries[0]
        if not (
            link.account_id == bundle.event.account_id
            and link.account_event_id == bundle.event.event_id
            and link.account_event_digest == bundle.event.event_digest
            and link.account_chain_digest == bundle.event.chain_digest
            and link.account_version == bundle.event.account_version
            and link.cash_entry_id == cash.cash_entry_id
            and link.cash_entry_digest == cash.entry_digest
            and link.position_entry_id == position.position_entry_id
            and link.position_entry_digest == position.entry_digest
            and cash.event_id == bundle.event.event_id
            and position.event_id == bundle.event.event_id
        ):
            raise ValueError("settlement link does not match M31 authority")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution settlement result is invalid") from exc
    return value


def reconcile_paper_execution_settlement(
    *,
    account_state: PaperAccountLedgerState,
    order: PaperExecutionOrder,
    attempt: PaperExecutionAttempt,
    fill: PaperExecutionFill,
    result: PaperExecutionSettlementResult,
) -> PaperExecutionSettlementResult:
    """Prove one supplied result from the exact prior M31/M34 authority."""
    valid_result = validate_paper_execution_settlement_result(result)
    validate_paper_execution_fill_settlement_bundle(
        account_state,
        valid_result.ledger_bundle,
    )
    expected = settle_paper_execution_fill(
        order=order,
        attempt=attempt,
        fill=fill,
        account_state=account_state,
        recorded_timestamp_utc=(
            valid_result.ledger_bundle.event.recorded_timestamp_utc
        ),
    )
    if expected != valid_result or expected.to_dict() != valid_result.to_dict():
        raise ValueError("paper execution settlement reconciliation failed")
    return valid_result
