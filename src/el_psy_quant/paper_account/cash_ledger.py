"""Immutable Paper Account cash ledger entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    normalize_bounded_string,
)
from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.identity import MAX_PAPER_ACCOUNT_ID_LENGTH

PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION = 1
MAX_PAPER_CASH_ENTRY_ID_LENGTH = 512

PaperCashMovementType = Literal[
    "initial_cash",
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
]

SUPPORTED_PAPER_CASH_LEDGER_MOVEMENT_TYPES = (
    "initial_cash",
    "deposit",
    "withdrawal",
    "manual_adjustment",
    "fee",
    "commission",
    "tax",
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError("cash ledger entries are created by trusted event factories")


@dataclass(frozen=True, init=False)
class PaperCashLedgerEntry:
    """One immutable exact cash posting owned by one account event."""

    cash_entry_id: str
    account_id: str
    event_id: str
    entry_index: int
    movement_type: PaperCashMovementType
    currency: str
    signed_amount: PaperMoney
    entry_digest: str

    __init__ = _reject_public_construction

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_CASH_LEDGER_ENTRY_SCHEMA_VERSION,
            "cash_entry_id": self.cash_entry_id,
            "account_id": self.account_id,
            "event_id": self.event_id,
            "entry_index": self.entry_index,
            "movement_type": self.movement_type,
            "currency": self.currency,
            "signed_amount": self.signed_amount.to_json_value(),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible posting."""
        payload = self._payload_without_digest()
        payload["entry_digest"] = self.entry_digest
        return payload


def _create_cash_ledger_entry(
    *,
    cash_entry_id: str,
    account_id: str,
    event_id: str,
    movement_type: PaperCashMovementType,
    currency: str,
    signed_amount: PaperMoney,
) -> PaperCashLedgerEntry:
    entry_id = normalize_bounded_string(
        cash_entry_id,
        field_name="cash_entry_id",
        maximum_length=MAX_PAPER_CASH_ENTRY_ID_LENGTH,
    )
    normalized_account_id = normalize_bounded_string(
        account_id,
        field_name="account_id",
        maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
    )
    normalized_event_id = normalize_bounded_string(
        event_id,
        field_name="event_id",
        maximum_length=MAX_PAPER_CASH_ENTRY_ID_LENGTH,
    )
    if movement_type not in SUPPORTED_PAPER_CASH_LEDGER_MOVEMENT_TYPES:
        raise ValueError("unsupported cash ledger movement type")
    if (
        not isinstance(currency, str)
        or len(currency) != 3
        or any(character < "A" or character > "Z" for character in currency)
    ):
        raise ValueError("currency must contain three uppercase ASCII letters")
    if type(signed_amount) is not PaperMoney:
        raise ValueError("signed_amount must be PaperMoney")

    result = object.__new__(PaperCashLedgerEntry)
    object.__setattr__(result, "cash_entry_id", entry_id)
    object.__setattr__(result, "account_id", normalized_account_id)
    object.__setattr__(result, "event_id", normalized_event_id)
    object.__setattr__(result, "entry_index", 0)
    object.__setattr__(result, "movement_type", movement_type)
    object.__setattr__(result, "currency", currency)
    object.__setattr__(result, "signed_amount", signed_amount)
    object.__setattr__(
        result,
        "entry_digest",
        canonical_digest(result._payload_without_digest()),
    )
    return result
