"""Canonical JSON and strict row/domain mapping for durable M34 authority."""

from __future__ import annotations

import types
from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.paper_execution import (
    ExecutionSettlementLink,
    PaperExecutionAttempt,
    PaperExecutionBasisPoints,
    PaperExecutionFill,
    PaperExecutionOrder,
    validate_execution_settlement_link,
    validate_paper_execution_attempt,
    validate_paper_execution_fill,
    validate_paper_execution_order,
)
from el_psy_quant.persistence.paper_execution_model import (
    PaperExecutionAttemptRow,
    PaperExecutionCommandReceiptRow,
    PaperExecutionFillRow,
    PaperExecutionOrderRow,
    PaperExecutionSettlementLinkRow,
)
from el_psy_quant.persistence.paper_execution_records import (
    PAPER_EXECUTION_PERSISTENCE_RECORD_SCHEMA_VERSION,
    PaperExecutionCommandReceipt,
    PaperExecutionCorruptAuthorityError,
    canonical_json,
    exact_utc,
    load_canonical_json,
)


def _hydrate(annotation: object, value: object) -> object:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if annotation is Any or annotation is object:
        return value
    if origin in (Union, types.UnionType):
        if value is None and type(None) in args:
            return None
        failures: list[Exception] = []
        for candidate in args:
            if candidate is type(None):
                continue
            try:
                return _hydrate(candidate, value)
            except (TypeError, ValueError) as exc:
                failures.append(exc)
        raise ValueError("union payload is invalid") from (
            failures[-1] if failures else None
        )
    if origin is Literal:
        if value not in args:
            raise ValueError("literal payload is invalid")
        return value
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("tuple payload must be a JSON list")
        item_type = args[0] if args else object
        return tuple(_hydrate(item_type, item) for item in value)
    if origin is list:
        if type(value) is not list:
            raise ValueError("list payload is invalid")
        item_type = args[0] if args else object
        return [_hydrate(item_type, item) for item in value]
    if origin is dict:
        if type(value) is not dict:
            raise ValueError("mapping payload is invalid")
        key_type, value_type = args or (object, object)
        return {
            _hydrate(key_type, key): _hydrate(value_type, item)
            for key, item in value.items()
        }
    if annotation is PaperMoney:
        if type(value) is not str:
            raise ValueError("money payload is invalid")
        return PaperMoney.parse(value)
    if annotation is PaperQuantity:
        if type(value) is not str:
            raise ValueError("quantity payload is invalid")
        return PaperQuantity.parse(value)
    if annotation is PaperExecutionBasisPoints:
        if type(value) is not str:
            raise ValueError("basis-points payload is invalid")
        return PaperExecutionBasisPoints.parse(value)
    if annotation is datetime:
        if type(value) is not str:
            raise ValueError("datetime payload is invalid")
        return datetime.fromisoformat(value)
    if annotation is date:
        if type(value) is not str:
            raise ValueError("date payload is invalid")
        return date.fromisoformat(value)
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            raise ValueError("scalar payload type is invalid")
        return value
    if isinstance(annotation, type) and is_dataclass(annotation):
        if type(value) is not dict:
            raise ValueError("domain payload must be an object")
        hints = get_type_hints(annotation)
        expected = {field.name for field in fields(annotation)}
        extras: dict[str, object] = {}
        if annotation.__name__ == "ReplayCursor":
            extras = {"schema_version": 1}
        elif annotation.__name__ == "PaperExecutionRiskRevalidation":
            extras = {
                "rounding_mode": "ROUND_HALF_EVEN",
                "rounding_quantum": "0.00000001",
            }
        if set(value) != expected | set(extras) or any(
            value.get(key) != expected_value for key, expected_value in extras.items()
        ):
            raise ValueError("domain payload fields are invalid")
        result = object.__new__(annotation)
        for field in fields(annotation):
            object.__setattr__(
                result,
                field.name,
                _hydrate(hints.get(field.name, object), value[field.name]),
            )
        return result
    raise ValueError("unsupported persisted domain type")


def _domain_from_payload(cls: type[Any], payload: object) -> Any:
    try:
        return _hydrate(cls, payload)
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


