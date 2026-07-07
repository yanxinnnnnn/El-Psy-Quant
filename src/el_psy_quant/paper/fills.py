"""Explicit paper fill application to local account state."""

from collections.abc import Sequence
from dataclasses import dataclass
import math
from numbers import Real

import pandas as pd

from el_psy_quant.data import normalize_symbol
from el_psy_quant.paper.account import PaperAccountState, create_paper_account_state

PAPER_FILL_SIDES = ("buy", "sell")


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
    if normalized not in PAPER_FILL_SIDES:
        supported = ", ".join(PAPER_FILL_SIDES)
        raise ValueError(f"side must be one of: {supported}")
    return normalized


def _validate_quantity(quantity: float) -> float:
    if isinstance(quantity, bool) or not isinstance(quantity, Real):
        raise ValueError("quantity must be a positive finite number")

    normalized = float(quantity)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError("quantity must be a positive finite number")
    return normalized


def _validate_price(price: float) -> float:
    if isinstance(price, bool) or not isinstance(price, Real):
        raise ValueError("price must be a finite non-negative number")

    normalized = float(price)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError("price must be a finite non-negative number")
    return normalized


def _normalize_order_id(order_id: str | None) -> str | None:
    if order_id is None:
        return None
    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError("order_id must be a non-empty string when provided")
    return order_id.strip()


@dataclass(frozen=True)
class PaperFill:
    """Immutable explicit paper fill input."""

    timestamp: object
    symbol: str
    side: str
    quantity: float
    price: float
    order_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _normalize_timestamp(self.timestamp))
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "side", _normalize_side(self.side))
        object.__setattr__(self, "quantity", _validate_quantity(self.quantity))
        object.__setattr__(self, "price", _validate_price(self.price))
        object.__setattr__(self, "order_id", _normalize_order_id(self.order_id))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible fill export."""
        payload: dict[str, object] = {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
        }
        if self.order_id is not None:
            payload["order_id"] = self.order_id
        return payload


def _validate_fills(fills: Sequence[PaperFill]) -> tuple[PaperFill, ...]:
    if isinstance(fills, PaperFill):
        raise ValueError("fills must be a non-empty sequence of PaperFill objects")
    if isinstance(fills, str) or not isinstance(fills, Sequence):
        raise ValueError("fills must be a non-empty sequence of PaperFill objects")
    if not fills:
        raise ValueError("fills must not be empty")

    normalized_fills: list[PaperFill] = []
    for fill in fills:
        if not isinstance(fill, PaperFill):
            raise ValueError("fills must contain only PaperFill objects")
        normalized_fills.append(fill)
    return tuple(normalized_fills)


def create_paper_fill(
    *,
    timestamp: object,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    order_id: str | None = None,
) -> PaperFill:
    """Create and validate one explicit paper fill."""
    return PaperFill(
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_id=order_id,
    )


def apply_paper_fills(
    account_state: PaperAccountState,
    fills: Sequence[PaperFill],
) -> PaperAccountState:
    """Apply explicit paper fills and return a new account state."""
    if not isinstance(account_state, PaperAccountState):
        raise ValueError("account_state must be a PaperAccountState")
    validated_fills = _validate_fills(fills)

    current_cash = account_state.current_cash
    positions = dict(account_state.positions)
    output_timestamp = validated_fills[-1].timestamp

    for fill in validated_fills:
        notional = fill.quantity * fill.price
        current_position = positions.get(fill.symbol, 0.0)
        if fill.side == "buy":
            current_cash -= notional
            positions[fill.symbol] = current_position + fill.quantity
        else:
            current_cash += notional
            positions[fill.symbol] = current_position - fill.quantity

    return create_paper_account_state(
        starting_cash=account_state.starting_cash,
        current_cash=current_cash,
        positions=positions,
        timestamp=output_timestamp,
    )
