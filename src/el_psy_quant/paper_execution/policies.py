"""Exact versioned Paper execution configuration contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)

PAPER_EXECUTION_BASIS_POINTS_SCHEMA_VERSION = 1
PAPER_EXECUTION_POLICY_SCHEMA_VERSION = 1

PAPER_EXECUTION_POLICY_ID = "paper_execution_v1"
EXECUTION_PRICE_POLICY_ID = "consumed_trade_event_price_v1"
SLIPPAGE_POLICY_ID = "fixed_bps_slippage_v1"
TRANSACTION_COST_POLICY_ID = "per_fill_bps_costs_v1"

_BASIS_POINTS_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")


@dataclass(frozen=True, init=False)
class PaperExecutionBasisPoints:
    """An exact non-negative v1 basis-points configuration value."""

    _decimal_value: Decimal
    _canonical: str

    __init__ = reject_public_construction

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse one already-canonical fixed-point basis-points string."""
        if not isinstance(value, str) or isinstance(value, bool):
            raise ValueError("basis points must be a canonical decimal string")
        if _BASIS_POINTS_PATTERN.fullmatch(value) is None:
            raise ValueError("basis points must be a canonical decimal string")
        _, separator, fractional = value.partition(".")
        if separator and len(fractional) > 8:
            raise ValueError("basis points support at most 8 fractional digits")
        decimal_value = Decimal(value)
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ValueError("basis points must be finite and non-negative")
        if decimal_value >= Decimal("10000"):
            raise ValueError("basis points must be strictly less than 10000")
        result = object.__new__(cls)
        object.__setattr__(result, "_decimal_value", decimal_value)
        object.__setattr__(result, "_canonical", value)
        return result

    @property
    def decimal_value(self) -> Decimal:
        return self._decimal_value

    @property
    def canonical(self) -> str:
        return self._canonical

    def to_json_value(self) -> str:
        return self._canonical

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_EXECUTION_BASIS_POINTS_SCHEMA_VERSION,
            "value": self._canonical,
        }

    def __str__(self) -> str:
        return self._canonical


def _exact_bps(
    value: object,
    *,
    field_name: str,
) -> PaperExecutionBasisPoints:
    if type(value) is not PaperExecutionBasisPoints:
        raise ValueError(f"{field_name} must be PaperExecutionBasisPoints")
    try:
        rebuilt = PaperExecutionBasisPoints.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is invalid")
    return rebuilt


def _exact_positive_quantity(
    value: object,
    *,
    field_name: str,
) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity or None")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
        or rebuilt.decimal_value <= 0
    ):
        raise ValueError(f"{field_name} must be strictly positive")
    return rebuilt


def _configuration_payload(
    *,
    max_fill_quantity_per_trade_event: PaperQuantity | None,
    slippage_bps: PaperExecutionBasisPoints,
    commission_bps: PaperExecutionBasisPoints,
    fee_bps: PaperExecutionBasisPoints,
    buy_tax_bps: PaperExecutionBasisPoints,
    sell_tax_bps: PaperExecutionBasisPoints,
) -> dict[str, object]:
    return {
        "max_fill_quantity_per_trade_event": (
            None
            if max_fill_quantity_per_trade_event is None
            else max_fill_quantity_per_trade_event.to_json_value()
        ),
        "slippage_bps": slippage_bps.to_json_value(),
        "commission_bps": commission_bps.to_json_value(),
        "fee_bps": fee_bps.to_json_value(),
        "buy_tax_bps": buy_tax_bps.to_json_value(),
        "sell_tax_bps": sell_tax_bps.to_json_value(),
    }


def _reference_payload_without_digest(
    *,
    schema_version: int,
    policy_id: str,
    execution_price_policy_id: str,
    max_fill_quantity_per_trade_event: PaperQuantity | None,
    slippage_policy_id: str,
    slippage_bps: PaperExecutionBasisPoints,
    transaction_cost_policy_id: str,
    commission_bps: PaperExecutionBasisPoints,
    fee_bps: PaperExecutionBasisPoints,
    buy_tax_bps: PaperExecutionBasisPoints,
    sell_tax_bps: PaperExecutionBasisPoints,
    configuration_digest: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_id": policy_id,
        "execution_price_policy_id": execution_price_policy_id,
        **_configuration_payload(
            max_fill_quantity_per_trade_event=(max_fill_quantity_per_trade_event),
            slippage_bps=slippage_bps,
            commission_bps=commission_bps,
            fee_bps=fee_bps,
            buy_tax_bps=buy_tax_bps,
            sell_tax_bps=sell_tax_bps,
        ),
        "slippage_policy_id": slippage_policy_id,
        "transaction_cost_policy_id": transaction_cost_policy_id,
        "configuration_digest": configuration_digest,
    }


