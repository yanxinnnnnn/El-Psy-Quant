"""Deterministic local paper trading session summaries."""

from collections.abc import Sequence
from dataclasses import dataclass

from el_psy_quant.paper.account import PaperAccountState
from el_psy_quant.paper.fills import PaperFill
from el_psy_quant.paper.orders import PaperOrderLedger, PaperOrderRecord


def _validate_account_state(
    account_state: PaperAccountState,
    *,
    field_name: str,
) -> PaperAccountState:
    if not isinstance(account_state, PaperAccountState):
        raise ValueError(f"{field_name} must be a PaperAccountState")
    return account_state


def _normalize_orders(
    orders: PaperOrderLedger | Sequence[PaperOrderRecord],
) -> tuple[PaperOrderRecord, ...]:
    if isinstance(orders, PaperOrderLedger):
        return tuple(orders.orders)
    if isinstance(orders, PaperOrderRecord):
        raise ValueError(
            "orders must be a PaperOrderLedger or a sequence of PaperOrderRecord objects"
        )
    if isinstance(orders, str) or not isinstance(orders, Sequence):
        raise ValueError(
            "orders must be a PaperOrderLedger or a sequence of PaperOrderRecord objects"
        )

    normalized_orders: list[PaperOrderRecord] = []
    for order in orders:
        if not isinstance(order, PaperOrderRecord):
            raise ValueError("orders must contain only PaperOrderRecord objects")
        normalized_orders.append(order)
    return tuple(normalized_orders)


def _normalize_fills(fills: Sequence[PaperFill]) -> tuple[PaperFill, ...]:
    if isinstance(fills, PaperFill):
        raise ValueError("fills must be a sequence of PaperFill objects")
    if isinstance(fills, str) or not isinstance(fills, Sequence):
        raise ValueError("fills must be a sequence of PaperFill objects")

    normalized_fills: list[PaperFill] = []
    for fill in fills:
        if not isinstance(fill, PaperFill):
            raise ValueError("fills must contain only PaperFill objects")
        normalized_fills.append(fill)
    return tuple(normalized_fills)


def _positions_to_records(
    positions: Sequence[tuple[str, float]],
) -> list[dict[str, object]]:
    return [
        {"symbol": symbol, "quantity": quantity}
        for symbol, quantity in positions
    ]


def _position_changes(
    starting_positions: Sequence[tuple[str, float]],
    ending_positions: Sequence[tuple[str, float]],
) -> list[dict[str, object]]:
    starting_by_symbol = dict(starting_positions)
    ending_by_symbol = dict(ending_positions)
    symbols = sorted(starting_by_symbol.keys() | ending_by_symbol.keys())

    return [
        {
            "symbol": symbol,
            "starting_quantity": starting_by_symbol.get(symbol, 0.0),
            "ending_quantity": ending_by_symbol.get(symbol, 0.0),
            "quantity_change": (
                ending_by_symbol.get(symbol, 0.0)
                - starting_by_symbol.get(symbol, 0.0)
            ),
        }
        for symbol in symbols
    ]


@dataclass(frozen=True)
class PaperTradingSessionSummary:
    """Immutable local paper trading session summary boundary."""

    starting_account_state: PaperAccountState
    ending_account_state: PaperAccountState
    orders: PaperOrderLedger | Sequence[PaperOrderRecord]
    fills: Sequence[PaperFill]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "starting_account_state",
            _validate_account_state(
                self.starting_account_state,
                field_name="starting_account_state",
            ),
        )
        object.__setattr__(
            self,
            "ending_account_state",
            _validate_account_state(
                self.ending_account_state,
                field_name="ending_account_state",
            ),
        )
        object.__setattr__(self, "orders", _normalize_orders(self.orders))
        object.__setattr__(self, "fills", _normalize_fills(self.fills))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible session summary export."""
        starting_positions = self.starting_account_state.positions
        ending_positions = self.ending_account_state.positions

        return {
            "session_start_timestamp": (
                self.starting_account_state.timestamp.isoformat()
            ),
            "session_end_timestamp": (
                self.ending_account_state.timestamp.isoformat()
            ),
            "starting_cash": self.starting_account_state.current_cash,
            "ending_cash": self.ending_account_state.current_cash,
            "cash_change": (
                self.ending_account_state.current_cash
                - self.starting_account_state.current_cash
            ),
            "starting_positions": _positions_to_records(starting_positions),
            "ending_positions": _positions_to_records(ending_positions),
            "position_changes": _position_changes(
                starting_positions,
                ending_positions,
            ),
            "order_count": len(self.orders),
            "fill_count": len(self.fills),
        }


def create_paper_trading_session_summary(
    *,
    starting_account_state: PaperAccountState,
    ending_account_state: PaperAccountState,
    orders: PaperOrderLedger | Sequence[PaperOrderRecord],
    fills: Sequence[PaperFill],
) -> PaperTradingSessionSummary:
    """Create and validate one local paper trading session summary."""
    return PaperTradingSessionSummary(
        starting_account_state=starting_account_state,
        ending_account_state=ending_account_state,
        orders=orders,
        fills=fills,
    )
