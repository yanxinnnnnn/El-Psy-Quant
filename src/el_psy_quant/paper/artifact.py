"""Standalone in-memory paper trading artifacts."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.paper.account import PaperAccountState
from el_psy_quant.paper.fills import PaperFill
from el_psy_quant.paper.orders import PaperOrderLedger, PaperOrderRecord
from el_psy_quant.paper.session import PaperTradingSessionSummary

PAPER_TRADING_ARTIFACT_SCHEMA_VERSION = 1


def _normalize_timestamp(timestamp: object) -> pd.Timestamp:
    try:
        normalized = pd.Timestamp(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("created_timestamp must be convertible to a pandas Timestamp") from exc

    if pd.isna(normalized):
        raise ValueError("created_timestamp must be valid")
    return normalized


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


def _validate_session_summary(
    session_summary: PaperTradingSessionSummary,
) -> PaperTradingSessionSummary:
    if not isinstance(session_summary, PaperTradingSessionSummary):
        raise ValueError("session_summary must be a PaperTradingSessionSummary")
    return session_summary


@dataclass(frozen=True)
class PaperTradingArtifact:
    """Immutable in-memory paper trading artifact boundary."""

    created_timestamp: object
    starting_account_state: PaperAccountState
    ending_account_state: PaperAccountState
    orders: PaperOrderLedger | Sequence[PaperOrderRecord]
    fills: Sequence[PaperFill]
    session_summary: PaperTradingSessionSummary

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_timestamp(self.created_timestamp),
        )
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
        object.__setattr__(
            self,
            "session_summary",
            _validate_session_summary(self.session_summary),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible paper trading artifact export."""
        return {
            "schema_version": PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
            "created_timestamp": self.created_timestamp.isoformat(),
            "starting_account_state": self.starting_account_state.to_dict(),
            "ending_account_state": self.ending_account_state.to_dict(),
            "orders": [order.to_dict() for order in self.orders],
            "fills": [fill.to_dict() for fill in self.fills],
            "session_summary": self.session_summary.to_dict(),
        }


def create_paper_trading_artifact(
    *,
    created_timestamp: object,
    starting_account_state: PaperAccountState,
    ending_account_state: PaperAccountState,
    orders: PaperOrderLedger | Sequence[PaperOrderRecord],
    fills: Sequence[PaperFill],
    session_summary: PaperTradingSessionSummary,
) -> PaperTradingArtifact:
    """Create and validate one standalone in-memory paper trading artifact."""
    return PaperTradingArtifact(
        created_timestamp=created_timestamp,
        starting_account_state=starting_account_state,
        ending_account_state=ending_account_state,
        orders=orders,
        fills=fills,
        session_summary=session_summary,
    )
