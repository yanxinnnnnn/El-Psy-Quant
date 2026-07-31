"""Immutable price, rule, and input-snapshot evidence for pre-trade risk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    normalize_market_instrument_id,
)
from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.account_references import (
    OrderIntentAccountReference,
    _clone_order_intent_account_reference,
    validate_order_intent_account_reference,
)
from el_psy_quant.strategy_order.market_references import (
    StrategySignalMarketReference,
    _clone_strategy_signal_market_reference,
    validate_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.order_intents import (
    ORDER_INTENT_SIDE_BUY,
    ORDER_INTENT_SIDE_SELL,
    OrderIntentReference,
    OrderIntentSide,
    validate_order_intent_reference,
)
from el_psy_quant.strategy_order.risk_commands import (
    _clone_order_intent_reference,
)
from el_psy_quant.strategy_order.risk_policies import (
    LATEST_TRADE_PRICE_POLICY_ID,
    PreTradeRiskPolicyReference,
    _clone_pre_trade_risk_policy_reference,
    validate_pre_trade_risk_policy_reference,
)

PRE_TRADE_RISK_PRICE_REFERENCE_SCHEMA_VERSION = 1
PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION = 1
PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION = 1

PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION = (
    "insufficient_position_quantity"
)
PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY = "maximum_order_quantity_exceeded"
PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL = "maximum_order_notional_exceeded"
PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH = "insufficient_available_cash"

PRE_TRADE_RISK_RULE_ORDER = (
    PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
    PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
    PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL,
    PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
)

PRE_TRADE_RISK_VALUE_TYPE_QUANTITY = "quantity"
PRE_TRADE_RISK_VALUE_TYPE_MONEY = "money"
SUPPORTED_PRE_TRADE_RISK_VALUE_TYPES = (
    PRE_TRADE_RISK_VALUE_TYPE_QUANTITY,
    PRE_TRADE_RISK_VALUE_TYPE_MONEY,
)

PreTradeRiskValueType = Literal["quantity", "money"]
RiskEvidenceValue = PaperQuantity | PaperMoney | None

_MAX_RISK_EVIDENCE_ID_LENGTH = 512


def _exact_quantity(
    value: object,
    *,
    field_name: str,
    strictly_positive: bool = False,
) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperQuantity") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
        or rebuilt.decimal_value < 0
        or (strictly_positive and rebuilt.decimal_value <= 0)
    ):
        qualifier = "strictly positive " if strictly_positive else "non-negative "
        raise ValueError(f"{field_name} must be an exact {qualifier}PaperQuantity")
    return rebuilt


def _exact_money(
    value: object,
    *,
    field_name: str,
    strictly_positive: bool = False,
) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperMoney") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
        or rebuilt.decimal_value < 0
        or (strictly_positive and rebuilt.decimal_value <= 0)
    ):
        qualifier = "strictly positive " if strictly_positive else "non-negative "
        raise ValueError(f"{field_name} must be an exact {qualifier}PaperMoney")
    return rebuilt


def _money_from_decimal(value: Decimal) -> PaperMoney:
    if not value.is_finite():
        raise ValueError("money arithmetic must be finite")
    canonical = format(value, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"", "-0"}:
        canonical = "0"
    return PaperMoney.parse(canonical)


def _evidence_json_value(value: RiskEvidenceValue) -> str | None:
    return None if value is None else value.to_json_value()


def _price_reference_payload_without_digest(
    *,
    schema_version: int,
    reference_price_policy_id: str,
    event_stream_digest: str,
    replay_id: str,
    cursor_position: int,
    price_event_position: int,
    price_event_id: str,
    price_event_time: datetime,
    instrument_id: str,
    price_event_digest: str,
    reference_price: PaperMoney,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "reference_price_policy_id": reference_price_policy_id,
        "event_stream_digest": event_stream_digest,
        "replay_id": replay_id,
        "cursor_position": cursor_position,
        "price_event_position": price_event_position,
        "price_event_id": price_event_id,
        "price_event_time": price_event_time.isoformat(),
        "instrument_id": instrument_id,
        "price_event_digest": price_event_digest,
        "reference_price": reference_price.to_json_value(),
    }


@dataclass(frozen=True, init=False)
class PreTradeRiskPriceReference:
    """Exact latest consumed same-instrument trade-price evidence."""

    schema_version: int
    reference_price_policy_id: str
    event_stream_digest: str
    replay_id: str
    cursor_position: int
    price_event_position: int
    price_event_id: str
    price_event_time: datetime
    instrument_id: str
    price_event_digest: str
    reference_price: PaperMoney
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON price-evidence contract."""
        return {
            **_price_reference_payload_without_digest(
                schema_version=self.schema_version,
                reference_price_policy_id=self.reference_price_policy_id,
                event_stream_digest=self.event_stream_digest,
                replay_id=self.replay_id,
                cursor_position=self.cursor_position,
                price_event_position=self.price_event_position,
                price_event_id=self.price_event_id,
                price_event_time=self.price_event_time,
                instrument_id=self.instrument_id,
                price_event_digest=self.price_event_digest,
                reference_price=self.reference_price,
            ),
            "reference_digest": self.reference_digest,
        }


