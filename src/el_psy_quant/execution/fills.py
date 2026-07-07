"""Deterministic assumed fills for local backtests."""

import math
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.execution.assumptions import ExecutionAssumptions
from el_psy_quant.execution.orders import OrderIntent

PRICE_FIELD_COLUMNS = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
}


@dataclass(frozen=True)
class AssumedFill:
    """A deterministic local backtest fill assumption."""

    intent_timestamp: pd.Timestamp
    fill_timestamp: pd.Timestamp
    symbol: str
    side: str
    quantity: float
    price: float
    price_field: str
    assumptions: ExecutionAssumptions

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible dictionary representation."""
        return {
            "intent_timestamp": self.intent_timestamp.isoformat(),
            "fill_timestamp": self.fill_timestamp.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "price_field": self.price_field,
            "assumptions": self.assumptions.to_dict(),
        }


def _validate_price_data(price_data: pd.DataFrame) -> None:
    if not isinstance(price_data, pd.DataFrame):
        raise ValueError("price_data must be a pandas DataFrame")
    if price_data.empty:
        raise ValueError("price_data must not be empty")
    if not isinstance(price_data.index, pd.DatetimeIndex):
        raise ValueError("price_data must have a DatetimeIndex")


def _price_column_for_assumptions(assumptions: ExecutionAssumptions) -> str:
    return PRICE_FIELD_COLUMNS[assumptions.price_field]


def _select_fill_timestamp(
    order_intent: OrderIntent,
    price_data: pd.DataFrame,
) -> pd.Timestamp:
    if order_intent.assumptions.timing == "same_bar":
        if order_intent.timestamp not in price_data.index:
            raise ValueError("same_bar fill bar is unavailable")
        return order_intent.timestamp

    next_timestamps = price_data.index[price_data.index > order_intent.timestamp]
    if next_timestamps.empty:
        raise ValueError("next_bar fill bar is unavailable")
    return next_timestamps.min()


def _read_fill_price(
    price_data: pd.DataFrame,
    fill_timestamp: pd.Timestamp,
    price_column: str,
) -> float:
    if price_column not in price_data.columns:
        raise ValueError(f"price_data is missing required column: {price_column}")
    if not pd.api.types.is_numeric_dtype(price_data[price_column]):
        raise ValueError(f"{price_column} must contain numeric values")

    raw_price = price_data.loc[fill_timestamp, price_column]
    if isinstance(raw_price, pd.Series):
        raise ValueError("fill bar must be unique")
    if pd.isna(raw_price):
        raise ValueError("fill price must not be missing")

    price = float(raw_price)
    if not math.isfinite(price):
        raise ValueError("fill price must be finite")
    return price


def fill_order_intent(
    order_intent: OrderIntent,
    price_data: pd.DataFrame,
) -> AssumedFill:
    """Convert one order intent into a deterministic assumed fill."""
    if not isinstance(order_intent, OrderIntent):
        raise ValueError("order_intent must be an OrderIntent")

    _validate_price_data(price_data)
    price_column = _price_column_for_assumptions(order_intent.assumptions)
    fill_timestamp = _select_fill_timestamp(order_intent, price_data)
    price = _read_fill_price(price_data, fill_timestamp, price_column)

    return AssumedFill(
        intent_timestamp=order_intent.timestamp,
        fill_timestamp=fill_timestamp,
        symbol=order_intent.symbol,
        side=order_intent.side,
        quantity=order_intent.quantity,
        price=price,
        price_field=order_intent.assumptions.price_field,
        assumptions=order_intent.assumptions,
    )
