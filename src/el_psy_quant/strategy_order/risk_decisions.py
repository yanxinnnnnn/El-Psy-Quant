"""Pure deterministic pre-trade risk evaluation and decision evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    TradingCalendar,
    TradingSession,
)
from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PaperAccountLedgerState,
    validate_paper_account_ledger_state,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.account_references import (
    _create_order_intent_account_reference_from_instrument,
)
from el_psy_quant.strategy_order.market_references import (
    create_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.order_intents import (
    OrderIntent,
    create_order_intent_reference,
    validate_order_intent,
)
from el_psy_quant.strategy_order.risk_commands import (
    EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
    EvaluatePreTradeRiskCommand,
    _evaluate_pre_trade_risk_command_digest,
    validate_evaluate_pre_trade_risk_command,
)
from el_psy_quant.strategy_order.risk_evidence import (
    PRE_TRADE_RISK_RULE_ORDER,
    PreTradeRiskInputSnapshot,
    _build_input_snapshot,
    _clone_input_snapshot,
    _create_latest_trade_price_reference,
    _create_rule_evidence,
    _money_from_decimal,
    validate_pre_trade_risk_input_snapshot,
)

PRE_TRADE_RISK_DECISION_SCHEMA_VERSION = 1
PRE_TRADE_RISK_OUTCOME_ALLOW = "allow"
PRE_TRADE_RISK_OUTCOME_REJECT = "reject"
SUPPORTED_PRE_TRADE_RISK_OUTCOMES = (
    PRE_TRADE_RISK_OUTCOME_ALLOW,
    PRE_TRADE_RISK_OUTCOME_REJECT,
)

PreTradeRiskOutcome = Literal["allow", "reject"]


def _decision_payload_without_identity(
    *,
    schema_version: int,
    input_snapshot: PreTradeRiskInputSnapshot,
    outcome: PreTradeRiskOutcome,
    reason_codes: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "input_snapshot": input_snapshot.to_dict(),
        "outcome": outcome,
        "reason_codes": list(reason_codes),
    }


@dataclass(frozen=True, init=False)
class PreTradeRiskDecision:
    """One immutable allow/reject result over an exact input snapshot."""

    schema_version: int
    decision_id: str
    decision_digest: str
    input_snapshot: PreTradeRiskInputSnapshot
    outcome: PreTradeRiskOutcome
    reason_codes: tuple[str, ...]
    origin_command_idempotency_key: str
    origin_command_digest: str
    origin_actor: str
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON decision contract."""
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "decision_digest": self.decision_digest,
            "input_snapshot": self.input_snapshot.to_dict(),
            "outcome": self.outcome,
            "reason_codes": list(self.reason_codes),
            "origin_command_idempotency_key": (
                self.origin_command_idempotency_key
            ),
            "origin_command_digest": self.origin_command_digest,
            "origin_actor": self.origin_actor,
            "created_at": self.created_at.isoformat(),
        }


def _build_decision(
    *,
    input_snapshot: PreTradeRiskInputSnapshot,
    outcome: PreTradeRiskOutcome,
    reason_codes: tuple[str, ...],
    origin_command_idempotency_key: str,
    origin_command_digest: str,
    origin_actor: str,
    created_at: datetime,
) -> PreTradeRiskDecision:
    snapshot = _clone_input_snapshot(input_snapshot)
    reasons = tuple(reason_codes)
    payload = _decision_payload_without_identity(
        schema_version=PRE_TRADE_RISK_DECISION_SCHEMA_VERSION,
        input_snapshot=snapshot,
        outcome=outcome,
        reason_codes=reasons,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PreTradeRiskDecision)
    for field_name, value in (
        ("schema_version", PRE_TRADE_RISK_DECISION_SCHEMA_VERSION),
        ("decision_id", f"risk_decision_{digest}"),
        ("decision_digest", digest),
        ("input_snapshot", snapshot),
        ("outcome", outcome),
        ("reason_codes", reasons),
        (
            "origin_command_idempotency_key",
            origin_command_idempotency_key,
        ),
        ("origin_command_digest", origin_command_digest),
        ("origin_actor", origin_actor),
        ("created_at", created_at),
    ):
        object.__setattr__(result, field_name, value)
    return result


