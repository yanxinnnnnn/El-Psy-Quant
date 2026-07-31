"""Immutable versioned pre-trade risk policy references."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    reject_public_construction,
    validate_digest,
)

PRE_TRADE_RISK_POLICY_SCHEMA_VERSION = 1
LONG_ONLY_CASH_RISK_POLICY_ID = "long_only_cash_risk_v1"
LATEST_TRADE_PRICE_POLICY_ID = "latest_trade_price_v1"


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
        raise ValueError(f"{field_name} must be a valid PaperQuantity") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
        or rebuilt.decimal_value <= 0
    ):
        raise ValueError(
            f"{field_name} must be an exact strictly positive PaperQuantity"
        )
    return rebuilt


def _exact_positive_money(
    value: object,
    *,
    field_name: str,
) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney or None")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperMoney") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
        or rebuilt.decimal_value <= 0
    ):
        raise ValueError(
            f"{field_name} must be an exact strictly positive PaperMoney"
        )
    return rebuilt


def _configuration_payload(
    *,
    maximum_order_quantity: PaperQuantity | None,
    maximum_order_notional: PaperMoney | None,
) -> dict[str, object]:
    return {
        "maximum_order_quantity": (
            None
            if maximum_order_quantity is None
            else maximum_order_quantity.to_json_value()
        ),
        "maximum_order_notional": (
            None
            if maximum_order_notional is None
            else maximum_order_notional.to_json_value()
        ),
    }


def _reference_payload_without_digest(
    *,
    schema_version: int,
    policy_id: str,
    reference_price_policy_id: str,
    maximum_order_quantity: PaperQuantity | None,
    maximum_order_notional: PaperMoney | None,
    configuration_digest: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_id": policy_id,
        "reference_price_policy_id": reference_price_policy_id,
        **_configuration_payload(
            maximum_order_quantity=maximum_order_quantity,
            maximum_order_notional=maximum_order_notional,
        ),
        "configuration_digest": configuration_digest,
    }


@dataclass(frozen=True, init=False)
class PreTradeRiskPolicyReference:
    """One immutable explicit long-only cash-risk policy selection."""

    schema_version: int
    policy_id: str
    reference_price_policy_id: str
    maximum_order_quantity: PaperQuantity | None
    maximum_order_notional: PaperMoney | None
    configuration_digest: str
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON policy reference."""
        return {
            **_reference_payload_without_digest(
                schema_version=self.schema_version,
                policy_id=self.policy_id,
                reference_price_policy_id=self.reference_price_policy_id,
                maximum_order_quantity=self.maximum_order_quantity,
                maximum_order_notional=self.maximum_order_notional,
                configuration_digest=self.configuration_digest,
            ),
            "reference_digest": self.reference_digest,
        }


def _build_policy_reference(
    *,
    schema_version: int,
    policy_id: str,
    reference_price_policy_id: str,
    maximum_order_quantity: PaperQuantity | None,
    maximum_order_notional: PaperMoney | None,
) -> PreTradeRiskPolicyReference:
    quantity = (
        None
        if maximum_order_quantity is None
        else PaperQuantity.parse(maximum_order_quantity.canonical)
    )
    notional = (
        None
        if maximum_order_notional is None
        else PaperMoney.parse(maximum_order_notional.canonical)
    )
    configuration_digest = canonical_digest(
        _configuration_payload(
            maximum_order_quantity=quantity,
            maximum_order_notional=notional,
        )
    )
    payload = _reference_payload_without_digest(
        schema_version=schema_version,
        policy_id=policy_id,
        reference_price_policy_id=reference_price_policy_id,
        maximum_order_quantity=quantity,
        maximum_order_notional=notional,
        configuration_digest=configuration_digest,
    )
    result = object.__new__(PreTradeRiskPolicyReference)
    for field_name, value in (
        ("schema_version", schema_version),
        ("policy_id", policy_id),
        ("reference_price_policy_id", reference_price_policy_id),
        ("maximum_order_quantity", quantity),
        ("maximum_order_notional", notional),
        ("configuration_digest", configuration_digest),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_long_only_cash_risk_policy_reference(
    *,
    maximum_order_quantity: PaperQuantity | None = None,
    maximum_order_notional: PaperMoney | None = None,
    schema_version: int = PRE_TRADE_RISK_POLICY_SCHEMA_VERSION,
) -> PreTradeRiskPolicyReference:
    """Create one explicit policy reference without evaluating any risk."""
    if (
        type(schema_version) is not int
        or schema_version != PRE_TRADE_RISK_POLICY_SCHEMA_VERSION
    ):
        raise ValueError(
            f"unsupported pre-trade risk policy schema_version: {schema_version}"
        )
    quantity = (
        None
        if maximum_order_quantity is None
        else _exact_positive_quantity(
            maximum_order_quantity,
            field_name="maximum_order_quantity",
        )
    )
    notional = (
        None
        if maximum_order_notional is None
        else _exact_positive_money(
            maximum_order_notional,
            field_name="maximum_order_notional",
        )
    )
    return _build_policy_reference(
        schema_version=schema_version,
        policy_id=LONG_ONLY_CASH_RISK_POLICY_ID,
        reference_price_policy_id=LATEST_TRADE_PRICE_POLICY_ID,
        maximum_order_quantity=quantity,
        maximum_order_notional=notional,
    )


def validate_pre_trade_risk_policy_reference(
    value: object,
) -> PreTradeRiskPolicyReference:
    """Recompute and verify one complete policy reference."""
    if type(value) is not PreTradeRiskPolicyReference:
        raise ValueError(
            "risk_policy_reference must be a PreTradeRiskPolicyReference"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PRE_TRADE_RISK_POLICY_SCHEMA_VERSION
        ):
            raise ValueError("unsupported risk policy schema_version")
        if value.policy_id != LONG_ONLY_CASH_RISK_POLICY_ID:
            raise ValueError("unsupported risk policy ID")
        if value.reference_price_policy_id != LATEST_TRADE_PRICE_POLICY_ID:
            raise ValueError("unsupported reference price policy ID")
        quantity = (
            None
            if value.maximum_order_quantity is None
            else _exact_positive_quantity(
                value.maximum_order_quantity,
                field_name="maximum_order_quantity",
            )
        )
        notional = (
            None
            if value.maximum_order_notional is None
            else _exact_positive_money(
                value.maximum_order_notional,
                field_name="maximum_order_notional",
            )
        )
        validate_digest(
            value.configuration_digest,
            field_name="configuration_digest",
        )
        validate_digest(value.reference_digest, field_name="reference_digest")
        rebuilt = _build_policy_reference(
            schema_version=value.schema_version,
            policy_id=value.policy_id,
            reference_price_policy_id=value.reference_price_policy_id,
            maximum_order_quantity=quantity,
            maximum_order_notional=notional,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("pre-trade risk policy reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("pre-trade risk policy reference is invalid")
    return value


def _clone_pre_trade_risk_policy_reference(
    value: PreTradeRiskPolicyReference,
) -> PreTradeRiskPolicyReference:
    validate_pre_trade_risk_policy_reference(value)
    return _build_policy_reference(
        schema_version=value.schema_version,
        policy_id=value.policy_id,
        reference_price_policy_id=value.reference_price_policy_id,
        maximum_order_quantity=value.maximum_order_quantity,
        maximum_order_notional=value.maximum_order_notional,
    )
