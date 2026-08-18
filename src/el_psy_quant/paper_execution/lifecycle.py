"""Pure derived lifecycle evidence for M34 Paper execution orders."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.paper_execution._canonical import reject_public_construction
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrder,
    PaperExecutionOrderReference,
    _clone_order_reference,
    create_paper_execution_order_reference,
    validate_paper_execution_order,
    validate_paper_execution_order_reference,
)

PAPER_EXECUTION_ORDER_STATE_SCHEMA_VERSION = 1

PAPER_EXECUTION_ORDER_STATUS_WORKING = "working"
PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED = "partially_filled"
PAPER_EXECUTION_ORDER_STATUS_FILLED = "filled"
PAPER_EXECUTION_ORDER_STATUS_REJECTED = "rejected"
PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED = "partially_filled_rejected"

SUPPORTED_PAPER_EXECUTION_ORDER_STATUSES = (
    PAPER_EXECUTION_ORDER_STATUS_WORKING,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_REJECTED,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED,
)

PaperExecutionOrderStatus = Literal[
    "working",
    "partially_filled",
    "filled",
    "rejected",
    "partially_filled_rejected",
]


def _canonical_decimal(value: Decimal) -> str:
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return "0" if result in {"", "-0"} else result


def _exact_quantity(
    value: object,
    *,
    field_name: str,
    non_negative: bool = True,
) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is invalid")
    if non_negative and rebuilt.decimal_value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return rebuilt


def _derive_status(
    *,
    requested: Decimal,
    cumulative: Decimal,
    terminal_rejected: bool,
) -> PaperExecutionOrderStatus:
    if type(terminal_rejected) is not bool:
        raise ValueError("terminal_rejected must be a boolean")
    if cumulative < 0 or cumulative > requested:
        raise ValueError("cumulative filled quantity is outside order bounds")
    if terminal_rejected:
        if cumulative == requested:
            raise ValueError("a fully filled order cannot be terminal-rejected")
        if cumulative == 0:
            return PAPER_EXECUTION_ORDER_STATUS_REJECTED
        return PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED
    if cumulative == 0:
        return PAPER_EXECUTION_ORDER_STATUS_WORKING
    if cumulative == requested:
        return PAPER_EXECUTION_ORDER_STATUS_FILLED
    return PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED


@dataclass(frozen=True, init=False)
class PaperExecutionOrderState:
    """Immutable derived state; the Order remains the authority."""

    schema_version: int
    execution_order_reference: PaperExecutionOrderReference
    execution_version: int
    status: PaperExecutionOrderStatus
    requested_quantity: PaperQuantity
    cumulative_filled_quantity: PaperQuantity
    remaining_quantity: PaperQuantity
    terminal: bool

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "execution_order_reference": (self.execution_order_reference.to_dict()),
            "execution_version": self.execution_version,
            "status": self.status,
            "requested_quantity": self.requested_quantity.to_json_value(),
            "cumulative_filled_quantity": (
                self.cumulative_filled_quantity.to_json_value()
            ),
            "remaining_quantity": self.remaining_quantity.to_json_value(),
            "terminal": self.terminal,
        }


def _build_state(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    execution_version: int,
    requested_quantity: PaperQuantity,
    cumulative_filled_quantity: PaperQuantity,
    terminal_rejected: bool,
) -> PaperExecutionOrderState:
    if type(execution_version) is not int or execution_version < 0:
        raise ValueError("execution_version must be non-negative")
    requested = _exact_quantity(
        requested_quantity,
        field_name="requested_quantity",
    )
    cumulative = _exact_quantity(
        cumulative_filled_quantity,
        field_name="cumulative_filled_quantity",
    )
    if requested.decimal_value <= 0:
        raise ValueError("requested_quantity must be strictly positive")
    status = _derive_status(
        requested=requested.decimal_value,
        cumulative=cumulative.decimal_value,
        terminal_rejected=terminal_rejected,
    )
    remaining = PaperQuantity.parse(
        _canonical_decimal(requested.decimal_value - cumulative.decimal_value)
    )
    reference = _clone_order_reference(execution_order_reference)
    result = object.__new__(PaperExecutionOrderState)
    for field_name, value in (
        ("schema_version", PAPER_EXECUTION_ORDER_STATE_SCHEMA_VERSION),
        ("execution_order_reference", reference),
        ("execution_version", execution_version),
        ("status", status),
        ("requested_quantity", PaperQuantity.parse(requested.canonical)),
        (
            "cumulative_filled_quantity",
            PaperQuantity.parse(cumulative.canonical),
        ),
        ("remaining_quantity", remaining),
        (
            "terminal",
            status
            in {
                PAPER_EXECUTION_ORDER_STATUS_FILLED,
                PAPER_EXECUTION_ORDER_STATUS_REJECTED,
                PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED,
            },
        ),
    ):
        object.__setattr__(result, field_name, value)
    return result


def _derive_paper_execution_order_state(
    order: PaperExecutionOrder,
    *,
    execution_version: int,
    cumulative_filled_quantity: PaperQuantity,
    terminal_rejected: bool,
) -> PaperExecutionOrderState:
    """Controlled pure seam reserved for S209 Attempt/Fill evidence."""
    valid_order = validate_paper_execution_order(order)
    return _build_state(
        execution_order_reference=create_paper_execution_order_reference(valid_order),
        execution_version=execution_version,
        requested_quantity=valid_order.requested_quantity,
        cumulative_filled_quantity=cumulative_filled_quantity,
        terminal_rejected=terminal_rejected,
    )


def create_initial_paper_execution_order_state(
    order: PaperExecutionOrder,
) -> PaperExecutionOrderState:
    """Derive the exact version-zero working state for a new valid Order."""
    return _derive_paper_execution_order_state(
        order,
        execution_version=0,
        cumulative_filled_quantity=PaperQuantity.parse("0"),
        terminal_rejected=False,
    )


def validate_paper_execution_order_state(
    value: object,
) -> PaperExecutionOrderState:
    """Validate quantity conservation and the closed derived status rules."""
    if type(value) is not PaperExecutionOrderState:
        raise ValueError("state must be PaperExecutionOrderState")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_ORDER_STATE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported execution state schema_version")
        validate_paper_execution_order_reference(value.execution_order_reference)
        if type(value.execution_version) is not int or value.execution_version < 0:
            raise ValueError("execution_version must be non-negative")
        requested = _exact_quantity(
            value.requested_quantity,
            field_name="requested_quantity",
        )
        cumulative = _exact_quantity(
            value.cumulative_filled_quantity,
            field_name="cumulative_filled_quantity",
        )
        remaining = _exact_quantity(
            value.remaining_quantity,
            field_name="remaining_quantity",
        )
        if requested.decimal_value <= 0:
            raise ValueError("requested quantity must be positive")
        if (
            remaining.decimal_value
            != requested.decimal_value - cumulative.decimal_value
        ):
            raise ValueError("execution state violates quantity conservation")
        if type(value.terminal) is not bool:
            raise ValueError("terminal must be a boolean")
        if value.status not in SUPPORTED_PAPER_EXECUTION_ORDER_STATUSES:
            raise ValueError("unsupported paper execution order status")
        terminal_rejected = value.status in {
            PAPER_EXECUTION_ORDER_STATUS_REJECTED,
            PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED,
        }
        expected = _build_state(
            execution_order_reference=value.execution_order_reference,
            execution_version=value.execution_version,
            requested_quantity=requested,
            cumulative_filled_quantity=cumulative,
            terminal_rejected=terminal_rejected,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution order state is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution order state is invalid")
    return value