def _validate_replay_engine(
    value: object,
) -> MarketDataReplayEngine:
    if type(value) is not MarketDataReplayEngine:
        raise ValueError("replay_engine must be a MarketDataReplayEngine")
    try:
        events = value.events
        cursor = value.cursor
        if type(events) is not tuple:
            raise ValueError("replay events must be an immutable tuple")
        rebuilt = MarketDataReplayEngine(
            replay_id=cursor.replay_id,
            events=events,
            cursor=cursor,
        )
        session = value.session
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(
            "replay_engine must be a valid MarketDataReplayEngine"
        ) from exc
    if (
        rebuilt.events != events
        or rebuilt.cursor != cursor
        or rebuilt.session != session
    ):
        raise ValueError("replay_engine must be a valid MarketDataReplayEngine")
    return value


def evaluate_pre_trade_risk(
    command: EvaluatePreTradeRiskCommand,
    *,
    intent: OrderIntent,
    account_state: PaperAccountLedgerState,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
    created_at: datetime,
) -> PreTradeRiskDecision:
    """Evaluate one exact intent without mutating any bound authority."""
    valid_command = validate_evaluate_pre_trade_risk_command(command)
    valid_intent = validate_order_intent(intent)
    validate_paper_account_ledger_state(account_state)
    valid_engine = _validate_replay_engine(replay_engine)

    recreated_intent = create_order_intent_reference(valid_intent)
    if (
        recreated_intent != valid_command.intent_reference
        or recreated_intent.to_dict()
        != valid_command.intent_reference.to_dict()
    ):
        raise ValueError("pre-trade risk command intent is stale or mismatched")

    recreated_account = (
        _create_order_intent_account_reference_from_instrument(
            instrument_id=valid_intent.market_reference.instrument_id,
            account_state=account_state,
        )
    )
    if (
        recreated_account != valid_intent.account_reference
        or recreated_account.to_dict()
        != valid_intent.account_reference.to_dict()
    ):
        raise ValueError("pre-trade risk account authority is stale or mismatched")

    cursor = valid_engine.cursor
    if cursor.position <= 0:
        raise ValueError("pre-trade risk replay must have a consumed event")
    current_event = valid_engine.events[cursor.position - 1]
    recreated_market = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=valid_engine.session,
        current_event=current_event,
    )
    if (
        recreated_market != valid_intent.market_reference
        or recreated_market.to_dict()
        != valid_intent.market_reference.to_dict()
    ):
        raise ValueError("pre-trade risk market authority is stale or mismatched")

    policy = valid_command.risk_policy_reference
    price_reference = _create_latest_trade_price_reference(
        replay_engine=valid_engine,
        market_reference=recreated_market,
    )
    try:
        estimated_notional = _money_from_decimal(
            valid_intent.requested_quantity.decimal_value
            * price_reference.reference_price.decimal_value
        )
    except ValueError as exc:
        raise ValueError(
            "estimated order notional is not exactly representable"
        ) from exc
    if estimated_notional.decimal_value <= 0:
        raise ValueError("estimated order notional must be strictly positive")

    rules = _create_rule_evidence(
        side=valid_intent.side,
        requested_quantity=valid_intent.requested_quantity,
        available_cash=recreated_account.available_cash,
        current_quantity=recreated_account.current_instrument_quantity,
        estimated_notional=estimated_notional,
        policy=policy,
    )
    snapshot = _build_input_snapshot(
        intent_reference=recreated_intent,
        market_reference=recreated_market,
        account_reference=recreated_account,
        risk_policy_reference=policy,
        price_reference=price_reference,
        side=valid_intent.side,
        requested_quantity=valid_intent.requested_quantity,
        verified_available_cash=recreated_account.available_cash,
        verified_current_instrument_quantity=(
            recreated_account.current_instrument_quantity
        ),
        estimated_order_notional=estimated_notional,
        rule_evidence=rules,
    )
    failed = tuple(
        rule.rule_code
        for rule in rules
        if rule.applicable and not rule.passed
    )
    outcome: PreTradeRiskOutcome = (
        PRE_TRADE_RISK_OUTCOME_ALLOW
        if not failed
        else PRE_TRADE_RISK_OUTCOME_REJECT
    )
    audit_time = normalize_utc_datetime(created_at, field_name="created_at")
    return _build_decision(
        input_snapshot=snapshot,
        outcome=outcome,
        reason_codes=failed,
        origin_command_idempotency_key=(
            valid_command.command_idempotency_key
        ),
        origin_command_digest=valid_command.command_digest,
        origin_actor=valid_command.actor,
        created_at=audit_time,
    )


