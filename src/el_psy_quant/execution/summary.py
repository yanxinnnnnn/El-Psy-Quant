"""Summaries for deterministic assumed execution activity."""

from collections.abc import Sequence
import math

from el_psy_quant.execution.fills import AssumedFill
from el_psy_quant.execution.orders import SUPPORTED_ORDER_SIDES


def _validate_fills_input(fills: Sequence[AssumedFill]) -> None:
    if isinstance(fills, AssumedFill):
        raise ValueError("fills must be a sequence of AssumedFill objects")
    if isinstance(fills, str):
        raise ValueError("fills must be a sequence of AssumedFill objects")
    if not isinstance(fills, Sequence):
        raise ValueError("fills must be a sequence of AssumedFill objects")
    if not fills:
        raise ValueError("fills must not be empty")


def _increment_ordered_count(counts: dict[str, int], value: str) -> None:
    counts[value] = counts.get(value, 0) + 1


def _validate_fill(fill: object) -> AssumedFill:
    if not isinstance(fill, AssumedFill):
        raise ValueError("fills must contain only AssumedFill objects")
    if fill.side not in SUPPORTED_ORDER_SIDES:
        raise ValueError("fill side must be buy or sell")
    if not math.isfinite(fill.quantity) or fill.quantity <= 0:
        raise ValueError("fill quantity must be positive and finite")
    if not math.isfinite(fill.price):
        raise ValueError("fill price must be finite")
    return fill


def summarize_assumed_fills(
    fills: Sequence[AssumedFill],
) -> dict[str, object]:
    """Summarize already-created assumed fills as JSON-compatible data."""
    _validate_fills_input(fills)

    symbols: list[str] = []
    seen_symbols: set[str] = set()
    price_fields: dict[str, int] = {}
    timings: dict[str, int] = {}

    buy_count = 0
    sell_count = 0
    buy_quantity = 0.0
    sell_quantity = 0.0
    buy_notional = 0.0
    sell_notional = 0.0

    intent_timestamps = []
    fill_timestamps = []

    for item in fills:
        fill = _validate_fill(item)
        if fill.symbol not in seen_symbols:
            seen_symbols.add(fill.symbol)
            symbols.append(fill.symbol)

        _increment_ordered_count(price_fields, fill.price_field)
        _increment_ordered_count(timings, fill.assumptions.timing)

        notional = fill.quantity * fill.price
        if fill.side == "buy":
            buy_count += 1
            buy_quantity += fill.quantity
            buy_notional += notional
        else:
            sell_count += 1
            sell_quantity += fill.quantity
            sell_notional += notional

        intent_timestamps.append(fill.intent_timestamp)
        fill_timestamps.append(fill.fill_timestamp)

    gross_quantity = buy_quantity + sell_quantity
    gross_notional = buy_notional + sell_notional

    return {
        "fill_count": len(fills),
        "symbols": symbols,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "buy_quantity": buy_quantity,
        "sell_quantity": sell_quantity,
        "gross_quantity": gross_quantity,
        "buy_notional": buy_notional,
        "sell_notional": sell_notional,
        "gross_notional": gross_notional,
        "price_fields": price_fields,
        "timings": timings,
        "first_intent_timestamp": min(intent_timestamps).isoformat(),
        "last_intent_timestamp": max(intent_timestamps).isoformat(),
        "first_fill_timestamp": min(fill_timestamps).isoformat(),
        "last_fill_timestamp": max(fill_timestamps).isoformat(),
    }
