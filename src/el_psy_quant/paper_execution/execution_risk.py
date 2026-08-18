"""Immutable M34 execution-time long-only cash-risk revalidation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from el_psy_quant.paper_account import (
    PaperAccountLedgerState,
    PaperMoney,
    PaperQuantity,
    validate_paper_account_ledger_state,
)
from el_psy_quant.paper_execution._arithmetic import (
    PAPER_EXECUTION_MONEY_QUANTUM,
    PAPER_EXECUTION_ROUNDING_MODE,
    add,
    canonical_decimal,
    exact_money,
    exact_quantity,
    multiply,
    round_money,
    subtract,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.costs import (
    PaperExecutionCostEvidence,
    _clone_cost_evidence,
    validate_paper_execution_cost_evidence,
)
from el_psy_quant.paper_execution.lifecycle import (
    PaperExecutionOrderState,
    validate_paper_execution_order_state,
)
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrder,
    PaperExecutionOrderReference,
    _clone_order_reference,
    create_paper_execution_order_reference,
    validate_paper_execution_order,
)
from el_psy_quant.paper_execution.pricing import (
    PaperExecutionPriceEvidence,
    _clone_price_evidence,
    validate_paper_execution_price_evidence,
)
from el_psy_quant.paper_execution.upstream_references import _clone_risk_policy
from el_psy_quant.strategy_order import (
    LONG_ONLY_CASH_RISK_POLICY_ID,
    PreTradeRiskPolicyReference,
    validate_pre_trade_risk_policy_reference,
)

PAPER_EXECUTION_RISK_REVALIDATION_SCHEMA_VERSION = 1

PAPER_EXECUTION_RISK_OUTCOME_ALLOW = "allow"
PAPER_EXECUTION_RISK_OUTCOME_REJECT = "reject"

PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_POSITION = (
    "insufficient_position_quantity"
)
PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_QUANTITY = (
    "maximum_order_quantity_exceeded"
)
PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_NOTIONAL = (
    "maximum_order_notional_exceeded"
)
PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_CASH = "insufficient_available_cash"
PAPER_EXECUTION_RISK_REASON_NEGATIVE_SELL_PROCEEDS = (
    "negative_sell_net_proceeds"
)

PaperExecutionRiskOutcome = Literal["allow", "reject"]


@dataclass(frozen=True)
class PaperExecutionRiskRuleEvidence:
    """One ordered, stable, JSON-safe execution-risk rule result."""

    rule_id: str
    passed: bool
    reason_code: str | None
    observed_value: str | None
    limit_value: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id:
            raise ValueError("risk rule_id must be non-empty")
        if type(self.passed) is not bool:
            raise ValueError("risk rule passed must be boolean")
        if self.passed != (self.reason_code is None):
            raise ValueError("risk rule reason_code must match outcome")
        for field_name in ("reason_code", "observed_value", "limit_value"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"risk rule {field_name} must be string or None")

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "reason_code": self.reason_code,
            "observed_value": self.observed_value,
            "limit_value": self.limit_value,
        }


def _rule(
    rule_id: str,
    passed: bool,
    *,
    reason_code: str | None = None,
    observed: str | None = None,
    limit: str | None = None,
) -> PaperExecutionRiskRuleEvidence:
    return PaperExecutionRiskRuleEvidence(
        rule_id=rule_id,
        passed=passed,
        reason_code=None if passed else reason_code,
        observed_value=observed,
        limit_value=limit,
    )


def _payload(
    *,
    schema_version: int,
    execution_order_reference: PaperExecutionOrderReference,
    execution_version: int,
    account_id: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    available_cash: PaperMoney,
    current_instrument_quantity: PaperQuantity,
    risk_policy_reference: PreTradeRiskPolicyReference,
    execution_price_evidence: PaperExecutionPriceEvidence,
    cost_evidence: PaperExecutionCostEvidence,
    requested_quantity: PaperQuantity,
    remaining_quantity_before_step: PaperQuantity,
    candidate_fill_quantity: PaperQuantity,
    cumulative_filled_gross_notional: PaperMoney,
    projected_notional_pre_round: str,
    projected_order_gross_notional: PaperMoney,
    projected_notional_rounding_applied: bool,
    rules: tuple[PaperExecutionRiskRuleEvidence, ...],
    outcome: PaperExecutionRiskOutcome,
    reason_codes: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "execution_order_reference": execution_order_reference.to_dict(),
        "execution_version": execution_version,
        "account_id": account_id,
        "account_head_version": account_head_version,
        "account_head_event_id": account_head_event_id,
        "account_head_chain_digest": account_head_chain_digest,
        "available_cash": available_cash.to_json_value(),
        "current_instrument_quantity": current_instrument_quantity.to_json_value(),
        "risk_policy_reference": risk_policy_reference.to_dict(),
        "execution_price_evidence": execution_price_evidence.to_dict(),
        "cost_evidence": cost_evidence.to_dict(),
        "requested_quantity": requested_quantity.to_json_value(),
        "remaining_quantity_before_step": (
            remaining_quantity_before_step.to_json_value()
        ),
        "candidate_fill_quantity": candidate_fill_quantity.to_json_value(),
        "cumulative_filled_gross_notional": (
            cumulative_filled_gross_notional.to_json_value()
        ),
        "projected_notional_pre_round": projected_notional_pre_round,
        "projected_order_gross_notional": (
            projected_order_gross_notional.to_json_value()
        ),
        "projected_notional_rounding_applied": (
            projected_notional_rounding_applied
        ),
        "rounding_quantum": canonical_decimal(PAPER_EXECUTION_MONEY_QUANTUM),
        "rounding_mode": PAPER_EXECUTION_ROUNDING_MODE,
        "rules": [rule.to_dict() for rule in rules],
        "outcome": outcome,
        "reason_codes": list(reason_codes),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionRiskRevalidation:
    """Exact immutable M34 risk result without creating an M33 Decision."""

    schema_version: int
    risk_revalidation_id: str
    risk_revalidation_digest: str
    execution_order_reference: PaperExecutionOrderReference
    execution_version: int
    account_id: str
    account_head_version: int
    account_head_event_id: str
    account_head_chain_digest: str
    available_cash: PaperMoney
    current_instrument_quantity: PaperQuantity
    risk_policy_reference: PreTradeRiskPolicyReference
    execution_price_evidence: PaperExecutionPriceEvidence
    cost_evidence: PaperExecutionCostEvidence
    requested_quantity: PaperQuantity
    remaining_quantity_before_step: PaperQuantity
    candidate_fill_quantity: PaperQuantity
    cumulative_filled_gross_notional: PaperMoney
    projected_notional_pre_round: str
    projected_order_gross_notional: PaperMoney
    projected_notional_rounding_applied: bool
    rules: tuple[PaperExecutionRiskRuleEvidence, ...]
    outcome: PaperExecutionRiskOutcome
    reason_codes: tuple[str, ...]

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                execution_order_reference=self.execution_order_reference,
                execution_version=self.execution_version,
                account_id=self.account_id,
                account_head_version=self.account_head_version,
                account_head_event_id=self.account_head_event_id,
                account_head_chain_digest=self.account_head_chain_digest,
                available_cash=self.available_cash,
                current_instrument_quantity=self.current_instrument_quantity,
                risk_policy_reference=self.risk_policy_reference,
                execution_price_evidence=self.execution_price_evidence,
                cost_evidence=self.cost_evidence,
                requested_quantity=self.requested_quantity,
                remaining_quantity_before_step=(self.remaining_quantity_before_step),
                candidate_fill_quantity=self.candidate_fill_quantity,
                cumulative_filled_gross_notional=(
                    self.cumulative_filled_gross_notional
                ),
                projected_notional_pre_round=self.projected_notional_pre_round,
                projected_order_gross_notional=(
                    self.projected_order_gross_notional
                ),
                projected_notional_rounding_applied=(
                    self.projected_notional_rounding_applied
                ),
                rules=self.rules,
                outcome=self.outcome,
                reason_codes=self.reason_codes,
            ),
            "risk_revalidation_id": self.risk_revalidation_id,
            "risk_revalidation_digest": self.risk_revalidation_digest,
        }


def _derive(
    *,
    order_reference: PaperExecutionOrderReference,
    execution_version: int,
    account_id: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    available_cash: PaperMoney,
    current_instrument_quantity: PaperQuantity,
    side: str,
    risk_policy_reference: PreTradeRiskPolicyReference,
    execution_price_evidence: PaperExecutionPriceEvidence,
    cost_evidence: PaperExecutionCostEvidence,
    requested_quantity: PaperQuantity,
    remaining_quantity_before_step: PaperQuantity,
    candidate_fill_quantity: PaperQuantity,
    cumulative_filled_gross_notional: PaperMoney,
) -> PaperExecutionRiskRevalidation:
    projected_remaining_pre = multiply(
        remaining_quantity_before_step.decimal_value,
        execution_price_evidence.execution_price.decimal_value,
    )
    projected_remaining, projected_rounded = round_money(projected_remaining_pre)
    projected_total = PaperMoney.parse(
        canonical_decimal(
            add(
                cumulative_filled_gross_notional.decimal_value,
                projected_remaining.decimal_value,
            )
        )
    )
    maximum_quantity = risk_policy_reference.maximum_order_quantity
    maximum_notional = risk_policy_reference.maximum_order_notional
    position_passed = (
        side == "buy"
        or candidate_fill_quantity.decimal_value
        <= current_instrument_quantity.decimal_value
    )
    quantity_passed = (
        maximum_quantity is None
        or requested_quantity.decimal_value <= maximum_quantity.decimal_value
    )
    notional_passed = (
        maximum_notional is None
        or projected_total.decimal_value <= maximum_notional.decimal_value
    )
    candidate_debit = add(
        cost_evidence.gross_notional.decimal_value,
        cost_evidence.total_charges.decimal_value,
    )
    cash_passed = side == "sell" or candidate_debit <= available_cash.decimal_value
    sell_net = subtract(
        cost_evidence.gross_notional.decimal_value,
        cost_evidence.total_charges.decimal_value,
    )
    proceeds_passed = side == "buy" or sell_net >= 0
    rules = (
        _rule(
            "active_account_compatible",
            True,
            observed=account_id,
            limit=account_id,
        ),
        _rule(
            "sufficient_position_quantity",
            position_passed,
            reason_code=PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_POSITION,
            observed=current_instrument_quantity.to_json_value(),
            limit=candidate_fill_quantity.to_json_value(),
        ),
        _rule(
            "maximum_order_quantity",
            quantity_passed,
            reason_code=PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_QUANTITY,
            observed=requested_quantity.to_json_value(),
            limit=(
                None
                if maximum_quantity is None
                else maximum_quantity.to_json_value()
            ),
        ),
        _rule(
            "maximum_order_notional",
            notional_passed,
            reason_code=PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_NOTIONAL,
            observed=projected_total.to_json_value(),
            limit=(
                None
                if maximum_notional is None
                else maximum_notional.to_json_value()
            ),
        ),
        _rule(
            "sufficient_available_cash",
            cash_passed,
            reason_code=PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_CASH,
            observed=available_cash.to_json_value(),
            limit=canonical_decimal(candidate_debit) if side == "buy" else None,
        ),
        _rule(
            "non_negative_sell_net_proceeds",
            proceeds_passed,
            reason_code=PAPER_EXECUTION_RISK_REASON_NEGATIVE_SELL_PROCEEDS,
            observed=canonical_decimal(sell_net) if side == "sell" else None,
            limit="0" if side == "sell" else None,
        ),
        _rule("long_only_execution_invariants", True),
    )
    reasons = tuple(
        rule.reason_code
        for rule in rules
        if not rule.passed and rule.reason_code is not None
    )
    outcome: PaperExecutionRiskOutcome = "allow" if not reasons else "reject"
    order_ref = _clone_order_reference(order_reference)
    policy = _clone_risk_policy(risk_policy_reference)
    price = _clone_price_evidence(execution_price_evidence)
    costs = _clone_cost_evidence(cost_evidence)
    payload = _payload(
        schema_version=PAPER_EXECUTION_RISK_REVALIDATION_SCHEMA_VERSION,
        execution_order_reference=order_ref,
        execution_version=execution_version,
        account_id=account_id,
        account_head_version=account_head_version,
        account_head_event_id=account_head_event_id,
        account_head_chain_digest=account_head_chain_digest,
        available_cash=available_cash,
        current_instrument_quantity=current_instrument_quantity,
        risk_policy_reference=policy,
        execution_price_evidence=price,
        cost_evidence=costs,
        requested_quantity=requested_quantity,
        remaining_quantity_before_step=remaining_quantity_before_step,
        candidate_fill_quantity=candidate_fill_quantity,
        cumulative_filled_gross_notional=cumulative_filled_gross_notional,
        projected_notional_pre_round=canonical_decimal(projected_remaining_pre),
        projected_order_gross_notional=projected_total,
        projected_notional_rounding_applied=projected_rounded,
        rules=rules,
        outcome=outcome,
        reason_codes=reasons,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PaperExecutionRiskRevalidation)
    values = {
        "schema_version": PAPER_EXECUTION_RISK_REVALIDATION_SCHEMA_VERSION,
        "risk_revalidation_id": f"perr_{digest}",
        "risk_revalidation_digest": digest,
        "execution_order_reference": order_ref,
        "execution_version": execution_version,
        "account_id": account_id,
        "account_head_version": account_head_version,
        "account_head_event_id": account_head_event_id,
        "account_head_chain_digest": account_head_chain_digest,
        "available_cash": PaperMoney.parse(available_cash.canonical),
        "current_instrument_quantity": PaperQuantity.parse(
            current_instrument_quantity.canonical
        ),
        "risk_policy_reference": policy,
        "execution_price_evidence": price,
        "cost_evidence": costs,
        "requested_quantity": PaperQuantity.parse(requested_quantity.canonical),
        "remaining_quantity_before_step": PaperQuantity.parse(
            remaining_quantity_before_step.canonical
        ),
        "candidate_fill_quantity": PaperQuantity.parse(
            candidate_fill_quantity.canonical
        ),
        "cumulative_filled_gross_notional": PaperMoney.parse(
            cumulative_filled_gross_notional.canonical
        ),
        "projected_notional_pre_round": canonical_decimal(projected_remaining_pre),
        "projected_order_gross_notional": projected_total,
        "projected_notional_rounding_applied": projected_rounded,
        "rules": tuple(rules),
        "outcome": outcome,
        "reason_codes": reasons,
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_risk_revalidation(
    *,
    order: PaperExecutionOrder,
    current_state: PaperExecutionOrderState,
    account_state: PaperAccountLedgerState,
    execution_price_evidence: PaperExecutionPriceEvidence,
    cost_evidence: PaperExecutionCostEvidence,
    candidate_fill_quantity: PaperQuantity,
    cumulative_filled_gross_notional: PaperMoney,
) -> PaperExecutionRiskRevalidation:
    """Recheck exact current M31 state under the copied M33 v1 policy."""
    valid_order = validate_paper_execution_order(order)
    state = validate_paper_execution_order_state(current_state)
    account = validate_paper_account_ledger_state(account_state)
    price = validate_paper_execution_price_evidence(execution_price_evidence)
    costs = validate_paper_execution_cost_evidence(cost_evidence)
    quantity = exact_quantity(
        candidate_fill_quantity,
        field_name="candidate_fill_quantity",
        strictly_positive=True,
    )
    cumulative = exact_money(
        cumulative_filled_gross_notional,
        field_name="cumulative_filled_gross_notional",
    )
    order_reference = create_paper_execution_order_reference(valid_order)
    if state.execution_order_reference != order_reference or state.terminal:
        raise ValueError("execution risk state is incompatible with order")
    if account.lifecycle_status != "active":
        raise ValueError("execution risk account must be active")
    if not (
        account.account_identity.account_id == valid_order.account_id
        and account.account_identity.base_currency
        == valid_order.account_handoff_reference.base_currency
        and price.side == valid_order.side
        and costs.execution_price_evidence == price
        and costs.fill_quantity == quantity
        and quantity.decimal_value <= state.remaining_quantity.decimal_value
        and cumulative.decimal_value >= 0
    ):
        raise ValueError("execution risk evidence anchors are incompatible")
    positions = {position.symbol: position.quantity for position in account.positions}
    current_quantity = positions.get(
        valid_order.instrument_id,
        PaperQuantity.parse("0"),
    )
    policy = valid_order.risk_handoff_reference.risk_policy_reference
    if policy.policy_id != LONG_ONLY_CASH_RISK_POLICY_ID:
        raise ValueError("unsupported execution risk policy")
    return _derive(
        order_reference=order_reference,
        execution_version=state.execution_version,
        account_id=account.account_identity.account_id,
        account_head_version=account.head_version,
        account_head_event_id=account.head_event_id,
        account_head_chain_digest=account.head_chain_digest,
        available_cash=account.available_cash,
        current_instrument_quantity=current_quantity,
        side=valid_order.side,
        risk_policy_reference=policy,
        execution_price_evidence=price,
        cost_evidence=costs,
        requested_quantity=valid_order.requested_quantity,
        remaining_quantity_before_step=state.remaining_quantity,
        candidate_fill_quantity=quantity,
        cumulative_filled_gross_notional=cumulative,
    )


def validate_paper_execution_risk_revalidation(
    value: object,
) -> PaperExecutionRiskRevalidation:
    if type(value) is not PaperExecutionRiskRevalidation:
        raise ValueError("risk evidence must be PaperExecutionRiskRevalidation")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PAPER_EXECUTION_RISK_REVALIDATION_SCHEMA_VERSION
            or type(value.execution_version) is not int
            or value.execution_version < 0
            or type(value.account_head_version) is not int
            or value.account_head_version < 1
            or type(value.projected_notional_rounding_applied) is not bool
            or value.outcome not in {"allow", "reject"}
            or type(value.rules) is not tuple
            or type(value.reason_codes) is not tuple
        ):
            raise ValueError("risk evidence metadata is invalid")
        validate_digest(
            value.risk_revalidation_digest,
            field_name="risk_revalidation_digest",
        )
        if value.risk_revalidation_id != f"perr_{value.risk_revalidation_digest}":
            raise ValueError("risk revalidation ID does not match digest")
        validate_pre_trade_risk_policy_reference(value.risk_policy_reference)
        price = validate_paper_execution_price_evidence(
            value.execution_price_evidence
        )
        costs = validate_paper_execution_cost_evidence(value.cost_evidence)
        if costs.execution_price_evidence != price:
            raise ValueError("risk price and costs do not match")
        available = exact_money(value.available_cash, field_name="available_cash")
        current = exact_quantity(
            value.current_instrument_quantity,
            field_name="current_instrument_quantity",
        )
        requested = exact_quantity(
            value.requested_quantity,
            field_name="requested_quantity",
            strictly_positive=True,
        )
        remaining = exact_quantity(
            value.remaining_quantity_before_step,
            field_name="remaining_quantity_before_step",
            strictly_positive=True,
        )
        candidate = exact_quantity(
            value.candidate_fill_quantity,
            field_name="candidate_fill_quantity",
            strictly_positive=True,
        )
        cumulative = exact_money(
            value.cumulative_filled_gross_notional,
            field_name="cumulative_filled_gross_notional",
        )
        expected = _derive(
            order_reference=value.execution_order_reference,
            execution_version=value.execution_version,
            account_id=value.account_id,
            account_head_version=value.account_head_version,
            account_head_event_id=value.account_head_event_id,
            account_head_chain_digest=value.account_head_chain_digest,
            available_cash=available,
            current_instrument_quantity=current,
            side=price.side,
            risk_policy_reference=value.risk_policy_reference,
            execution_price_evidence=price,
            cost_evidence=costs,
            requested_quantity=requested,
            remaining_quantity_before_step=remaining,
            candidate_fill_quantity=candidate,
            cumulative_filled_gross_notional=cumulative,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution risk revalidation is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution risk revalidation is invalid")
    return value


def _clone_risk_revalidation(
    value: PaperExecutionRiskRevalidation,
) -> PaperExecutionRiskRevalidation:
    validate_paper_execution_risk_revalidation(value)
    return _derive(
        order_reference=value.execution_order_reference,
        execution_version=value.execution_version,
        account_id=value.account_id,
        account_head_version=value.account_head_version,
        account_head_event_id=value.account_head_event_id,
        account_head_chain_digest=value.account_head_chain_digest,
        available_cash=value.available_cash,
        current_instrument_quantity=value.current_instrument_quantity,
        side=value.execution_price_evidence.side,
        risk_policy_reference=value.risk_policy_reference,
        execution_price_evidence=value.execution_price_evidence,
        cost_evidence=value.cost_evidence,
        requested_quantity=value.requested_quantity,
        remaining_quantity_before_step=value.remaining_quantity_before_step,
        candidate_fill_quantity=value.candidate_fill_quantity,
        cumulative_filled_gross_notional=(
            value.cumulative_filled_gross_notional
        ),
    )
