"""Deterministic local paper account state."""

from collections.abc import Mapping
from dataclasses import dataclass
import math
from numbers import Real

import pandas as pd

from el_psy_quant.data import normalize_symbol


def _validate_cash(value: float, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a finite non-negative number")

    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{field_name} must be a finite non-negative number")
    return normalized


def _normalize_timestamp(timestamp: object) -> pd.Timestamp:
    try:
        normalized = pd.Timestamp(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be convertible to a pandas Timestamp") from exc

    if pd.isna(normalized):
        raise ValueError("timestamp must be valid")
    return normalized


def _normalize_positions(
    positions: Mapping[str, float],
) -> tuple[tuple[str, float], ...]:
    if not isinstance(positions, Mapping):
        raise ValueError("positions must be a mapping of symbol to quantity")

    normalized_positions: dict[str, float] = {}
    for symbol, quantity in positions.items():
        normalized_symbol = normalize_symbol(symbol)
        if normalized_symbol in normalized_positions:
            raise ValueError(f"duplicate symbol: {normalized_symbol}")
        if isinstance(quantity, bool) or not isinstance(quantity, Real):
            raise ValueError(f"{normalized_symbol} quantity must be finite")

        normalized_quantity = float(quantity)
        if not math.isfinite(normalized_quantity):
            raise ValueError(f"{normalized_symbol} quantity must be finite")
        normalized_positions[normalized_symbol] = normalized_quantity

    return tuple(sorted(normalized_positions.items()))


def _normalize_prices(prices: Mapping[str, float]) -> dict[str, float]:
    if not isinstance(prices, Mapping):
        raise ValueError("prices must be a mapping of symbol to price")

    normalized_prices: dict[str, float] = {}
    for symbol, price in prices.items():
        normalized_symbol = normalize_symbol(symbol)
        if normalized_symbol in normalized_prices:
            raise ValueError(f"duplicate price symbol: {normalized_symbol}")
        if isinstance(price, bool) or not isinstance(price, Real):
            raise ValueError(f"{normalized_symbol} price must be finite and non-negative")

        normalized_price = float(price)
        if not math.isfinite(normalized_price) or normalized_price < 0:
            raise ValueError(f"{normalized_symbol} price must be finite and non-negative")
        normalized_prices[normalized_symbol] = normalized_price
    return normalized_prices


@dataclass(frozen=True)
class PaperAccountState:
    """Immutable local paper account state."""

    starting_cash: float
    current_cash: float
    positions: Mapping[str, float]
    timestamp: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "starting_cash",
            _validate_cash(self.starting_cash, field_name="starting_cash"),
        )
        object.__setattr__(
            self,
            "current_cash",
            _validate_cash(self.current_cash, field_name="current_cash"),
        )
        object.__setattr__(
            self,
            "positions",
            _normalize_positions(self.positions),
        )
        object.__setattr__(self, "timestamp", _normalize_timestamp(self.timestamp))

    def to_dict(
        self,
        prices: Mapping[str, float] | None = None,
    ) -> dict[str, object]:
        """Return a deterministic JSON-compatible account state export."""
        payload: dict[str, object] = {
            "timestamp": self.timestamp.isoformat(),
            "starting_cash": self.starting_cash,
            "current_cash": self.current_cash,
            "positions": [
                {"symbol": symbol, "quantity": quantity}
                for symbol, quantity in self.positions
            ],
        }
        if prices is not None:
            normalized_prices = _normalize_prices(prices)
            equity = self.current_cash
            for symbol, quantity in self.positions:
                if symbol not in normalized_prices:
                    raise ValueError(f"missing price for symbol: {symbol}")
                equity += quantity * normalized_prices[symbol]
            payload["equity"] = float(equity)
        return payload


def create_paper_account_state(
    *,
    starting_cash: float,
    current_cash: float,
    positions: Mapping[str, float],
    timestamp: object,
) -> PaperAccountState:
    """Create and validate one local paper account state."""
    return PaperAccountState(
        starting_cash=starting_cash,
        current_cash=current_cash,
        positions=positions,
        timestamp=timestamp,
    )