@dataclass(frozen=True, init=False)
class PaperExecutionPolicyReference:
    """One immutable explicit v1 Paper execution-policy selection."""

    schema_version: int
    policy_id: str
    execution_price_policy_id: str
    max_fill_quantity_per_trade_event: PaperQuantity | None
    slippage_policy_id: str
    slippage_bps: PaperExecutionBasisPoints
    transaction_cost_policy_id: str
    commission_bps: PaperExecutionBasisPoints
    fee_bps: PaperExecutionBasisPoints
    buy_tax_bps: PaperExecutionBasisPoints
    sell_tax_bps: PaperExecutionBasisPoints
    configuration_digest: str
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_reference_payload_without_digest(
                schema_version=self.schema_version,
                policy_id=self.policy_id,
                execution_price_policy_id=self.execution_price_policy_id,
                max_fill_quantity_per_trade_event=(
                    self.max_fill_quantity_per_trade_event
                ),
                slippage_policy_id=self.slippage_policy_id,
                slippage_bps=self.slippage_bps,
                transaction_cost_policy_id=(self.transaction_cost_policy_id),
                commission_bps=self.commission_bps,
                fee_bps=self.fee_bps,
                buy_tax_bps=self.buy_tax_bps,
                sell_tax_bps=self.sell_tax_bps,
                configuration_digest=self.configuration_digest,
            ),
            "reference_digest": self.reference_digest,
        }


