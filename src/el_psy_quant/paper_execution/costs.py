"""Deterministic per-fill commission, fee, and tax evidence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.paper_execution._arithmetic import (
    PAPER_EXECUTION_MONEY_QUANTUM,
    PAPER_EXECUTION_ROUNDING_MODE,
    add,
    canonical_decimal,
    divide,
    exact_money,
    exact_quantity,
    multiply,
    round_money,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.policies import (
    TRANSACTION_COST_POLICY_ID,
    PaperExecutionBasisPoints,
    PaperExecutionPolicyReference,
    validate_paper_execution_policy_reference,
)
from el_psy_quant.paper_execution.pricing import (
    PaperExecutionPriceEvidence,
    _clone_price_evidence,
    validate_paper_execution_price_evidence,
)

PAPER_EXECUTION_COST_EVIDENCE_SCHEMA_VERSION = 1


def _exact_bps(value: object, *, field_name: str) -> PaperExecutionBasisPoints:
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


def _payload(
    *,
    schema_version: int,
    transaction_cost_policy_id: str,
    execution_price_evidence: PaperExecutionPriceEvidence,
    fill_quantity: PaperQuantity,
    gross_notional_pre_round: str,
    gross_notional: PaperMoney,
    gross_notional_rounding_applied: bool,
    commission_bps: PaperExecutionBasisPoints,
    commission_pre_round: str,
    commission: PaperMoney,
    commission_rounding_applied: bool,
    fee_bps: PaperExecutionBasisPoints,
    fee_pre_round: str,
    fee: PaperMoney,
    fee_rounding_applied: bool,
    side_tax_bps: PaperExecutionBasisPoints,
    tax_pre_round: str,
    tax: PaperMoney,
    tax_rounding_applied: bool,
    total_charges: PaperMoney,
    rounding_quantum: str,
    rounding_mode: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "transaction_cost_policy_id": transaction_cost_policy_id,
        "execution_price_evidence": execution_price_evidence.to_dict(),
        "fill_quantity": fill_quantity.to_json_value(),
        "gross_notional_pre_round": gross_notional_pre_round,
        "gross_notional": gross_notional.to_json_value(),
        "gross_notional_rounding_applied": gross_notional_rounding_applied,
        "commission_bps": commission_bps.to_json_value(),
        "commission_pre_round": commission_pre_round,
        "commission": commission.to_json_value(),
        "commission_rounding_applied": commission_rounding_applied,
        "fee_bps": fee_bps.to_json_value(),
        "fee_pre_round": fee_pre_round,
        "fee": fee.to_json_value(),
        "fee_rounding_applied": fee_rounding_applied,
        "side_tax_bps": side_tax_bps.to_json_value(),
        "tax_pre_round": tax_pre_round,
        "tax": tax.to_json_value(),
        "tax_rounding_applied": tax_rounding_applied,
        "total_charges": total_charges.to_json_value(),
        "rounding_quantum": rounding_quantum,
        "rounding_mode": rounding_mode,
    }


@dataclass(frozen=True, init=False)
class PaperExecutionCostEvidence:
    """Exact independently rounded per-fill transaction-cost evidence."""

    schema_version: int
    transaction_cost_policy_id: str
    execution_price_evidence: PaperExecutionPriceEvidence
    fill_quantity: PaperQuantity
    gross_notional_pre_round: str
    gross_notional: PaperMoney
    gross_notional_rounding_applied: bool
    commission_bps: PaperExecutionBasisPoints
    commission_pre_round: str
    commission: PaperMoney
    commission_rounding_applied: bool
    fee_bps: PaperExecutionBasisPoints
    fee_pre_round: str
    fee: PaperMoney
    fee_rounding_applied: bool
    side_tax_bps: PaperExecutionBasisPoints
    tax_pre_round: str
    tax: PaperMoney
    tax_rounding_applied: bool
    total_charges: PaperMoney
    rounding_quantum: str
    rounding_mode: str
    cost_evidence_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                transaction_cost_policy_id=self.transaction_cost_policy_id,
                execution_price_evidence=self.execution_price_evidence,
                fill_quantity=self.fill_quantity,
                gross_notional_pre_round=self.gross_notional_pre_round,
                gross_notional=self.gross_notional,
                gross_notional_rounding_applied=(
                    self.gross_notional_rounding_applied
                ),
                commission_bps=self.commission_bps,
                commission_pre_round=self.commission_pre_round,
                commission=self.commission,
                commission_rounding_applied=self.commission_rounding_applied,
                fee_bps=self.fee_bps,
                fee_pre_round=self.fee_pre_round,
                fee=self.fee,
                fee_rounding_applied=self.fee_rounding_applied,
                side_tax_bps=self.side_tax_bps,
                tax_pre_round=self.tax_pre_round,
                tax=self.tax,
                tax_rounding_applied=self.tax_rounding_applied,
                total_charges=self.total_charges,
                rounding_quantum=self.rounding_quantum,
                rounding_mode=self.rounding_mode,
            ),
            "cost_evidence_digest": self.cost_evidence_digest,
        }


def _rounded_component(
    gross_notional: PaperMoney,
    bps: PaperExecutionBasisPoints,
) -> tuple[str, PaperMoney, bool]:
    pre_round = divide(
        multiply(gross_notional.decimal_value, bps.decimal_value),
        Decimal("10000"),
    )
    rounded, applied = round_money(pre_round)
    return canonical_decimal(pre_round), rounded, applied


def _build(
    *,
    execution_price_evidence: PaperExecutionPriceEvidence,
    fill_quantity: PaperQuantity,
    commission_bps: PaperExecutionBasisPoints,
    fee_bps: PaperExecutionBasisPoints,
    side_tax_bps: PaperExecutionBasisPoints,
) -> PaperExecutionCostEvidence:
    price = _clone_price_evidence(execution_price_evidence)
    quantity = PaperQuantity.parse(fill_quantity.canonical)
    commission_rate = PaperExecutionBasisPoints.parse(commission_bps.canonical)
    fee_rate = PaperExecutionBasisPoints.parse(fee_bps.canonical)
    tax_rate = PaperExecutionBasisPoints.parse(side_tax_bps.canonical)
    gross_pre_decimal = multiply(
        price.execution_price.decimal_value,
        quantity.decimal_value,
    )
    gross, gross_rounded = round_money(gross_pre_decimal)
    commission_pre, commission, commission_rounded = _rounded_component(
        gross,
        commission_rate,
    )
    fee_pre, fee, fee_rounded = _rounded_component(gross, fee_rate)
    tax_pre, tax, tax_rounded = _rounded_component(gross, tax_rate)
    total = PaperMoney.parse(
        canonical_decimal(
            add(
                commission.decimal_value,
                fee.decimal_value,
                tax.decimal_value,
            )
        )
    )
    payload = _payload(
        schema_version=PAPER_EXECUTION_COST_EVIDENCE_SCHEMA_VERSION,
        transaction_cost_policy_id=TRANSACTION_COST_POLICY_ID,
        execution_price_evidence=price,
        fill_quantity=quantity,
        gross_notional_pre_round=canonical_decimal(gross_pre_decimal),
        gross_notional=gross,
        gross_notional_rounding_applied=gross_rounded,
        commission_bps=commission_rate,
        commission_pre_round=commission_pre,
        commission=commission,
        commission_rounding_applied=commission_rounded,
        fee_bps=fee_rate,
        fee_pre_round=fee_pre,
        fee=fee,
        fee_rounding_applied=fee_rounded,
        side_tax_bps=tax_rate,
        tax_pre_round=tax_pre,
        tax=tax,
        tax_rounding_applied=tax_rounded,
        total_charges=total,
        rounding_quantum=canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM),
        rounding_mode=PAPER_EXECUTION_ROUNDING_MODE,
    )
    result = object.__new__(PaperExecutionCostEvidence)
    values = {
        **{
            key: value
            for key, value in payload.items()
            if key
            not in {
                "execution_price_evidence",
                "fill_quantity",
                "gross_notional",
                "commission_bps",
                "commission",
                "fee_bps",
                "fee",
                "side_tax_bps",
                "tax",
                "total_charges",
            }
        },
        "execution_price_evidence": price,
        "fill_quantity": quantity,
        "gross_notional": gross,
        "commission_bps": commission_rate,
        "commission": commission,
        "fee_bps": fee_rate,
        "fee": fee,
        "side_tax_bps": tax_rate,
        "tax": tax,
        "total_charges": total,
        "cost_evidence_digest": canonical_digest(payload),
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_cost_evidence(
    *,
    execution_price_evidence: PaperExecutionPriceEvidence,
    fill_quantity: PaperQuantity,
    execution_policy_reference: PaperExecutionPolicyReference,
) -> PaperExecutionCostEvidence:
    """Derive one candidate Fill's exact v1 cost evidence."""
    price = validate_paper_execution_price_evidence(execution_price_evidence)
    quantity = exact_quantity(
        fill_quantity,
        field_name="fill_quantity",
        strictly_positive=True,
    )
    policy = validate_paper_execution_policy_reference(
        execution_policy_reference
    )
    side_tax = policy.buy_tax_bps if price.side == "buy" else policy.sell_tax_bps
    return _build(
        execution_price_evidence=price,
        fill_quantity=quantity,
        commission_bps=policy.commission_bps,
        fee_bps=policy.fee_bps,
        side_tax_bps=side_tax,
    )


