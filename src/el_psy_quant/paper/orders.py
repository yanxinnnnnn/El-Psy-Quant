"""Deterministic local paper order records and ledgers."""

from collections.abc import Sequence
from dataclasses import dataclass
import math
from numbers import Real

import pandas as pd

from el_psy_quant.data import normalize_symbol

PAPER_ORDER_SIDES = ("buy", "sell")
PAPER_ORDER_STATUSES = ("submitted", "accepted", "rejected", "filled")


def _normalize_order_id(order_id: str) -> str:
    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError("order_id must be a non-empty string")
    return order_id.strip()


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
    if normalized not in PAPER_ORDER_SIDES:
        supported = ", ".join(PAPER_ORDER_SIDES)
        raise ValueError(f"side must be one of: {supported}")
    return normalized


def _validate_quantity(quantity: float) -> float:
    if isinstance(quantity, bool) or not isinstance(quantity, Real):
        raise ValueError("quantity must be a positive finite number")

    normalized = float(quantity)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError("quantity must be a positive finite number")
    return normalized


def _normalize_status(status: str) -> str:
    if not isinstance(status, str):
        raise ValueError("status must be a string")

    normalized = status.strip().lower()
    if normalized not in PAPER_ORDER_STATUSES:
        supported = ", ".join(PAPER_ORDER_STATUSES)
        raise ValueError(f"status must be one of: {supported}")
    return normalized


@dataclass(frozen=True)
class PaperOrderRecord:
    """Immutable local paper order record."""

    order_id: str
    timestamp: object
    symbol: str
    side: str
    quantity: float
    status: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "order_id", _normalize_order_id(self.order_id))
        object.__setattr__(self, "timestamp", _normalize_timestamp(self.timestamp))
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "side", _normalize_side(self.side))
        object.__setattr__(self, "quantity", _validate_quantity(self.quantity))
        object.__setattr__(self, "status", _normalize_status(self.status))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible order export."""
        return {
            "order_id": self.order_id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "status": self.status,
        }


@dataclass(frozen=True)
class PaperOrderLedger:
    """Immutable deterministic local paper order ledger."""

    orders: Sequence[PaperOrderRecord]

    def __post_init__(self) -> None:
        if isinstance(self.orders, PaperOrderRecord):
            raise ValueError("orders must be a sequence of PaperOrderRecord objects")
        if isinstance(self.orders, str) or not isinstance(self.orders, Sequence):
            raise ValueError("orders must be a sequence of PaperOrderRecord objects")

        normalized_orders: list[PaperOrderRecord] = []
        seen_order_ids: set[str] = set()
        for order in self.orders:
            if not isinstance(order, PaperOrderRecord):
                raise ValueError("orders must contain only PaperOrderRecord objects")
            if order.order_id in seen_order_ids:
                raise ValueError(f"duplicate order_id: {order.order_id}")
            seen_order_ids.add(order.order_id)
            normalized_orders.append(order)

        object.__setattr__(self, "orders", tuple(normalized_orders))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible ledger export."""
        return {
            "order_count": len(self.orders),
            "orders": [order.to_dict() for order in self.orders],
        }


def create_paper_order_record(
    *,
    order_id: str,
    timestamp: object,
    symbol: str,
    side: str,
    quantity: float,
    status: str,
) -> PaperOrderRecord:
    """Create and validate one local paper order record."""
    return PaperOrderRecord(
        order_id=order_id,
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        status=status,
    )


def create_paper_order_ledger(
    orders: Sequence[PaperOrderRecord],
) -> PaperOrderLedger:
    """Create and validate one local paper order ledger."""
    return PaperOrderLedger(orders=orders)
