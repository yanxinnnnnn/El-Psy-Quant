"""Immutable paper run request contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.paper.account import PaperAccountState
from el_psy_quant.paper.fills import PaperFill
from el_psy_quant.paper.orders import (
    PaperOrderLedger,
    PaperOrderRecord,
    create_paper_order_ledger,
)


def _normalize_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    return run_id.strip()


def _normalize_created_timestamp(created_timestamp: object) -> pd.Timestamp:
    try:
        normalized = pd.Timestamp(created_timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "created_timestamp must be convertible to a pandas Timestamp"
        ) from exc

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
            "orders must be a PaperOrderLedger or a sequence of PaperOrderRecord "
            "objects"
        )
    if isinstance(orders, str) or not isinstance(orders, Sequence):
        raise ValueError(
            "orders must be a PaperOrderLedger or a sequence of PaperOrderRecord "
            "objects"
        )
    return tuple(create_paper_order_ledger(orders).orders)


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


@dataclass(frozen=True)
class PaperRunRequest:
    """Immutable explicit request for one local paper run."""

    run_id: str
    created_timestamp: object
    starting_account_state: PaperAccountState
    ending_account_state: PaperAccountState
    orders: PaperOrderLedger | Sequence[PaperOrderRecord]
    fills: Sequence[PaperFill]

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _normalize_run_id(self.run_id))
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_created_timestamp(self.created_timestamp),
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

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible paper run request export."""
        return {
            "run_id": self.run_id,
            "created_timestamp": self.created_timestamp.isoformat(),
            "starting_account_state": self.starting_account_state.to_dict(),
            "ending_account_state": self.ending_account_state.to_dict(),
            "orders": [order.to_dict() for order in self.orders],
            "fills": [fill.to_dict() for fill in self.fills],
        }


def create_paper_run_request(
    *,
    run_id: str,
    created_timestamp: object,
    starting_account_state: PaperAccountState,
    ending_account_state: PaperAccountState,
    orders: PaperOrderLedger | Sequence[PaperOrderRecord],
    fills: Sequence[PaperFill],
) -> PaperRunRequest:
    """Create and validate one explicit local paper run request."""
    return PaperRunRequest(
        run_id=run_id,
        created_timestamp=created_timestamp,
        starting_account_state=starting_account_state,
        ending_account_state=ending_account_state,
        orders=orders,
        fills=fills,
    )