def validate_paper_execution_cost_evidence(
    value: object,
) -> PaperExecutionCostEvidence:
    if type(value) is not PaperExecutionCostEvidence:
        raise ValueError("cost evidence must be PaperExecutionCostEvidence")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_COST_EVIDENCE_SCHEMA_VERSION
            or value.transaction_cost_policy_id != TRANSACTION_COST_POLICY_ID
            or value.rounding_quantum
            != canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM)
            or value.rounding_mode != PAPER_EXECUTION_ROUNDING_MODE
        ):
            raise ValueError("cost evidence metadata is invalid")
        price = validate_paper_execution_price_evidence(
            value.execution_price_evidence
        )
        quantity = exact_quantity(
            value.fill_quantity,
            field_name="fill_quantity",
            strictly_positive=True,
        )
        commission_rate = _exact_bps(
            value.commission_bps,
            field_name="commission_bps",
        )
        fee_rate = _exact_bps(value.fee_bps, field_name="fee_bps")
        tax_rate = _exact_bps(value.side_tax_bps, field_name="side_tax_bps")
        for field_name in (
            "gross_notional",
            "commission",
            "fee",
            "tax",
            "total_charges",
        ):
            exact_money(getattr(value, field_name), field_name=field_name)
        for field_name in (
            "gross_notional_rounding_applied",
            "commission_rounding_applied",
            "fee_rounding_applied",
            "tax_rounding_applied",
        ):
            if type(getattr(value, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a boolean")
        validate_digest(value.cost_evidence_digest, field_name="cost_evidence_digest")
        expected = _build(
            execution_price_evidence=price,
            fill_quantity=quantity,
            commission_bps=commission_rate,
            fee_bps=fee_rate,
            side_tax_bps=tax_rate,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution cost evidence is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution cost evidence is invalid")
    return value


def _clone_cost_evidence(
    value: PaperExecutionCostEvidence,
) -> PaperExecutionCostEvidence:
    validate_paper_execution_cost_evidence(value)
    return _build(
        execution_price_evidence=value.execution_price_evidence,
        fill_quantity=value.fill_quantity,
        commission_bps=value.commission_bps,
        fee_bps=value.fee_bps,
        side_tax_bps=value.side_tax_bps,
    )
