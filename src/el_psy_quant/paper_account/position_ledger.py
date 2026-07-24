"""Immutable Paper Account position ledger entries."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
)
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.identity import MAX_PAPER_ACCOUNT_ID_LENGTH
from el_psy_quant.paper_account.position_commands import (
    MAX_PAPER_POSITION_SYMBOL_LENGTH,
    SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES,
    PaperPositionAdjustmentCategory,
    _normalize_position_symbol,
)

PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION = 1
MAX_PAPER_POSITION_ENTRY_ID_LENGTH = 512


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(
        "position ledger entries are created by trusted event factories"
    )


@dataclass(frozen=True, init=False)
class PaperPositionLedgerEntry:
    """One immutable position posting owned by one account event."""

    position_entry_id: str
    account_id: str
    event_id: str
    entry_index: int
    symbol: str
    signed_quantity_delta: PaperQuantity
    signed_cost_basis_delta: PaperMoney
    adjustment_category: PaperPositionAdjustmentCategory
    entry_digest: str

    __init__ = _reject_public_construction

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_POSITION_LEDGER_ENTRY_SCHEMA_VERSION,
            "position_entry_id": self.position_entry_id,
            "account_id": self.account_id,
            "event_id": self.event_id,
            "entry_index": self.entry_index,
            "symbol": self.symbol,
            "signed_quantity_delta": (
                self.signed_quantity_delta.to_json_value()
            ),
            "signed_cost_basis_delta": (
                self.signed_cost_basis_delta.to_json_value()
            ),
            "adjustment_category": self.adjustment_category,
        }

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible posting."""
        payload = self._payload_without_digest()
        payload["entry_digest"] = self.entry_digest
        return payload


def _create_position_ledger_entry(
    *,
    position_entry_id: str,
    account_id: str,
    event_id: str,
    symbol: str,
    signed_quantity_delta: PaperQuantity,
    signed_cost_basis_delta: PaperMoney,
    adjustment_category: PaperPositionAdjustmentCategory,
) -> PaperPositionLedgerEntry:
    entry_id = normalize_bounded_string(
        position_entry_id,
        field_name="position_entry_id",
        maximum_length=MAX_PAPER_POSITION_ENTRY_ID_LENGTH,
    )
    normalized_account_id = normalize_bounded_string(
        account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    normalized_event_id = normalize_bounded_string(
        event_id,
        field_name="event_id",
        maximum_length=MAX_PAPER_POSITION_ENTRY_ID_LENGTH,
    )
    normalized_symbol = _normalize_position_symbol(symbol)
    if normalized_symbol != symbol:
        raise ValueError("position entry symbol must already be normalized")
    if len(normalized_symbol) > MAX_PAPER_POSITION_SYMBOL_LENGTH:
        raise ValueError("position entry symbol is too long")
    if adjustment_category not in (
        SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES
    ):
        raise ValueError("unsupported position adjustment category")
    if type(signed_quantity_delta) is not PaperQuantity:
        raise ValueError("signed_quantity_delta must be PaperQuantity")
    if type(signed_cost_basis_delta) is not PaperMoney:
        raise ValueError("signed_cost_basis_delta must be PaperMoney")
    if (
        signed_quantity_delta.decimal_value == 0
        and signed_cost_basis_delta.decimal_value == 0
    ):
        raise ValueError(
            "at least one position ledger delta must be non-zero"
        )

    result = object.__new__(PaperPositionLedgerEntry)
    object.__setattr__(result, "position_entry_id", entry_id)
    object.__setattr__(result, "account_id", normalized_account_id)
    object.__setattr__(result, "event_id", normalized_event_id)
    object.__setattr__(result, "entry_index", 0)
    object.__setattr__(result, "symbol", normalized_symbol)
    object.__setattr__(
        result,
        "signed_quantity_delta",
        signed_quantity_delta,
    )
    object.__setattr__(
        result,
        "signed_cost_basis_delta",
        signed_cost_basis_delta,
    )
    object.__setattr__(
        result,
        "adjustment_category",
        adjustment_category,
    )
    object.__setattr__(
        result,
        "entry_digest",
        canonical_digest(result._payload_without_digest()),
    )
    return result
