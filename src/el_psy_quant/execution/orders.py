"""Order intent boundaries for deterministic local backtests."""

import math
from dataclasses import dataclass
from numbers import Real

import pandas as pd

from el_psy_quant.data import normalize_symbol
from el_psy_quant.execution.assumptions import (
    ExecutionAssumptions,
    default_execution_assumptions,
)

SUPPORTED_ORDER_SIDES = ("buy", "sell")


def _normalize_timestamp(timestamp: object) -> pd.Timestamp:
    try:
        normalized = pd.Timestamp(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be convertible to a pandas Timestamp") from exc

    if pd.isna(normalized):
        raise ValueError("timestamp must be valid")
    return normalized


def _normalize_side(side: str) -> str:
    if not isinstance(side, str):
        raise ValueError("side must be a string")

    normalized = side.strip().lower()
    if normalized not in SUPPORTED_ORDER_SIDES:
        supported = ", ".join(SUPPORTED_ORDER_SIDES)
        raise ValueError(f"side must be one of: {supported}")
    return normalized


def _validate_quantity(quantity: float) -> float:
    if isinstance(quantity, bool) or not isinstance(quantity, Real):
        raise ValueError("quantity must be a positive number")

    normalized = float(quantity)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError("quantity must be a positive number")
    return normalized


def _normalize_assumptions(
    assumptions: ExecutionAssumptions | None,
) -> ExecutionAssumptions:
    if assumptions is None:
        return default_execution_assumptions()
    if not isinstance(assumptions, ExecutionAssumptions):
        raise ValueError("assumptions must be an ExecutionAssumptions instance")
    return assumptions


@dataclass(frozen=True)
class OrderIntent:
    """A deterministic statement of what a strategy wants to do."""

    timestamp: object
    symbol: str
    side: str
    quantity: float
    assumptions: ExecutionAssumptions | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _normalize_timestamp(self.timestamp))
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "side", _normalize_side(self.side))
        object.__setattr__(self, "quantity", _validate_quantity(self.quantity))
        object.__setattr__(
            self,
            "assumptions",
            _normalize_assumptions(self.assumptions),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "assumptions": self.assumptions.to_dict(),
        }


def validate_order_intent(
    timestamp: object,
    symbol: str,
    side: str,
    quantity: float,
    assumptions: ExecutionAssumptions | None = None,
) -> OrderIntent:
    """Validate and normalize one order intent."""
    return OrderIntent(
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        assumptions=assumptions,
    )
