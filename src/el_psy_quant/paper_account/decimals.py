"""Exact decimal value contracts for future Paper Account ledger authority."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

PAPER_MONEY_SCHEMA_VERSION = 1
PAPER_QUANTITY_SCHEMA_VERSION = 1

_CANONICAL_DECIMAL_PATTERN = re.compile(
    r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z"
)
_MAX_INTEGER_DIGITS = 18


def _parse_canonical_decimal(
    value: str,
    *,
    field_name: str,
    maximum_fractional_digits: int,
) -> tuple[Decimal, str]:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a canonical decimal string")
    if _CANONICAL_DECIMAL_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical decimal string")

    unsigned = value[1:] if value.startswith("-") else value
    integer_part, separator, fractional_part = unsigned.partition(".")
    if len(integer_part) > _MAX_INTEGER_DIGITS:
        raise ValueError(
            f"{field_name} must contain at most {_MAX_INTEGER_DIGITS} "
            "integer digits"
        )
    if separator and len(fractional_part) > maximum_fractional_digits:
        raise ValueError(
            f"{field_name} must contain at most "
            f"{maximum_fractional_digits} fractional digits"
        )

    decimal_value = Decimal(value)
    if decimal_value.is_zero() and value.startswith("-"):
        raise ValueError(f"{field_name} must not use signed zero")
    return decimal_value, value


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("decimal values must be created with the parse class method")


@dataclass(frozen=True, init=False)
class PaperMoney:
    """An exact signed money value with at most eight fractional digits."""

    _decimal_value: Decimal
    _canonical: str

    __init__ = _reject_public_construction

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse one already-canonical money string without rounding."""
        decimal_value, canonical = _parse_canonical_decimal(
            value,
            field_name="money",
            maximum_fractional_digits=8,
        )
        result = object.__new__(cls)
        object.__setattr__(result, "_decimal_value", decimal_value)
        object.__setattr__(result, "_canonical", canonical)
        return result

    @property
    def decimal_value(self) -> Decimal:
        """Return the exact immutable Decimal value."""
        return self._decimal_value

    @property
    def canonical(self) -> str:
        """Return the canonical fixed-point string."""
        return self._canonical

    def to_json_value(self) -> str:
        """Return the strictly JSON-compatible financial value."""
        return self._canonical

    def to_dict(self) -> dict[str, object]:
        """Return a versioned deterministic JSON-compatible export."""
        return {
            "schema_version": PAPER_MONEY_SCHEMA_VERSION,
            "value": self._canonical,
        }

    def __str__(self) -> str:
        return self._canonical


@dataclass(frozen=True, init=False)
class PaperQuantity:
    """An exact signed quantity with at most twelve fractional digits."""

    _decimal_value: Decimal
    _canonical: str

    __init__ = _reject_public_construction

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse one already-canonical quantity string without rounding."""
        decimal_value, canonical = _parse_canonical_decimal(
            value,
            field_name="quantity",
            maximum_fractional_digits=12,
        )
        result = object.__new__(cls)
        object.__setattr__(result, "_decimal_value", decimal_value)
        object.__setattr__(result, "_canonical", canonical)
        return result

    @property
    def decimal_value(self) -> Decimal:
        """Return the exact immutable Decimal value."""
        return self._decimal_value

    @property
    def canonical(self) -> str:
        """Return the canonical fixed-point string."""
        return self._canonical

    def to_json_value(self) -> str:
        """Return the strictly JSON-compatible financial value."""
        return self._canonical

    def to_dict(self) -> dict[str, object]:
        """Return a versioned deterministic JSON-compatible export."""
        return {
            "schema_version": PAPER_QUANTITY_SCHEMA_VERSION,
            "value": self._canonical,
        }

    def __str__(self) -> str:
        return self._canonical
