"""Deterministic consumed-trade execution-price evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from el_psy_quant.market_time import MarketDataEvent
from el_psy_quant.paper_account import PaperMoney
from el_psy_quant.paper_execution._arithmetic import (
    PAPER_EXECUTION_MONEY_QUANTUM,
    PAPER_EXECUTION_ROUNDING_MODE,
    add,
    canonical_decimal,
    divide,
    exact_money,
    multiply,
    round_money,
    subtract,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.market_events import (
    PaperExecutionEventReference,
    _clone_event_reference,
    validate_paper_execution_event_reference,
)
from el_psy_quant.paper_execution.policies import (
    EXECUTION_PRICE_POLICY_ID,
    SLIPPAGE_POLICY_ID,
    PaperExecutionBasisPoints,
    PaperExecutionPolicyReference,
    validate_paper_execution_policy_reference,
)

PAPER_EXECUTION_PRICE_EVIDENCE_SCHEMA_VERSION = 1


def _exact_bps(value: object) -> PaperExecutionBasisPoints:
    if type(value) is not PaperExecutionBasisPoints:
        raise ValueError("slippage_bps must be PaperExecutionBasisPoints")
    try:
        rebuilt = PaperExecutionBasisPoints.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError("slippage_bps is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError("slippage_bps is invalid")
    return rebuilt


def _payload(
    *,
    schema_version: int,
    execution_price_policy_id: str,
    execution_event_reference: PaperExecutionEventReference,
    side: str,
    base_trade_price: PaperMoney,
    slippage_policy_id: str,
    slippage_bps: PaperExecutionBasisPoints,
    pre_round_execution_price: str,
    execution_price: PaperMoney,
    rounding_quantum: str,
    rounding_mode: str,
    rounding_applied: bool,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "execution_price_policy_id": execution_price_policy_id,
        "execution_event_reference": execution_event_reference.to_dict(),
        "side": side,
        "base_trade_price": base_trade_price.to_json_value(),
        "slippage_policy_id": slippage_policy_id,
        "slippage_bps": slippage_bps.to_json_value(),
        "pre_round_execution_price": pre_round_execution_price,
        "execution_price": execution_price.to_json_value(),
        "rounding_quantum": rounding_quantum,
        "rounding_mode": rounding_mode,
        "rounding_applied": rounding_applied,
    }


@dataclass(frozen=True, init=False)
class PaperExecutionPriceEvidence:
    """Exact base event price, slippage, and final rounded execution price."""

    schema_version: int
    execution_price_policy_id: str
    execution_event_reference: PaperExecutionEventReference
    side: str
    base_trade_price: PaperMoney
    slippage_policy_id: str
    slippage_bps: PaperExecutionBasisPoints
    pre_round_execution_price: str
    execution_price: PaperMoney
    rounding_quantum: str
    rounding_mode: str
    rounding_applied: bool
    price_evidence_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                execution_price_policy_id=self.execution_price_policy_id,
                execution_event_reference=self.execution_event_reference,
                side=self.side,
                base_trade_price=self.base_trade_price,
                slippage_policy_id=self.slippage_policy_id,
                slippage_bps=self.slippage_bps,
                pre_round_execution_price=self.pre_round_execution_price,
                execution_price=self.execution_price,
                rounding_quantum=self.rounding_quantum,
                rounding_mode=self.rounding_mode,
                rounding_applied=self.rounding_applied,
            ),
            "price_evidence_digest": self.price_evidence_digest,
        }


def _derive_values(
    *,
    base_trade_price: PaperMoney,
    side: str,
    slippage_bps: PaperExecutionBasisPoints,
) -> tuple[str, PaperMoney, bool]:
    base = base_trade_price.decimal_value
    slip = divide(slippage_bps.decimal_value, Decimal("10000"))
    factor = (
        add(Decimal("1"), slip)
        if side == "buy"
        else subtract(Decimal("1"), slip)
    )
    pre_round = multiply(base, factor)
    execution_price, rounding_applied = round_money(pre_round)
    if execution_price.decimal_value <= 0:
        raise ValueError("execution price must remain strictly positive")
    return canonical_decimal(pre_round), execution_price, rounding_applied


def _build(
    *,
    execution_event_reference: PaperExecutionEventReference,
    side: str,
    base_trade_price: PaperMoney,
    slippage_bps: PaperExecutionBasisPoints,
) -> PaperExecutionPriceEvidence:
    event_reference = _clone_event_reference(execution_event_reference)
    base = PaperMoney.parse(base_trade_price.canonical)
    slip = PaperExecutionBasisPoints.parse(slippage_bps.canonical)
    pre_round, execution_price, rounding_applied = _derive_values(
        base_trade_price=base,
        side=side,
        slippage_bps=slip,
    )
    payload = _payload(
        schema_version=PAPER_EXECUTION_PRICE_EVIDENCE_SCHEMA_VERSION,
        execution_price_policy_id=EXECUTION_PRICE_POLICY_ID,
        execution_event_reference=event_reference,
        side=side,
        base_trade_price=base,
        slippage_policy_id=SLIPPAGE_POLICY_ID,
        slippage_bps=slip,
        pre_round_execution_price=pre_round,
        execution_price=execution_price,
        rounding_quantum=canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM),
        rounding_mode=PAPER_EXECUTION_ROUNDING_MODE,
        rounding_applied=rounding_applied,
    )
    result = object.__new__(PaperExecutionPriceEvidence)
    values = {
        "schema_version": PAPER_EXECUTION_PRICE_EVIDENCE_SCHEMA_VERSION,
        "execution_price_policy_id": EXECUTION_PRICE_POLICY_ID,
        "execution_event_reference": event_reference,
        "side": side,
        "base_trade_price": base,
        "slippage_policy_id": SLIPPAGE_POLICY_ID,
        "slippage_bps": slip,
        "pre_round_execution_price": pre_round,
        "execution_price": execution_price,
        "rounding_quantum": canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM),
        "rounding_mode": PAPER_EXECUTION_ROUNDING_MODE,
        "rounding_applied": rounding_applied,
        "price_evidence_digest": canonical_digest(payload),
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def extract_supported_trade_price(event: MarketDataEvent) -> PaperMoney | None:
    """Return an exact positive M31-money price or classify it as invalid."""
    if type(event) is not MarketDataEvent or event.event_type != "trade":
        return None
    try:
        serialized = json.loads(
            event.to_json(),
            parse_float=Decimal,
            parse_int=Decimal,
        )
        value = serialized["payload"].get("price")
        if type(value) is not Decimal or not value.is_finite() or value <= 0:
            return None
        canonical = canonical_decimal(value)
        price = PaperMoney.parse(canonical)
        if price.decimal_value != value:
            return None
        return price
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def create_paper_execution_price_evidence(
    *,
    event: MarketDataEvent,
    execution_event_reference: PaperExecutionEventReference,
    side: str,
    execution_policy_reference: PaperExecutionPolicyReference,
) -> PaperExecutionPriceEvidence:
    """Derive M34 execution price only from one exact consumed trade event."""
    reference = validate_paper_execution_event_reference(
        execution_event_reference
    )
    policy = validate_paper_execution_policy_reference(
        execution_policy_reference
    )
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if type(event) is not MarketDataEvent:
        raise ValueError("event must be MarketDataEvent")
    if not (
        reference.event_id == event.event_id
        and reference.event_digest == canonical_digest(event.to_dict())
        and reference.event_time == event.event_time
        and reference.instrument_id == event.instrument_id
        and reference.event_type == event.event_type
    ):
        raise ValueError("execution event reference does not match event")
    base = extract_supported_trade_price(event)
    if base is None:
        raise ValueError("trade event price is not an exact supported price")
    return _build(
        execution_event_reference=reference,
        side=side,
        base_trade_price=base,
        slippage_bps=policy.slippage_bps,
    )


def validate_paper_execution_price_evidence(
    value: object,
) -> PaperExecutionPriceEvidence:
    if type(value) is not PaperExecutionPriceEvidence:
        raise ValueError("price evidence must be PaperExecutionPriceEvidence")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_PRICE_EVIDENCE_SCHEMA_VERSION
            or value.execution_price_policy_id != EXECUTION_PRICE_POLICY_ID
            or value.slippage_policy_id != SLIPPAGE_POLICY_ID
            or value.side not in {"buy", "sell"}
            or value.rounding_quantum
            != canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM)
            or value.rounding_mode != PAPER_EXECUTION_ROUNDING_MODE
            or type(value.rounding_applied) is not bool
        ):
            raise ValueError("price evidence metadata is invalid")
        validate_paper_execution_event_reference(value.execution_event_reference)
        base = exact_money(value.base_trade_price, field_name="base_trade_price")
        if base.decimal_value <= 0:
            raise ValueError("base trade price must be positive")
        slip = _exact_bps(value.slippage_bps)
        expected = _build(
            execution_event_reference=value.execution_event_reference,
            side=value.side,
            base_trade_price=base,
            slippage_bps=slip,
        )
        validate_digest(
            value.price_evidence_digest,
            field_name="price_evidence_digest",
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution price evidence is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution price evidence is invalid")
    return value


def _clone_price_evidence(
    value: PaperExecutionPriceEvidence,
) -> PaperExecutionPriceEvidence:
    validate_paper_execution_price_evidence(value)
    return _build(
        execution_event_reference=value.execution_event_reference,
        side=value.side,
        base_trade_price=value.base_trade_price,
        slippage_bps=value.slippage_bps,
    )
