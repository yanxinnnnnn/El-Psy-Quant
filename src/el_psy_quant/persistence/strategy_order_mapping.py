"""Strict canonical reconstruction and row mapping for durable M33 authority."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeVar, cast

from el_psy_quant.paper_account import PaperMoney, PaperQuantity
from el_psy_quant.persistence.strategy_order_model import (
    OrderIntentRow,
    PreTradeRiskDecisionRow,
    StrategyOrderCommandReceiptRow,
    StrategySignalRow,
)
from el_psy_quant.persistence.strategy_order_records import (
    RESULT_KIND_DECISION,
    RESULT_KIND_INTENT,
    RESULT_KIND_NO_ACTION,
    RESULT_KIND_SIGNAL,
    STRATEGY_ORDER_PERSISTENCE_RECORD_SCHEMA_VERSION,
    StrategyOrderCommandReceipt,
    StrategyOrderCorruptAuthorityError,
    canonical_json,
    load_canonical_json,
)
from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentAccountReference,
    OrderIntentNoAction,
    OrderIntentReference,
    PreTradeRiskDecision,
    PreTradeRiskInputSnapshot,
    PreTradeRiskPolicyReference,
    PreTradeRiskPriceReference,
    PreTradeRiskRuleEvidence,
    StrategyRuntimeReference,
    StrategySignal,
    StrategySignalMarketReference,
    StrategySignalReference,
    validate_order_intent,
    validate_order_intent_account_reference,
    validate_order_intent_no_action,
    validate_order_intent_reference,
    validate_pre_trade_risk_decision,
    validate_pre_trade_risk_input_snapshot,
    validate_pre_trade_risk_policy_reference,
    validate_pre_trade_risk_price_reference,
    validate_pre_trade_risk_rule_evidence,
    validate_strategy_runtime_reference,
    validate_strategy_signal,
    validate_strategy_signal_market_reference,
    validate_strategy_signal_reference,
)

T = TypeVar("T")


def _dict(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise ValueError("object fields are invalid")
    return cast(dict[str, object], value)


def _list(value: object, length: int | None = None) -> list[object]:
    if type(value) is not list or (length is not None and len(value) != length):
        raise ValueError("array is invalid")
    return cast(list[object], value)


def _str(value: object) -> str:
    if type(value) is not str:
        raise ValueError("string is invalid")
    return value


def _int(value: object) -> int:
    if type(value) is not int:
        raise ValueError("integer is invalid")
    return value


def _bool(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("boolean is invalid")
    return value


def _time(value: object) -> datetime:
    text = _str(value)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None or parsed.isoformat() != text:
        raise ValueError("timestamp is invalid")
    normalized = parsed.astimezone(timezone.utc)
    if normalized != parsed:
        raise ValueError("timestamp is not UTC")
    return normalized


def _sqlite_time(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("stored timestamp is invalid")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _money(value: object) -> PaperMoney:
    return PaperMoney.parse(_str(value))


def _quantity(value: object) -> PaperQuantity:
    return PaperQuantity.parse(_str(value))


def _optional_money(value: object) -> PaperMoney | None:
    return None if value is None else _money(value)


def _optional_quantity(value: object) -> PaperQuantity | None:
    return None if value is None else _quantity(value)


def _new(cls: type[T], values: dict[str, object]) -> T:
    result = object.__new__(cls)
    for field, value in values.items():
        object.__setattr__(result, field, value)
    return result


def _runtime(value: object) -> StrategyRuntimeReference:
    payload = _dict(
        value,
        {
            "schema_version",
            "strategy_name",
            "strategy_version",
            "adapter_version",
            "runtime_sizing_semantics",
            "parameters",
            "parameters_digest",
            "reference_digest",
        },
    )
    parameters = _dict(
        payload["parameters"],
        {"fast_window", "slow_window", "target_position_quantity"},
    )
    result = _new(
        StrategyRuntimeReference,
        {
            "schema_version": _int(payload["schema_version"]),
            "strategy_name": _str(payload["strategy_name"]),
            "strategy_version": _str(payload["strategy_version"]),
            "adapter_version": _str(payload["adapter_version"]),
            "runtime_sizing_semantics": _str(
                payload["runtime_sizing_semantics"]
            ),
            "_parameters_json": canonical_json(parameters),
            "parameters_digest": _str(payload["parameters_digest"]),
            "reference_digest": _str(payload["reference_digest"]),
        },
    )
    return validate_strategy_runtime_reference(result)


def _market(value: object) -> StrategySignalMarketReference:
    fields = {
        "schema_version",
        "calendar_id",
        "calendar_version",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "last_event_id",
        "signal_event_id",
        "signal_time",
        "instrument_id",
        "reference_digest",
    }
    p = _dict(value, fields)
    result = _new(
        StrategySignalMarketReference,
        {
            "schema_version": _int(p["schema_version"]),
            "calendar_id": _str(p["calendar_id"]),
            "calendar_version": _int(p["calendar_version"]),
            "trading_session_id": _str(p["trading_session_id"]),
            "replay_id": _str(p["replay_id"]),
            "event_stream_digest": _str(p["event_stream_digest"]),
            "cursor_position": _int(p["cursor_position"]),
            "last_event_id": _str(p["last_event_id"]),
            "signal_event_id": _str(p["signal_event_id"]),
            "signal_time": _time(p["signal_time"]),
            "instrument_id": _str(p["instrument_id"]),
            "reference_digest": _str(p["reference_digest"]),
        },
    )
    return validate_strategy_signal_market_reference(result)


def _signal_reference(value: object) -> StrategySignalReference:
    p = _dict(value, {"schema_version", "signal_id", "signal_digest"})
    result = _new(
        StrategySignalReference,
        {
            "schema_version": _int(p["schema_version"]),
            "signal_id": _str(p["signal_id"]),
            "signal_digest": _str(p["signal_digest"]),
        },
    )
    return validate_strategy_signal_reference(result)


def _intent_reference(value: object) -> OrderIntentReference:
    p = _dict(value, {"schema_version", "intent_id", "intent_digest"})
    result = _new(
        OrderIntentReference,
        {
            "schema_version": _int(p["schema_version"]),
            "intent_id": _str(p["intent_id"]),
            "intent_digest": _str(p["intent_digest"]),
        },
    )
    return validate_order_intent_reference(result)


def _account(value: object) -> OrderIntentAccountReference:
    fields = {
        "schema_version",
        "account_id",
        "base_currency",
        "lifecycle_status",
        "account_head_version",
        "account_head_event_id",
        "account_head_chain_digest",
        "cash_balance",
        "available_cash",
        "instrument_id",
        "current_instrument_quantity",
        "reference_digest",
    }
    p = _dict(value, fields)
    result = _new(
        OrderIntentAccountReference,
        {
            "schema_version": _int(p["schema_version"]),
            "account_id": _str(p["account_id"]),
            "base_currency": _str(p["base_currency"]),
            "lifecycle_status": _str(p["lifecycle_status"]),
            "account_head_version": _int(p["account_head_version"]),
            "account_head_event_id": _str(p["account_head_event_id"]),
            "account_head_chain_digest": _str(
                p["account_head_chain_digest"]
            ),
            "cash_balance": _money(p["cash_balance"]),
            "available_cash": _money(p["available_cash"]),
            "instrument_id": _str(p["instrument_id"]),
            "current_instrument_quantity": _quantity(
                p["current_instrument_quantity"]
            ),
            "reference_digest": _str(p["reference_digest"]),
        },
    )
    return validate_order_intent_account_reference(result)


def _policy(value: object) -> PreTradeRiskPolicyReference:
    fields = {
        "schema_version",
        "policy_id",
        "reference_price_policy_id",
        "maximum_order_quantity",
        "maximum_order_notional",
        "configuration_digest",
        "reference_digest",
    }
    p = _dict(value, fields)
    result = _new(
        PreTradeRiskPolicyReference,
        {
            "schema_version": _int(p["schema_version"]),
            "policy_id": _str(p["policy_id"]),
            "reference_price_policy_id": _str(
                p["reference_price_policy_id"]
            ),
            "maximum_order_quantity": _optional_quantity(
                p["maximum_order_quantity"]
            ),
            "maximum_order_notional": _optional_money(
                p["maximum_order_notional"]
            ),
            "configuration_digest": _str(p["configuration_digest"]),
            "reference_digest": _str(p["reference_digest"]),
        },
    )
    return validate_pre_trade_risk_policy_reference(result)


def _price(value: object) -> PreTradeRiskPriceReference:
    fields = {
        "schema_version",
        "reference_price_policy_id",
        "event_stream_digest",
        "replay_id",
        "cursor_position",
        "price_event_position",
        "price_event_id",
        "price_event_time",
        "instrument_id",
        "price_event_digest",
        "reference_price",
        "reference_digest",
    }
    p = _dict(value, fields)
    result = _new(
        PreTradeRiskPriceReference,
        {
            "schema_version": _int(p["schema_version"]),
            "reference_price_policy_id": _str(
                p["reference_price_policy_id"]
            ),
            "event_stream_digest": _str(p["event_stream_digest"]),
            "replay_id": _str(p["replay_id"]),
            "cursor_position": _int(p["cursor_position"]),
            "price_event_position": _int(p["price_event_position"]),
            "price_event_id": _str(p["price_event_id"]),
            "price_event_time": _time(p["price_event_time"]),
            "instrument_id": _str(p["instrument_id"]),
            "price_event_digest": _str(p["price_event_digest"]),
            "reference_price": _money(p["reference_price"]),
            "reference_digest": _str(p["reference_digest"]),
        },
    )
    return validate_pre_trade_risk_price_reference(result)


def _rule(value: object) -> PreTradeRiskRuleEvidence:
    fields = {
        "schema_version",
        "rule_code",
        "applicable",
        "value_type",
        "observed_value",
        "threshold_value",
        "passed",
        "rule_digest",
    }
    p = _dict(value, fields)
    value_type = _str(p["value_type"])
    parser = _quantity if value_type == "quantity" else _money
    observed = None if p["observed_value"] is None else parser(p["observed_value"])
    threshold = (
        None if p["threshold_value"] is None else parser(p["threshold_value"])
    )
    result = _new(
        PreTradeRiskRuleEvidence,
        {
            "schema_version": _int(p["schema_version"]),
            "rule_code": _str(p["rule_code"]),
            "applicable": _bool(p["applicable"]),
            "value_type": value_type,
            "observed_value": observed,
            "threshold_value": threshold,
            "passed": _bool(p["passed"]),
            "rule_digest": _str(p["rule_digest"]),
        },
    )
    return validate_pre_trade_risk_rule_evidence(result)


def _snapshot(value: object) -> PreTradeRiskInputSnapshot:
    fields = {
        "schema_version",
        "snapshot_id",
        "snapshot_digest",
        "intent_reference",
        "market_reference",
        "account_reference",
        "risk_policy_reference",
        "price_reference",
        "side",
        "requested_quantity",
        "verified_available_cash",
        "verified_current_instrument_quantity",
        "estimated_order_notional",
        "rule_evidence",
    }
    p = _dict(value, fields)
    result = _new(
        PreTradeRiskInputSnapshot,
        {
            "schema_version": _int(p["schema_version"]),
            "snapshot_id": _str(p["snapshot_id"]),
            "snapshot_digest": _str(p["snapshot_digest"]),
            "intent_reference": _intent_reference(p["intent_reference"]),
            "market_reference": _market(p["market_reference"]),
            "account_reference": _account(p["account_reference"]),
            "risk_policy_reference": _policy(p["risk_policy_reference"]),
            "price_reference": _price(p["price_reference"]),
            "side": _str(p["side"]),
            "requested_quantity": _quantity(p["requested_quantity"]),
            "verified_available_cash": _money(p["verified_available_cash"]),
            "verified_current_instrument_quantity": _quantity(
                p["verified_current_instrument_quantity"]
            ),
            "estimated_order_notional": _money(
                p["estimated_order_notional"]
            ),
            "rule_evidence": tuple(
                _rule(item) for item in _list(p["rule_evidence"], 4)
            ),
        },
    )
    return validate_pre_trade_risk_input_snapshot(result)


def strategy_signal_from_payload(value: object) -> StrategySignal:
    """Strictly reconstruct and revalidate one complete Strategy Signal."""
    fields = {
        "schema_version",
        "signal_id",
        "signal_digest",
        "strategy_runtime_reference",
        "market_reference",
        "target_semantics",
        "target_position_quantity",
        "created_at",
    }
    try:
        p = _dict(value, fields)
        result = _new(
            StrategySignal,
            {
                "schema_version": _int(p["schema_version"]),
                "signal_id": _str(p["signal_id"]),
                "signal_digest": _str(p["signal_digest"]),
                "strategy_runtime_reference": _runtime(
                    p["strategy_runtime_reference"]
                ),
                "market_reference": _market(p["market_reference"]),
                "target_semantics": _str(p["target_semantics"]),
                "target_position_quantity": _quantity(
                    p["target_position_quantity"]
                ),
                "created_at": _time(p["created_at"]),
            },
        )
        return validate_strategy_signal(result)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def order_intent_from_payload(value: object) -> OrderIntent:
    """Strictly reconstruct and revalidate one complete Order Intent."""
    fields = {
        "schema_version",
        "intent_id",
        "intent_digest",
        "signal_reference",
        "market_reference",
        "account_reference",
        "target_semantics",
        "target_position_quantity",
        "current_position_quantity",
        "side",
        "requested_quantity",
        "intent_policy_version",
        "origin_command_idempotency_key",
        "origin_command_digest",
        "origin_actor",
        "created_at",
    }
    try:
        p = _dict(value, fields)
        result = _new(
            OrderIntent,
            {
                "schema_version": _int(p["schema_version"]),
                "intent_id": _str(p["intent_id"]),
                "intent_digest": _str(p["intent_digest"]),
                "signal_reference": _signal_reference(p["signal_reference"]),
                "market_reference": _market(p["market_reference"]),
                "account_reference": _account(p["account_reference"]),
                "target_semantics": _str(p["target_semantics"]),
                "target_position_quantity": _quantity(
                    p["target_position_quantity"]
                ),
                "current_position_quantity": _quantity(
                    p["current_position_quantity"]
                ),
                "side": _str(p["side"]),
                "requested_quantity": _quantity(p["requested_quantity"]),
                "intent_policy_version": _str(p["intent_policy_version"]),
                "origin_command_idempotency_key": _str(
                    p["origin_command_idempotency_key"]
                ),
                "origin_command_digest": _str(p["origin_command_digest"]),
                "origin_actor": _str(p["origin_actor"]),
                "created_at": _time(p["created_at"]),
            },
        )
        return validate_order_intent(result)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def order_intent_no_action_from_payload(value: object) -> OrderIntentNoAction:
    """Strictly reconstruct deterministic no-action evidence."""
    fields = {
        "schema_version",
        "no_action_id",
        "no_action_digest",
        "reason_code",
        "signal_reference",
        "market_reference",
        "account_reference",
        "target_semantics",
        "target_position_quantity",
        "current_position_quantity",
        "intent_policy_version",
        "origin_command_idempotency_key",
        "origin_command_digest",
        "origin_actor",
        "created_at",
    }
    try:
        p = _dict(value, fields)
        result = _new(
            OrderIntentNoAction,
            {
                "schema_version": _int(p["schema_version"]),
                "no_action_id": _str(p["no_action_id"]),
                "no_action_digest": _str(p["no_action_digest"]),
                "reason_code": _str(p["reason_code"]),
                "signal_reference": _signal_reference(p["signal_reference"]),
                "market_reference": _market(p["market_reference"]),
                "account_reference": _account(p["account_reference"]),
                "target_semantics": _str(p["target_semantics"]),
                "target_position_quantity": _quantity(
                    p["target_position_quantity"]
                ),
                "current_position_quantity": _quantity(
                    p["current_position_quantity"]
                ),
                "intent_policy_version": _str(p["intent_policy_version"]),
                "origin_command_idempotency_key": _str(
                    p["origin_command_idempotency_key"]
                ),
                "origin_command_digest": _str(p["origin_command_digest"]),
                "origin_actor": _str(p["origin_actor"]),
                "created_at": _time(p["created_at"]),
            },
        )
        return validate_order_intent_no_action(result)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def pre_trade_risk_decision_from_payload(value: object) -> PreTradeRiskDecision:
    """Strictly reconstruct a decision and every nested evidence record."""
    fields = {
        "schema_version",
        "decision_id",
        "decision_digest",
        "input_snapshot",
        "outcome",
        "reason_codes",
        "origin_command_idempotency_key",
        "origin_command_digest",
        "origin_actor",
        "created_at",
    }
    try:
        p = _dict(value, fields)
        result = _new(
            PreTradeRiskDecision,
            {
                "schema_version": _int(p["schema_version"]),
                "decision_id": _str(p["decision_id"]),
                "decision_digest": _str(p["decision_digest"]),
                "input_snapshot": _snapshot(p["input_snapshot"]),
                "outcome": _str(p["outcome"]),
                "reason_codes": tuple(
                    _str(item) for item in _list(p["reason_codes"])
                ),
                "origin_command_idempotency_key": _str(
                    p["origin_command_idempotency_key"]
                ),
                "origin_command_digest": _str(p["origin_command_digest"]),
                "origin_actor": _str(p["origin_actor"]),
                "created_at": _time(p["created_at"]),
            },
        )
        return validate_pre_trade_risk_decision(result)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def signal_row(signal: StrategySignal) -> StrategySignalRow:
    signal = validate_strategy_signal(signal)
    runtime = signal.strategy_runtime_reference
    market = signal.market_reference
    return StrategySignalRow(
        record_schema_version=STRATEGY_ORDER_PERSISTENCE_RECORD_SCHEMA_VERSION,
        signal_schema_version=signal.schema_version,
        signal_id=signal.signal_id,
        signal_digest=signal.signal_digest,
        payload_json=canonical_json(signal.to_dict()),
        strategy_name=runtime.strategy_name,
        strategy_version=runtime.strategy_version,
        adapter_version=runtime.adapter_version,
        parameters_digest=runtime.parameters_digest,
        calendar_id=market.calendar_id,
        calendar_version=market.calendar_version,
        trading_session_id=market.trading_session_id,
        replay_id=market.replay_id,
        event_stream_digest=market.event_stream_digest,
        cursor_position=market.cursor_position,
        signal_event_id=market.signal_event_id,
        instrument_id=market.instrument_id,
        target_semantics=signal.target_semantics,
        target_position_quantity=signal.target_position_quantity.canonical,
        created_at=signal.created_at,
    )


def signal_from_row(row: StrategySignalRow) -> StrategySignal:
    try:
        signal = strategy_signal_from_payload(load_canonical_json(row.payload_json))
        runtime = signal.strategy_runtime_reference
        market = signal.market_reference
        actual = (
            row.record_schema_version,
            row.signal_schema_version,
            row.signal_id,
            row.signal_digest,
            row.strategy_name,
            row.strategy_version,
            row.adapter_version,
            row.parameters_digest,
            row.calendar_id,
            row.calendar_version,
            row.trading_session_id,
            row.replay_id,
            row.event_stream_digest,
            row.cursor_position,
            row.signal_event_id,
            row.instrument_id,
            row.target_semantics,
            row.target_position_quantity,
            _sqlite_time(row.created_at),
        )
        expected = (
            1,
            signal.schema_version,
            signal.signal_id,
            signal.signal_digest,
            runtime.strategy_name,
            runtime.strategy_version,
            runtime.adapter_version,
            runtime.parameters_digest,
            market.calendar_id,
            market.calendar_version,
            market.trading_session_id,
            market.replay_id,
            market.event_stream_digest,
            market.cursor_position,
            market.signal_event_id,
            market.instrument_id,
            signal.target_semantics,
            signal.target_position_quantity.canonical,
            signal.created_at,
        )
        if actual != expected:
            raise ValueError("signal metadata mismatch")
        return signal
    except StrategyOrderCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def intent_row(intent: OrderIntent) -> OrderIntentRow:
    intent = validate_order_intent(intent)
    market = intent.market_reference
    account = intent.account_reference
    return OrderIntentRow(
        record_schema_version=1,
        intent_schema_version=intent.schema_version,
        intent_id=intent.intent_id,
        intent_digest=intent.intent_digest,
        payload_json=canonical_json(intent.to_dict()),
        signal_id=intent.signal_reference.signal_id,
        signal_digest=intent.signal_reference.signal_digest,
        account_id=account.account_id,
        account_head_version=account.account_head_version,
        account_head_event_id=account.account_head_event_id,
        account_head_chain_digest=account.account_head_chain_digest,
        calendar_id=market.calendar_id,
        trading_session_id=market.trading_session_id,
        replay_id=market.replay_id,
        event_stream_digest=market.event_stream_digest,
        cursor_position=market.cursor_position,
        current_event_id=market.signal_event_id,
        instrument_id=market.instrument_id,
        side=intent.side,
        requested_quantity=intent.requested_quantity.canonical,
        target_position_quantity=intent.target_position_quantity.canonical,
        current_position_quantity=intent.current_position_quantity.canonical,
        intent_policy_version=intent.intent_policy_version,
        created_at=intent.created_at,
    )


def intent_from_row(row: OrderIntentRow) -> OrderIntent:
    try:
        intent = order_intent_from_payload(load_canonical_json(row.payload_json))
        market = intent.market_reference
        account = intent.account_reference
        actual = (
            row.record_schema_version,
            row.intent_schema_version,
            row.intent_id,
            row.intent_digest,
            row.signal_id,
            row.signal_digest,
            row.account_id,
            row.account_head_version,
            row.account_head_event_id,
            row.account_head_chain_digest,
            row.calendar_id,
            row.trading_session_id,
            row.replay_id,
            row.event_stream_digest,
            row.cursor_position,
            row.current_event_id,
            row.instrument_id,
            row.side,
            row.requested_quantity,
            row.target_position_quantity,
            row.current_position_quantity,
            row.intent_policy_version,
            _sqlite_time(row.created_at),
        )
        expected = (
            1,
            intent.schema_version,
            intent.intent_id,
            intent.intent_digest,
            intent.signal_reference.signal_id,
            intent.signal_reference.signal_digest,
            account.account_id,
            account.account_head_version,
            account.account_head_event_id,
            account.account_head_chain_digest,
            market.calendar_id,
            market.trading_session_id,
            market.replay_id,
            market.event_stream_digest,
            market.cursor_position,
            market.signal_event_id,
            market.instrument_id,
            intent.side,
            intent.requested_quantity.canonical,
            intent.target_position_quantity.canonical,
            intent.current_position_quantity.canonical,
            intent.intent_policy_version,
            intent.created_at,
        )
        if actual != expected:
            raise ValueError("intent metadata mismatch")
        return intent
    except StrategyOrderCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def decision_row(decision: PreTradeRiskDecision) -> PreTradeRiskDecisionRow:
    decision = validate_pre_trade_risk_decision(decision)
    snapshot = decision.input_snapshot
    market = snapshot.market_reference
    account = snapshot.account_reference
    return PreTradeRiskDecisionRow(
        record_schema_version=1,
        decision_schema_version=decision.schema_version,
        decision_id=decision.decision_id,
        decision_digest=decision.decision_digest,
        payload_json=canonical_json(decision.to_dict()),
        snapshot_id=snapshot.snapshot_id,
        snapshot_digest=snapshot.snapshot_digest,
        intent_id=snapshot.intent_reference.intent_id,
        intent_digest=snapshot.intent_reference.intent_digest,
        account_id=account.account_id,
        account_head_version=account.account_head_version,
        account_head_event_id=account.account_head_event_id,
        account_head_chain_digest=account.account_head_chain_digest,
        calendar_id=market.calendar_id,
        trading_session_id=market.trading_session_id,
        replay_id=market.replay_id,
        event_stream_digest=market.event_stream_digest,
        cursor_position=market.cursor_position,
        current_event_id=market.signal_event_id,
        instrument_id=market.instrument_id,
        risk_policy_id=snapshot.risk_policy_reference.policy_id,
        risk_policy_configuration_digest=(
            snapshot.risk_policy_reference.configuration_digest
        ),
        outcome=decision.outcome,
        reason_codes_json=canonical_json(list(decision.reason_codes)),
        created_at=decision.created_at,
    )


def decision_from_row(row: PreTradeRiskDecisionRow) -> PreTradeRiskDecision:
    try:
        decision = pre_trade_risk_decision_from_payload(
            load_canonical_json(row.payload_json)
        )
        snapshot = decision.input_snapshot
        market = snapshot.market_reference
        account = snapshot.account_reference
        actual = (
            row.record_schema_version,
            row.decision_schema_version,
            row.decision_id,
            row.decision_digest,
            row.snapshot_id,
            row.snapshot_digest,
            row.intent_id,
            row.intent_digest,
            row.account_id,
            row.account_head_version,
            row.account_head_event_id,
            row.account_head_chain_digest,
            row.calendar_id,
            row.trading_session_id,
            row.replay_id,
            row.event_stream_digest,
            row.cursor_position,
            row.current_event_id,
            row.instrument_id,
            row.risk_policy_id,
            row.risk_policy_configuration_digest,
            row.outcome,
            row.reason_codes_json,
            _sqlite_time(row.created_at),
        )
        expected = (
            1,
            decision.schema_version,
            decision.decision_id,
            decision.decision_digest,
            snapshot.snapshot_id,
            snapshot.snapshot_digest,
            snapshot.intent_reference.intent_id,
            snapshot.intent_reference.intent_digest,
            account.account_id,
            account.account_head_version,
            account.account_head_event_id,
            account.account_head_chain_digest,
            market.calendar_id,
            market.trading_session_id,
            market.replay_id,
            market.event_stream_digest,
            market.cursor_position,
            market.signal_event_id,
            market.instrument_id,
            snapshot.risk_policy_reference.policy_id,
            snapshot.risk_policy_reference.configuration_digest,
            decision.outcome,
            canonical_json(list(decision.reason_codes)),
            decision.created_at,
        )
        if actual != expected:
            raise ValueError("decision metadata mismatch")
        return decision
    except StrategyOrderCorruptAuthorityError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def receipt_row(receipt: StrategyOrderCommandReceipt) -> StrategyOrderCommandReceiptRow:
    if type(receipt) is not StrategyOrderCommandReceipt:
        raise ValueError("receipt must be StrategyOrderCommandReceipt")
    return StrategyOrderCommandReceiptRow(
        record_schema_version=receipt.record_schema_version,
        namespace=receipt.namespace,
        command_idempotency_key=receipt.command_idempotency_key,
        command_digest=receipt.command_digest,
        command_actor=receipt.command_actor,
        result_kind=receipt.result_kind,
        result_id=receipt.result_id,
        result_digest=receipt.result_digest,
        result_payload_json=receipt.result_payload_json,
        created_at=receipt.created_at,
    )


def receipt_from_row(
    row: StrategyOrderCommandReceiptRow,
) -> StrategyOrderCommandReceipt:
    try:
        return StrategyOrderCommandReceipt(
            record_schema_version=row.record_schema_version,
            namespace=cast(Any, row.namespace),
            command_idempotency_key=row.command_idempotency_key,
            command_digest=row.command_digest,
            command_actor=row.command_actor,
            result_kind=cast(Any, row.result_kind),
            result_id=row.result_id,
            result_digest=row.result_digest,
            result_payload_json=row.result_payload_json,
            created_at=_sqlite_time(row.created_at),
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise StrategyOrderCorruptAuthorityError() from exc


def result_identity(result: object) -> tuple[str, str, str]:
    if type(result) is StrategySignal:
        return RESULT_KIND_SIGNAL, result.signal_id, result.signal_digest
    if type(result) is OrderIntent:
        return RESULT_KIND_INTENT, result.intent_id, result.intent_digest
    if type(result) is OrderIntentNoAction:
        return (
            RESULT_KIND_NO_ACTION,
            result.no_action_id,
            result.no_action_digest,
        )
    if type(result) is PreTradeRiskDecision:
        return RESULT_KIND_DECISION, result.decision_id, result.decision_digest
    raise ValueError("unsupported strategy-order result")


__all__ = [
    "decision_from_row",
    "decision_row",
    "intent_from_row",
    "intent_row",
    "order_intent_from_payload",
    "order_intent_no_action_from_payload",
    "pre_trade_risk_decision_from_payload",
    "receipt_from_row",
    "receipt_row",
    "result_identity",
    "signal_from_row",
    "signal_row",
    "strategy_signal_from_payload",
]