def validate_pre_trade_risk_decision(
    value: object,
) -> PreTradeRiskDecision:
    """Recompute the decision, nested evidence, and origin provenance."""
    if type(value) is not PreTradeRiskDecision:
        raise ValueError("decision must be a PreTradeRiskDecision")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PRE_TRADE_RISK_DECISION_SCHEMA_VERSION
        ):
            raise ValueError("unsupported risk decision schema_version")
        snapshot = validate_pre_trade_risk_input_snapshot(
            value.input_snapshot
        )
        if value.outcome not in SUPPORTED_PRE_TRADE_RISK_OUTCOMES:
            raise ValueError("unsupported pre-trade risk outcome")
        if type(value.reason_codes) is not tuple:
            raise ValueError("reason_codes must be an immutable tuple")
        if any(
            type(reason) is not str or reason not in PRE_TRADE_RISK_RULE_ORDER
            for reason in value.reason_codes
        ):
            raise ValueError("unsupported pre-trade risk reason code")
        expected_reasons = tuple(
            rule.rule_code
            for rule in snapshot.rule_evidence
            if rule.applicable and not rule.passed
        )
        expected_outcome: PreTradeRiskOutcome = (
            PRE_TRADE_RISK_OUTCOME_ALLOW
            if not expected_reasons
            else PRE_TRADE_RISK_OUTCOME_REJECT
        )
        if (
            value.outcome != expected_outcome
            or value.reason_codes != expected_reasons
        ):
            raise ValueError("risk outcome and ordered reasons are invalid")
        key = normalize_bounded_string(
            value.origin_command_idempotency_key,
            field_name="origin_command_idempotency_key",
            maximum_length=MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
        )
        actor = normalize_bounded_string(
            value.origin_actor,
            field_name="origin_actor",
            maximum_length=MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
        )
        if (
            key != value.origin_command_idempotency_key
            or actor != value.origin_actor
        ):
            raise ValueError("origin audit strings must already be normalized")
        command_digest = validate_digest(
            value.origin_command_digest,
            field_name="origin_command_digest",
        )
        expected_command_digest = _evaluate_pre_trade_risk_command_digest(
            schema_version=EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
            intent_reference=snapshot.intent_reference,
            risk_policy_reference=snapshot.risk_policy_reference,
            command_idempotency_key=key,
            actor=actor,
        )
        if command_digest != expected_command_digest:
            raise ValueError("origin command digest does not match provenance")
        audit_time = normalize_utc_datetime(
            value.created_at,
            field_name="created_at",
        )
        if audit_time != value.created_at:
            raise ValueError("created_at must be normalized to UTC")
        validate_digest(value.decision_digest, field_name="decision_digest")
        rebuilt = _build_decision(
            input_snapshot=snapshot,
            outcome=expected_outcome,
            reason_codes=expected_reasons,
            origin_command_idempotency_key=key,
            origin_command_digest=command_digest,
            origin_actor=actor,
            created_at=audit_time,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("pre-trade risk decision is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("pre-trade risk decision is invalid")
    return value