def _build_policy_reference(
    *,
    schema_version: int,
    max_fill_quantity_per_trade_event: PaperQuantity | None,
    slippage_bps: PaperExecutionBasisPoints,
    commission_bps: PaperExecutionBasisPoints,
    fee_bps: PaperExecutionBasisPoints,
    buy_tax_bps: PaperExecutionBasisPoints,
    sell_tax_bps: PaperExecutionBasisPoints,
) -> PaperExecutionPolicyReference:
    cap = (
        None
        if max_fill_quantity_per_trade_event is None
        else PaperQuantity.parse(max_fill_quantity_per_trade_event.canonical)
    )
    copied_bps = tuple(
        PaperExecutionBasisPoints.parse(value.canonical)
        for value in (
            slippage_bps,
            commission_bps,
            fee_bps,
            buy_tax_bps,
            sell_tax_bps,
        )
    )
    slip, commission, fee, buy_tax, sell_tax = copied_bps
    configuration_digest = canonical_digest(
        _configuration_payload(
            max_fill_quantity_per_trade_event=cap,
            slippage_bps=slip,
            commission_bps=commission,
            fee_bps=fee,
            buy_tax_bps=buy_tax,
            sell_tax_bps=sell_tax,
        )
    )
    payload = _reference_payload_without_digest(
        schema_version=schema_version,
        policy_id=PAPER_EXECUTION_POLICY_ID,
        execution_price_policy_id=EXECUTION_PRICE_POLICY_ID,
        max_fill_quantity_per_trade_event=cap,
        slippage_policy_id=SLIPPAGE_POLICY_ID,
        slippage_bps=slip,
        transaction_cost_policy_id=TRANSACTION_COST_POLICY_ID,
        commission_bps=commission,
        fee_bps=fee,
        buy_tax_bps=buy_tax,
        sell_tax_bps=sell_tax,
        configuration_digest=configuration_digest,
    )
    result = object.__new__(PaperExecutionPolicyReference)
    for field_name, value in (
        ("schema_version", schema_version),
        ("policy_id", PAPER_EXECUTION_POLICY_ID),
        ("execution_price_policy_id", EXECUTION_PRICE_POLICY_ID),
        ("max_fill_quantity_per_trade_event", cap),
        ("slippage_policy_id", SLIPPAGE_POLICY_ID),
        ("slippage_bps", slip),
        ("transaction_cost_policy_id", TRANSACTION_COST_POLICY_ID),
        ("commission_bps", commission),
        ("fee_bps", fee),
        ("buy_tax_bps", buy_tax),
        ("sell_tax_bps", sell_tax),
        ("configuration_digest", configuration_digest),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_policy_reference(
    *,
    max_fill_quantity_per_trade_event: PaperQuantity | None,
    slippage_bps: PaperExecutionBasisPoints,
    commission_bps: PaperExecutionBasisPoints,
    fee_bps: PaperExecutionBasisPoints,
    buy_tax_bps: PaperExecutionBasisPoints,
    sell_tax_bps: PaperExecutionBasisPoints,
    schema_version: int = PAPER_EXECUTION_POLICY_SCHEMA_VERSION,
) -> PaperExecutionPolicyReference:
    """Create one policy reference without performing execution arithmetic."""
    if (
        type(schema_version) is not int
        or schema_version != PAPER_EXECUTION_POLICY_SCHEMA_VERSION
    ):
        raise ValueError("unsupported paper execution policy schema_version")
    cap = (
        None
        if max_fill_quantity_per_trade_event is None
        else _exact_positive_quantity(
            max_fill_quantity_per_trade_event,
            field_name="max_fill_quantity_per_trade_event",
        )
    )
    return _build_policy_reference(
        schema_version=schema_version,
        max_fill_quantity_per_trade_event=cap,
        slippage_bps=_exact_bps(slippage_bps, field_name="slippage_bps"),
        commission_bps=_exact_bps(
            commission_bps,
            field_name="commission_bps",
        ),
        fee_bps=_exact_bps(fee_bps, field_name="fee_bps"),
        buy_tax_bps=_exact_bps(buy_tax_bps, field_name="buy_tax_bps"),
        sell_tax_bps=_exact_bps(sell_tax_bps, field_name="sell_tax_bps"),
    )


def validate_paper_execution_policy_reference(
    value: object,
) -> PaperExecutionPolicyReference:
    """Recompute and verify one complete v1 execution policy reference."""
    if type(value) is not PaperExecutionPolicyReference:
        raise ValueError(
            "execution_policy_reference must be a PaperExecutionPolicyReference"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_POLICY_SCHEMA_VERSION
        ):
            raise ValueError("unsupported execution policy schema_version")
        if value.policy_id != PAPER_EXECUTION_POLICY_ID:
            raise ValueError("unsupported execution policy ID")
        if value.execution_price_policy_id != EXECUTION_PRICE_POLICY_ID:
            raise ValueError("unsupported execution price policy ID")
        if value.slippage_policy_id != SLIPPAGE_POLICY_ID:
            raise ValueError("unsupported slippage policy ID")
        if value.transaction_cost_policy_id != TRANSACTION_COST_POLICY_ID:
            raise ValueError("unsupported transaction cost policy ID")
        cap = (
            None
            if value.max_fill_quantity_per_trade_event is None
            else _exact_positive_quantity(
                value.max_fill_quantity_per_trade_event,
                field_name="max_fill_quantity_per_trade_event",
            )
        )
        slip = _exact_bps(value.slippage_bps, field_name="slippage_bps")
        commission = _exact_bps(
            value.commission_bps,
            field_name="commission_bps",
        )
        fee = _exact_bps(value.fee_bps, field_name="fee_bps")
        buy_tax = _exact_bps(value.buy_tax_bps, field_name="buy_tax_bps")
        sell_tax = _exact_bps(
            value.sell_tax_bps,
            field_name="sell_tax_bps",
        )
        validate_digest(
            value.configuration_digest,
            field_name="configuration_digest",
        )
        validate_digest(value.reference_digest, field_name="reference_digest")
        rebuilt = _build_policy_reference(
            schema_version=value.schema_version,
            max_fill_quantity_per_trade_event=cap,
            slippage_bps=slip,
            commission_bps=commission,
            fee_bps=fee,
            buy_tax_bps=buy_tax,
            sell_tax_bps=sell_tax,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution policy reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("paper execution policy reference is invalid")
    return value


def _clone_policy_reference(
    value: PaperExecutionPolicyReference,
) -> PaperExecutionPolicyReference:
    validate_paper_execution_policy_reference(value)
    return _build_policy_reference(
        schema_version=value.schema_version,
        max_fill_quantity_per_trade_event=(value.max_fill_quantity_per_trade_event),
        slippage_bps=value.slippage_bps,
        commission_bps=value.commission_bps,
        fee_bps=value.fee_bps,
        buy_tax_bps=value.buy_tax_bps,
        sell_tax_bps=value.sell_tax_bps,
    )