def _sqlite_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("persisted timestamp is invalid")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _column_equal(actual: object, expected: object) -> bool:
    if type(actual) is datetime and type(expected) is datetime:
        return _sqlite_utc(actual) == _sqlite_utc(expected)
    return actual == expected


def order_row(order: PaperExecutionOrder) -> PaperExecutionOrderRow:
    validate_paper_execution_order(order)
    intent = order.order_intent_reference
    risk = order.risk_handoff_reference
    account = order.account_handoff_reference
    market = order.market_handoff_reference
    policy = order.execution_policy_reference
    return PaperExecutionOrderRow(
        record_schema_version=PAPER_EXECUTION_PERSISTENCE_RECORD_SCHEMA_VERSION,
        order_schema_version=order.schema_version,
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        payload_json=canonical_json(order.to_dict()),
        intent_id=intent.intent_id,
        intent_digest=intent.intent_digest,
        risk_decision_id=risk.risk_decision_id,
        risk_decision_digest=risk.risk_decision_digest,
        risk_snapshot_id=risk.risk_snapshot_id,
        risk_snapshot_digest=risk.risk_snapshot_digest,
        account_id=order.account_id,
        account_handoff_version=account.account_head_version,
        account_handoff_event_id=account.account_head_event_id,
        account_handoff_chain_digest=account.account_head_chain_digest,
        calendar_id=market.calendar_id,
        calendar_version=market.calendar_version,
        trading_session_id=market.trading_session_id,
        replay_id=market.replay_id,
        event_stream_digest=market.event_stream_digest,
        handoff_cursor_position=market.cursor_position,
        handoff_event_id=market.current_event_id,
        instrument_id=order.instrument_id,
        side=order.side,
        requested_quantity=order.requested_quantity.canonical,
        policy_id=policy.policy_id,
        policy_configuration_digest=policy.configuration_digest,
        policy_reference_digest=policy.reference_digest,
        origin_command_digest=order.origin_command_digest,
        created_at=order.created_at,
    )


def order_from_row(row: PaperExecutionOrderRow) -> PaperExecutionOrder:
    try:
        if row.record_schema_version != 1:
            raise ValueError("unsupported order record schema")
        order = _domain_from_payload(
            PaperExecutionOrder, load_canonical_json(row.payload_json)
        )
        validate_paper_execution_order(order)
        expected = order_row(order)
        for name in PaperExecutionOrderRow.__table__.columns.keys():
            if name != "payload_json" and not _column_equal(
                getattr(row, name), getattr(expected, name)
            ):
                raise ValueError("order payload/index mismatch")
        if row.payload_json != expected.payload_json:
            raise ValueError("order payload is not canonical")
        return order
    except PaperExecutionCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


def attempt_row(attempt: PaperExecutionAttempt) -> PaperExecutionAttemptRow:
    validate_paper_execution_attempt(attempt)
    event = attempt.consumed_event_reference
    return PaperExecutionAttemptRow(
        record_schema_version=1,
        attempt_schema_version=attempt.schema_version,
        attempt_id=attempt.attempt_id,
        attempt_digest=attempt.attempt_digest,
        execution_order_id=attempt.execution_order_reference.execution_order_id,
        execution_version_before=attempt.execution_version_before,
        execution_version_after=attempt.execution_version_after,
        attempt_result=attempt.attempt_result,
        consumed_event_id=None if event is None else event.event_id,
        consumed_event_position=None
        if event is None
        else event.consumed_event_position,
        pre_cursor_position=attempt.pre_step_cursor.position,
        pre_cursor_last_event_id=attempt.pre_step_cursor.last_event_id,
        post_cursor_position=attempt.post_step_cursor.position,
        post_cursor_last_event_id=attempt.post_step_cursor.last_event_id,
        payload_json=canonical_json(attempt.to_dict()),
        created_at=attempt.created_at,
    )


def attempt_from_row(row: PaperExecutionAttemptRow) -> PaperExecutionAttempt:
    try:
        if row.record_schema_version != 1:
            raise ValueError("unsupported Attempt record schema")
        attempt = _domain_from_payload(
            PaperExecutionAttempt, load_canonical_json(row.payload_json)
        )
        validate_paper_execution_attempt(attempt)
        expected = attempt_row(attempt)
        for name in PaperExecutionAttemptRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("Attempt payload/index mismatch")
        return attempt
    except PaperExecutionCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