def _build_price_reference(
    *,
    schema_version: int,
    reference_price_policy_id: str,
    event_stream_digest: str,
    replay_id: str,
    cursor_position: int,
    price_event_position: int,
    price_event_id: str,
    price_event_time: datetime,
    instrument_id: str,
    price_event_digest: str,
    reference_price: PaperMoney,
) -> PreTradeRiskPriceReference:
    price = PaperMoney.parse(reference_price.canonical)
    payload = _price_reference_payload_without_digest(
        schema_version=schema_version,
        reference_price_policy_id=reference_price_policy_id,
        event_stream_digest=event_stream_digest,
        replay_id=replay_id,
        cursor_position=cursor_position,
        price_event_position=price_event_position,
        price_event_id=price_event_id,
        price_event_time=price_event_time,
        instrument_id=instrument_id,
        price_event_digest=price_event_digest,
        reference_price=price,
    )
    result = object.__new__(PreTradeRiskPriceReference)
    for field_name, value in (
        ("schema_version", schema_version),
        ("reference_price_policy_id", reference_price_policy_id),
        ("event_stream_digest", event_stream_digest),
        ("replay_id", replay_id),
        ("cursor_position", cursor_position),
        ("price_event_position", price_event_position),
        ("price_event_id", price_event_id),
        ("price_event_time", price_event_time),
        ("instrument_id", instrument_id),
        ("price_event_digest", price_event_digest),
        ("reference_price", price),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def _price_from_event(event: MarketDataEvent) -> PaperMoney:
    payload = event.payload
    if "price" not in payload:
        raise ValueError("latest matching trade must contain top-level price")
    raw_price = payload["price"]
    if type(raw_price) not in (int, float):
        raise ValueError("latest matching trade price must be a JSON number")
    try:
        decimal_price = Decimal(str(raw_price))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("latest matching trade price is invalid") from exc
    if not decimal_price.is_finite() or decimal_price <= 0:
        raise ValueError(
            "latest matching trade price must be finite and strictly positive"
        )
    try:
        return _money_from_decimal(decimal_price)
    except ValueError as exc:
        raise ValueError(
            "latest matching trade price is not exactly representable"
        ) from exc


def _create_latest_trade_price_reference(
    *,
    replay_engine: MarketDataReplayEngine,
    market_reference: StrategySignalMarketReference,
) -> PreTradeRiskPriceReference:
    cursor = replay_engine.cursor
    consumed = replay_engine.events[: cursor.position]
    candidate: tuple[int, MarketDataEvent] | None = None
    for zero_based_position in range(len(consumed) - 1, -1, -1):
        event = consumed[zero_based_position]
        if (
            event.instrument_id == market_reference.instrument_id
            and event.event_type == "trade"
        ):
            candidate = (zero_based_position + 1, event)
            break
    if candidate is None:
        raise ValueError("no consumed same-instrument trade price exists")
    price_event_position, event = candidate
    price = _price_from_event(event)
    return _build_price_reference(
        schema_version=PRE_TRADE_RISK_PRICE_REFERENCE_SCHEMA_VERSION,
        reference_price_policy_id=LATEST_TRADE_PRICE_POLICY_ID,
        event_stream_digest=cursor.event_stream_digest,
        replay_id=cursor.replay_id,
        cursor_position=cursor.position,
        price_event_position=price_event_position,
        price_event_id=event.event_id,
        price_event_time=event.event_time,
        instrument_id=event.instrument_id,
        price_event_digest=canonical_digest(event.to_dict()),
        reference_price=price,
    )


def validate_pre_trade_risk_price_reference(
    value: object,
) -> PreTradeRiskPriceReference:
    """Recompute and verify one complete price reference."""
    if type(value) is not PreTradeRiskPriceReference:
        raise ValueError(
            "price_reference must be a PreTradeRiskPriceReference"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PRE_TRADE_RISK_PRICE_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported price-reference schema_version")
        if value.reference_price_policy_id != LATEST_TRADE_PRICE_POLICY_ID:
            raise ValueError("unsupported reference price policy ID")
        event_stream_digest = validate_digest(
            value.event_stream_digest,
            field_name="event_stream_digest",
        )
        replay_id = normalize_bounded_string(
            value.replay_id,
            field_name="replay_id",
            maximum_length=_MAX_RISK_EVIDENCE_ID_LENGTH,
        )
        event_id = normalize_bounded_string(
            value.price_event_id,
            field_name="price_event_id",
            maximum_length=_MAX_RISK_EVIDENCE_ID_LENGTH,
        )
        instrument_id = normalize_market_instrument_id(value.instrument_id)
        if replay_id != value.replay_id or event_id != value.price_event_id:
            raise ValueError("price-reference IDs must already be normalized")
        if instrument_id != value.instrument_id:
            raise ValueError("price-reference instrument must be normalized")
        if type(value.cursor_position) is not int or value.cursor_position < 1:
            raise ValueError("cursor_position must be positive")
        if (
            type(value.price_event_position) is not int
            or value.price_event_position < 1
            or value.price_event_position > value.cursor_position
        ):
            raise ValueError("price_event_position must be in consumed prefix")
        event_time = normalize_utc_datetime(
            value.price_event_time,
            field_name="price_event_time",
        )
        if event_time != value.price_event_time:
            raise ValueError("price_event_time must be normalized to UTC")
        price_event_digest = validate_digest(
            value.price_event_digest,
            field_name="price_event_digest",
        )
        price = _exact_money(
            value.reference_price,
            field_name="reference_price",
            strictly_positive=True,
        )
        validate_digest(value.reference_digest, field_name="reference_digest")
        rebuilt = _build_price_reference(
            schema_version=value.schema_version,
            reference_price_policy_id=value.reference_price_policy_id,
            event_stream_digest=event_stream_digest,
            replay_id=replay_id,
            cursor_position=value.cursor_position,
            price_event_position=value.price_event_position,
            price_event_id=event_id,
            price_event_time=event_time,
            instrument_id=instrument_id,
            price_event_digest=price_event_digest,
            reference_price=price,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("pre-trade risk price reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("pre-trade risk price reference is invalid")
    return value


def _clone_price_reference(
    value: PreTradeRiskPriceReference,
) -> PreTradeRiskPriceReference:
    validate_pre_trade_risk_price_reference(value)
    return _build_price_reference(
        schema_version=value.schema_version,
        reference_price_policy_id=value.reference_price_policy_id,
        event_stream_digest=value.event_stream_digest,
        replay_id=value.replay_id,
        cursor_position=value.cursor_position,
        price_event_position=value.price_event_position,
        price_event_id=value.price_event_id,
        price_event_time=value.price_event_time,
        instrument_id=value.instrument_id,
        price_event_digest=value.price_event_digest,
        reference_price=value.reference_price,
    )


def _rule_payload_without_digest(
    *,
    schema_version: int,
    rule_code: str,
    applicable: bool,
    value_type: PreTradeRiskValueType,
    observed_value: RiskEvidenceValue,
    threshold_value: RiskEvidenceValue,
    passed: bool,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "rule_code": rule_code,
        "applicable": applicable,
        "value_type": value_type,
        "observed_value": _evidence_json_value(observed_value),
        "threshold_value": _evidence_json_value(threshold_value),
        "passed": passed,
    }


@dataclass(frozen=True, init=False)
class PreTradeRiskRuleEvidence:
    """One immutable ordered pre-trade rule result."""

    schema_version: int
    rule_code: str
    applicable: bool
    value_type: PreTradeRiskValueType
    observed_value: RiskEvidenceValue
    threshold_value: RiskEvidenceValue
    passed: bool
    rule_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return one strict-JSON rule-evidence record."""
        return {
            **_rule_payload_without_digest(
                schema_version=self.schema_version,
                rule_code=self.rule_code,
                applicable=self.applicable,
                value_type=self.value_type,
                observed_value=self.observed_value,
                threshold_value=self.threshold_value,
                passed=self.passed,
            ),
            "rule_digest": self.rule_digest,
        }


def _clone_evidence_value(
    value: RiskEvidenceValue,
    *,
    value_type: PreTradeRiskValueType,
) -> RiskEvidenceValue:
    if value is None:
        return None
    if value_type == PRE_TRADE_RISK_VALUE_TYPE_QUANTITY:
        return PaperQuantity.parse(value.canonical)
    return PaperMoney.parse(value.canonical)


def _build_rule_evidence(
    *,
    rule_code: str,
    applicable: bool,
    value_type: PreTradeRiskValueType,
    observed_value: RiskEvidenceValue,
    threshold_value: RiskEvidenceValue,
    passed: bool,
) -> PreTradeRiskRuleEvidence:
    observed = _clone_evidence_value(
        observed_value,
        value_type=value_type,
    )
    threshold = _clone_evidence_value(
        threshold_value,
        value_type=value_type,
    )
    payload = _rule_payload_without_digest(
        schema_version=PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION,
        rule_code=rule_code,
        applicable=applicable,
        value_type=value_type,
        observed_value=observed,
        threshold_value=threshold,
        passed=passed,
    )
    result = object.__new__(PreTradeRiskRuleEvidence)
    for field_name, value in (
        ("schema_version", PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION),
        ("rule_code", rule_code),
        ("applicable", applicable),
        ("value_type", value_type),
        ("observed_value", observed),
        ("threshold_value", threshold),
        ("passed", passed),
        ("rule_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def validate_pre_trade_risk_rule_evidence(
    value: object,
) -> PreTradeRiskRuleEvidence:
    """Recompute and verify one complete rule-evidence record."""
    if type(value) is not PreTradeRiskRuleEvidence:
        raise ValueError("rule must be a PreTradeRiskRuleEvidence")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported rule-evidence schema_version")
        if value.rule_code not in PRE_TRADE_RISK_RULE_ORDER:
            raise ValueError("unsupported pre-trade risk rule code")
        expected_type: PreTradeRiskValueType = (
            PRE_TRADE_RISK_VALUE_TYPE_QUANTITY
            if value.rule_code
            in (
                PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
                PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
            )
            else PRE_TRADE_RISK_VALUE_TYPE_MONEY
        )
        if value.value_type != expected_type:
            raise ValueError("rule value_type does not match rule code")
        if type(value.applicable) is not bool or type(value.passed) is not bool:
            raise ValueError("rule booleans must be concrete bool values")
        if not value.applicable:
            if (
                not value.passed
                or value.observed_value is not None
                or value.threshold_value is not None
            ):
                raise ValueError(
                    "non-applicable rule values must be null and passed"
                )
            observed = None
            threshold = None
        elif expected_type == PRE_TRADE_RISK_VALUE_TYPE_QUANTITY:
            observed = _exact_quantity(
                value.observed_value,
                field_name="observed_value",
                strictly_positive=(
                    value.rule_code == PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY
                ),
            )
            threshold = _exact_quantity(
                value.threshold_value,
                field_name="threshold_value",
                strictly_positive=True,
            )
        else:
            observed = _exact_money(
                value.observed_value,
                field_name="observed_value",
                strictly_positive=(
                    value.rule_code == PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL
                ),
            )
            threshold = _exact_money(
                value.threshold_value,
                field_name="threshold_value",
                strictly_positive=True,
            )
        if value.applicable:
            assert observed is not None
            assert threshold is not None
            if value.rule_code in (
                PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
                PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
            ):
                expected_passed = (
                    observed.decimal_value >= threshold.decimal_value
                )
            else:
                expected_passed = (
                    observed.decimal_value <= threshold.decimal_value
                )
            if value.passed != expected_passed:
                raise ValueError("rule result does not match exact values")
        validate_digest(value.rule_digest, field_name="rule_digest")
        rebuilt = _build_rule_evidence(
            rule_code=value.rule_code,
            applicable=value.applicable,
            value_type=expected_type,
            observed_value=observed,
            threshold_value=threshold,
            passed=value.passed,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("pre-trade risk rule evidence is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("pre-trade risk rule evidence is invalid")
    return value


def _create_rule_evidence(
    *,
    side: OrderIntentSide,
    requested_quantity: PaperQuantity,
    available_cash: PaperMoney,
    current_quantity: PaperQuantity,
    estimated_notional: PaperMoney,
    policy: PreTradeRiskPolicyReference,
) -> tuple[PreTradeRiskRuleEvidence, ...]:
    sell = side == ORDER_INTENT_SIDE_SELL
    buy = side == ORDER_INTENT_SIDE_BUY
    quantity_limited = policy.maximum_order_quantity is not None
    notional_limited = policy.maximum_order_notional is not None
    return (
        _build_rule_evidence(
            rule_code=PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
            applicable=sell,
            value_type=PRE_TRADE_RISK_VALUE_TYPE_QUANTITY,
            observed_value=current_quantity if sell else None,
            threshold_value=requested_quantity if sell else None,
            passed=(
                True
                if not sell
                else current_quantity.decimal_value
                >= requested_quantity.decimal_value
            ),
        ),
        _build_rule_evidence(
            rule_code=PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
            applicable=quantity_limited,
            value_type=PRE_TRADE_RISK_VALUE_TYPE_QUANTITY,
            observed_value=requested_quantity if quantity_limited else None,
            threshold_value=policy.maximum_order_quantity,
            passed=(
                True
                if policy.maximum_order_quantity is None
                else requested_quantity.decimal_value
                <= policy.maximum_order_quantity.decimal_value
            ),
        ),
        _build_rule_evidence(
            rule_code=PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL,
            applicable=notional_limited,
            value_type=PRE_TRADE_RISK_VALUE_TYPE_MONEY,
            observed_value=estimated_notional if notional_limited else None,
            threshold_value=policy.maximum_order_notional,
            passed=(
                True
                if policy.maximum_order_notional is None
                else estimated_notional.decimal_value
                <= policy.maximum_order_notional.decimal_value
            ),
        ),
        _build_rule_evidence(
            rule_code=PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
            applicable=buy,
            value_type=PRE_TRADE_RISK_VALUE_TYPE_MONEY,
            observed_value=available_cash if buy else None,
            threshold_value=estimated_notional if buy else None,
            passed=(
                True
                if not buy
                else available_cash.decimal_value
                >= estimated_notional.decimal_value
            ),
        ),
    )


def _snapshot_payload_without_identity(
    *,
    schema_version: int,
    intent_reference: OrderIntentReference,
    market_reference: StrategySignalMarketReference,
    account_reference: OrderIntentAccountReference,
    risk_policy_reference: PreTradeRiskPolicyReference,
    price_reference: PreTradeRiskPriceReference,
    side: OrderIntentSide,
    requested_quantity: PaperQuantity,
    verified_available_cash: PaperMoney,
    verified_current_instrument_quantity: PaperQuantity,
    estimated_order_notional: PaperMoney,
    rule_evidence: tuple[PreTradeRiskRuleEvidence, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "intent_reference": intent_reference.to_dict(),
        "market_reference": market_reference.to_dict(),
        "account_reference": account_reference.to_dict(),
        "risk_policy_reference": risk_policy_reference.to_dict(),
        "price_reference": price_reference.to_dict(),
        "side": side,
        "requested_quantity": requested_quantity.to_json_value(),
        "verified_available_cash": verified_available_cash.to_json_value(),
        "verified_current_instrument_quantity": (
            verified_current_instrument_quantity.to_json_value()
        ),
        "estimated_order_notional": estimated_order_notional.to_json_value(),
        "rule_evidence": [rule.to_dict() for rule in rule_evidence],
    }


@dataclass(frozen=True, init=False)
class PreTradeRiskInputSnapshot:
    """Complete immutable authority and derived evidence used by risk."""

    schema_version: int
    snapshot_id: str
    snapshot_digest: str
    intent_reference: OrderIntentReference
    market_reference: StrategySignalMarketReference
    account_reference: OrderIntentAccountReference
    risk_policy_reference: PreTradeRiskPolicyReference
    price_reference: PreTradeRiskPriceReference
    side: OrderIntentSide
    requested_quantity: PaperQuantity
    verified_available_cash: PaperMoney
    verified_current_instrument_quantity: PaperQuantity
    estimated_order_notional: PaperMoney
    rule_evidence: tuple[PreTradeRiskRuleEvidence, ...]

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON risk input snapshot."""
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "snapshot_digest": self.snapshot_digest,
            **{
                key: value
                for key, value in _snapshot_payload_without_identity(
                    schema_version=self.schema_version,
                    intent_reference=self.intent_reference,
                    market_reference=self.market_reference,
                    account_reference=self.account_reference,
                    risk_policy_reference=self.risk_policy_reference,
                    price_reference=self.price_reference,
                    side=self.side,
                    requested_quantity=self.requested_quantity,
                    verified_available_cash=self.verified_available_cash,
                    verified_current_instrument_quantity=(
                        self.verified_current_instrument_quantity
                    ),
                    estimated_order_notional=self.estimated_order_notional,
                    rule_evidence=self.rule_evidence,
                ).items()
                if key != "schema_version"
            },
        }


def _clone_rule_evidence(
    value: PreTradeRiskRuleEvidence,
) -> PreTradeRiskRuleEvidence:
    validate_pre_trade_risk_rule_evidence(value)
    return _build_rule_evidence(
        rule_code=value.rule_code,
        applicable=value.applicable,
        value_type=value.value_type,
        observed_value=value.observed_value,
        threshold_value=value.threshold_value,
        passed=value.passed,
    )


def _build_input_snapshot(
    *,
    intent_reference: OrderIntentReference,
    market_reference: StrategySignalMarketReference,
    account_reference: OrderIntentAccountReference,
    risk_policy_reference: PreTradeRiskPolicyReference,
    price_reference: PreTradeRiskPriceReference,
    side: OrderIntentSide,
    requested_quantity: PaperQuantity,
    verified_available_cash: PaperMoney,
    verified_current_instrument_quantity: PaperQuantity,
    estimated_order_notional: PaperMoney,
    rule_evidence: tuple[PreTradeRiskRuleEvidence, ...],
) -> PreTradeRiskInputSnapshot:
    intent_snapshot = _clone_order_intent_reference(intent_reference)
    market_snapshot = _clone_strategy_signal_market_reference(market_reference)
    account_snapshot = _clone_order_intent_account_reference(account_reference)
    policy_snapshot = _clone_pre_trade_risk_policy_reference(
        risk_policy_reference
    )
    price_snapshot = _clone_price_reference(price_reference)
    requested = PaperQuantity.parse(requested_quantity.canonical)
    available = PaperMoney.parse(verified_available_cash.canonical)
    current = PaperQuantity.parse(
        verified_current_instrument_quantity.canonical
    )
    notional = PaperMoney.parse(estimated_order_notional.canonical)
    rules = tuple(_clone_rule_evidence(rule) for rule in rule_evidence)
    payload = _snapshot_payload_without_identity(
        schema_version=PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION,
        intent_reference=intent_snapshot,
        market_reference=market_snapshot,
        account_reference=account_snapshot,
        risk_policy_reference=policy_snapshot,
        price_reference=price_snapshot,
        side=side,
        requested_quantity=requested,
        verified_available_cash=available,
        verified_current_instrument_quantity=current,
        estimated_order_notional=notional,
        rule_evidence=rules,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PreTradeRiskInputSnapshot)
    for field_name, value in (
        ("schema_version", PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION),
        ("snapshot_id", f"risk_input_{digest}"),
        ("snapshot_digest", digest),
        ("intent_reference", intent_snapshot),
        ("market_reference", market_snapshot),
        ("account_reference", account_snapshot),
        ("risk_policy_reference", policy_snapshot),
        ("price_reference", price_snapshot),
        ("side", side),
        ("requested_quantity", requested),
        ("verified_available_cash", available),
        ("verified_current_instrument_quantity", current),
        ("estimated_order_notional", notional),
        ("rule_evidence", rules),
    ):
        object.__setattr__(result, field_name, value)
    return result


def validate_pre_trade_risk_input_snapshot(
    value: object,
) -> PreTradeRiskInputSnapshot:
    """Recompute every nested input, rule, and deterministic identity."""
    if type(value) is not PreTradeRiskInputSnapshot:
        raise ValueError("input_snapshot must be a PreTradeRiskInputSnapshot")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION
        ):
            raise ValueError("unsupported risk input schema_version")
        validate_order_intent_reference(value.intent_reference)
        validate_strategy_signal_market_reference(value.market_reference)
        validate_order_intent_account_reference(value.account_reference)
        validate_pre_trade_risk_policy_reference(
            value.risk_policy_reference
        )
        validate_pre_trade_risk_price_reference(value.price_reference)
        if value.side not in (ORDER_INTENT_SIDE_BUY, ORDER_INTENT_SIDE_SELL):
            raise ValueError("unsupported order intent side")
        requested = _exact_quantity(
            value.requested_quantity,
            field_name="requested_quantity",
            strictly_positive=True,
        )
        available = _exact_money(
            value.verified_available_cash,
            field_name="verified_available_cash",
        )
        current = _exact_quantity(
            value.verified_current_instrument_quantity,
            field_name="verified_current_instrument_quantity",
        )
        notional = _exact_money(
            value.estimated_order_notional,
            field_name="estimated_order_notional",
            strictly_positive=True,
        )
        if available != value.account_reference.available_cash:
            raise ValueError("verified available cash does not match account")
        if current != value.account_reference.current_instrument_quantity:
            raise ValueError("verified current quantity does not match account")
        if (
            value.market_reference.instrument_id
            != value.account_reference.instrument_id
            or value.price_reference.instrument_id
            != value.market_reference.instrument_id
        ):
            raise ValueError("risk evidence instrument anchors do not match")
        if (
            value.price_reference.replay_id
            != value.market_reference.replay_id
            or value.price_reference.event_stream_digest
            != value.market_reference.event_stream_digest
            or value.price_reference.cursor_position
            != value.market_reference.cursor_position
        ):
            raise ValueError("price and market replay anchors do not match")
        if (
            value.price_reference.reference_price_policy_id
            != value.risk_policy_reference.reference_price_policy_id
        ):
            raise ValueError("price and risk policy references do not match")
        expected_notional = _money_from_decimal(
            requested.decimal_value
            * value.price_reference.reference_price.decimal_value
        )
        if notional != expected_notional:
            raise ValueError("estimated order notional is invalid")
        if type(value.rule_evidence) is not tuple:
            raise ValueError("rule_evidence must be an immutable tuple")
        for rule in value.rule_evidence:
            validate_pre_trade_risk_rule_evidence(rule)
        expected_rules = _create_rule_evidence(
            side=value.side,
            requested_quantity=requested,
            available_cash=available,
            current_quantity=current,
            estimated_notional=notional,
            policy=value.risk_policy_reference,
        )
        if value.rule_evidence != expected_rules:
            raise ValueError("ordered pre-trade rule evidence is invalid")
        validate_digest(value.snapshot_digest, field_name="snapshot_digest")
        rebuilt = _build_input_snapshot(
            intent_reference=value.intent_reference,
            market_reference=value.market_reference,
            account_reference=value.account_reference,
            risk_policy_reference=value.risk_policy_reference,
            price_reference=value.price_reference,
            side=value.side,
            requested_quantity=requested,
            verified_available_cash=available,
            verified_current_instrument_quantity=current,
            estimated_order_notional=notional,
            rule_evidence=expected_rules,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("pre-trade risk input snapshot is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("pre-trade risk input snapshot is invalid")
    return value


def _clone_input_snapshot(
    value: PreTradeRiskInputSnapshot,
) -> PreTradeRiskInputSnapshot:
    validate_pre_trade_risk_input_snapshot(value)
    return _build_input_snapshot(
        intent_reference=value.intent_reference,
        market_reference=value.market_reference,
        account_reference=value.account_reference,
        risk_policy_reference=value.risk_policy_reference,
        price_reference=value.price_reference,
        side=value.side,
        requested_quantity=value.requested_quantity,
        verified_available_cash=value.verified_available_cash,
        verified_current_instrument_quantity=(
            value.verified_current_instrument_quantity
        ),
        estimated_order_notional=value.estimated_order_notional,
        rule_evidence=value.rule_evidence,
    )
