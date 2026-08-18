"""Private exact Decimal arithmetic shared by S209 execution evidence."""

from __future__ import annotations

from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from el_psy_quant.paper_account import PaperMoney, PaperQuantity

PAPER_EXECUTION_MONEY_QUANTUM = Decimal("0.00000001")
PAPER_EXECUTION_ROUNDING_MODE = "ROUND_HALF_EVEN"

_ARITHMETIC_CONTEXT = Context(prec=100, rounding=ROUND_HALF_EVEN)


def canonical_decimal(value: Decimal) -> str:
    """Return one non-exponent fixed-point representation."""
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return "0" if result in {"", "-0"} else result


def exact_money(value: object, *, field_name: str) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is invalid")
    return rebuilt


def exact_quantity(
    value: object,
    *,
    field_name: str,
    strictly_positive: bool = False,
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
    if strictly_positive and rebuilt.decimal_value <= 0:
        raise ValueError(f"{field_name} must be strictly positive")
    return rebuilt


def multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_ARITHMETIC_CONTEXT):
        return left * right


def divide(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_ARITHMETIC_CONTEXT):
        return left / right


def add(*values: Decimal) -> Decimal:
    with localcontext(_ARITHMETIC_CONTEXT):
        result = Decimal("0")
        for value in values:
            result += value
        return result


def subtract(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_ARITHMETIC_CONTEXT):
        return left - right


def round_money(value: Decimal) -> tuple[PaperMoney, bool]:
    """Round once to the M31 money quantum and retain whether it changed."""
    with localcontext(_ARITHMETIC_CONTEXT):
        rounded = value.quantize(
            PAPER_EXECUTION_MONEY_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
    return PaperMoney.parse(canonical_decimal(rounded)), rounded != value