def fill_row(fill: PaperExecutionFill) -> PaperExecutionFillRow:
    validate_paper_execution_fill(fill)
    event = fill.execution_event_reference
    return PaperExecutionFillRow(
        record_schema_version=1,
        fill_schema_version=fill.schema_version,
        fill_id=fill.fill_id,
        fill_digest=fill.fill_digest,
        execution_order_id=fill.execution_order_reference.execution_order_id,
        attempt_id=fill.attempt_reference.attempt_id,
        consumed_event_id=event.event_id,
        consumed_event_position=event.consumed_event_position,
        payload_json=canonical_json(fill.to_dict()),
        created_at=fill.created_at,
    )


def fill_from_row(row: PaperExecutionFillRow) -> PaperExecutionFill:
    try:
        if row.record_schema_version != 1:
            raise ValueError("unsupported Fill record schema")
        fill = _domain_from_payload(
            PaperExecutionFill, load_canonical_json(row.payload_json)
        )
        validate_paper_execution_fill(fill)
        expected = fill_row(fill)
        for name in PaperExecutionFillRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("Fill payload/index mismatch")
        return fill
    except PaperExecutionCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


def settlement_link_row(
    link: ExecutionSettlementLink, *, recorded_at: datetime
) -> PaperExecutionSettlementLinkRow:
    validate_execution_settlement_link(link)
    return PaperExecutionSettlementLinkRow(
        record_schema_version=1,
        settlement_link_schema_version=link.schema_version,
        settlement_link_id=link.settlement_link_id,
        settlement_link_digest=link.settlement_link_digest,
        settlement_link_evidence_digest=link.settlement_link_evidence_digest,
        execution_order_id=link.execution_order_reference.execution_order_id,
        attempt_id=link.execution_attempt_reference.attempt_id,
        fill_id=link.execution_fill_reference.fill_id,
        account_id=link.account_id,
        account_event_id=link.account_event_id,
        cash_entry_id=link.cash_entry_id,
        position_entry_id=link.position_entry_id,
        payload_json=canonical_json(link.to_dict()),
        recorded_at=exact_utc(recorded_at, "recorded_at"),
    )


def settlement_link_from_row(
    row: PaperExecutionSettlementLinkRow,
) -> ExecutionSettlementLink:
    try:
        if row.record_schema_version != 1:
            raise ValueError("unsupported settlement-link record schema")
        link = _domain_from_payload(
            ExecutionSettlementLink, load_canonical_json(row.payload_json)
        )
        validate_execution_settlement_link(link)
        expected = settlement_link_row(link, recorded_at=_sqlite_utc(row.recorded_at))
        for name in PaperExecutionSettlementLinkRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("settlement-link payload/index mismatch")
        return link
    except PaperExecutionCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


def receipt_row(
    receipt: PaperExecutionCommandReceipt,
) -> PaperExecutionCommandReceiptRow:
    if type(receipt) is not PaperExecutionCommandReceipt:
        raise ValueError("receipt must be PaperExecutionCommandReceipt")
    return PaperExecutionCommandReceiptRow(**receipt.__dict__)


def receipt_from_row(
    row: PaperExecutionCommandReceiptRow,
) -> PaperExecutionCommandReceipt:
    try:
        values = {
            name: getattr(row, name)
            for name in PaperExecutionCommandReceipt.__dataclass_fields__
        }
        values["created_at"] = _sqlite_utc(values["created_at"])
        receipt = PaperExecutionCommandReceipt(**values)
        expected = receipt_row(receipt)
        for name in PaperExecutionCommandReceiptRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("receipt row mismatch")
        return receipt
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


__all__ = [
    "attempt_from_row",
    "attempt_row",
    "fill_from_row",
    "fill_row",
    "order_from_row",
    "order_row",
    "receipt_from_row",
    "receipt_row",
    "settlement_link_from_row",
    "settlement_link_row",
]
