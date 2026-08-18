"""Immutable M31/M32/M33 handoff evidence for Paper execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    TradingCalendar,
    TradingSession,
    normalize_market_instrument_id,
    validate_trading_session_for_calendar,
)
from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountLedgerState,
    PaperMoney,
    PaperQuantity,
    validate_paper_account_ledger_state,
)
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order import (
    OrderIntent,
    OrderIntentReference,
    PreTradeRiskDecision,
    PreTradeRiskPolicyReference,
    create_long_only_cash_risk_policy_reference,
    create_order_intent_reference,
    validate_order_intent,
    validate_order_intent_reference,
    validate_pre_trade_risk_decision,
    validate_pre_trade_risk_policy_reference,
)

PAPER_EXECUTION_ACCOUNT_HANDOFF_REFERENCE_SCHEMA_VERSION = 1
PAPER_EXECUTION_MARKET_HANDOFF_REFERENCE_SCHEMA_VERSION = 1
PAPER_EXECUTION_RISK_HANDOFF_REFERENCE_SCHEMA_VERSION = 1


def _clone_intent_reference(value: OrderIntentReference) -> OrderIntentReference:
    validate_order_intent_reference(value)
    result = object.__new__(OrderIntentReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "intent_id", value.intent_id)
    object.__setattr__(result, "intent_digest", value.intent_digest)
    return result


def _clone_risk_policy(
    value: PreTradeRiskPolicyReference,
) -> PreTradeRiskPolicyReference:
    validate_pre_trade_risk_policy_reference(value)
    return create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=value.maximum_order_quantity,
        maximum_order_notional=value.maximum_order_notional,
        schema_version=value.schema_version,
    )


def _exact_money(value: object, *, field_name: str) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is invalid")
    return rebuilt


def _exact_quantity(value: object, *, field_name: str) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is invalid")
    return rebuilt


def _account_payload(
    *,
    schema_version: int,
    account_id: str,
    base_currency: str,
    lifecycle_status: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    cash_balance: PaperMoney,
    available_cash: PaperMoney,
    instrument_id: str,
    current_instrument_quantity: PaperQuantity,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "account_id": account_id,
        "base_currency": base_currency,
        "lifecycle_status": lifecycle_status,
        "account_head_version": account_head_version,
        "account_head_event_id": account_head_event_id,
        "account_head_chain_digest": account_head_chain_digest,
        "cash_balance": cash_balance.to_json_value(),
        "available_cash": available_cash.to_json_value(),
        "instrument_id": instrument_id,
        "current_instrument_quantity": (current_instrument_quantity.to_json_value()),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionAccountHandoffReference:
    """Copied evidence from the exact active M31 ledger-state handoff."""

    schema_version: int
    account_id: str
    base_currency: str
    lifecycle_status: str
    account_head_version: int
    account_head_event_id: str
    account_head_chain_digest: str
    cash_balance: PaperMoney
    available_cash: PaperMoney
    instrument_id: str
    current_instrument_quantity: PaperQuantity
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_account_payload(
                schema_version=self.schema_version,
                account_id=self.account_id,
                base_currency=self.base_currency,
                lifecycle_status=self.lifecycle_status,
                account_head_version=self.account_head_version,
                account_head_event_id=self.account_head_event_id,
                account_head_chain_digest=self.account_head_chain_digest,
                cash_balance=self.cash_balance,
                available_cash=self.available_cash,
                instrument_id=self.instrument_id,
                current_instrument_quantity=(self.current_instrument_quantity),
            ),
            "reference_digest": self.reference_digest,
        }


def _build_account_handoff(
    *,
    account_id: str,
    base_currency: str,
    lifecycle_status: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    cash_balance: PaperMoney,
    available_cash: PaperMoney,
    instrument_id: str,
    current_instrument_quantity: PaperQuantity,
) -> PaperExecutionAccountHandoffReference:
    cash = PaperMoney.parse(cash_balance.canonical)
    available = PaperMoney.parse(available_cash.canonical)
    current = PaperQuantity.parse(current_instrument_quantity.canonical)
    payload = _account_payload(
        schema_version=(PAPER_EXECUTION_ACCOUNT_HANDOFF_REFERENCE_SCHEMA_VERSION),
        account_id=account_id,
        base_currency=base_currency,
        lifecycle_status=lifecycle_status,
        account_head_version=account_head_version,
        account_head_event_id=account_head_event_id,
        account_head_chain_digest=account_head_chain_digest,
        cash_balance=cash,
        available_cash=available,
        instrument_id=instrument_id,
        current_instrument_quantity=current,
    )
    result = object.__new__(PaperExecutionAccountHandoffReference)
    for field_name, value in (
        (
            "schema_version",
            PAPER_EXECUTION_ACCOUNT_HANDOFF_REFERENCE_SCHEMA_VERSION,
        ),
        ("account_id", account_id),
        ("base_currency", base_currency),
        ("lifecycle_status", lifecycle_status),
        ("account_head_version", account_head_version),
        ("account_head_event_id", account_head_event_id),
        ("account_head_chain_digest", account_head_chain_digest),
        ("cash_balance", cash),
        ("available_cash", available),
        ("instrument_id", instrument_id),
        ("current_instrument_quantity", current),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_account_handoff_reference(
    *,
    intent: OrderIntent,
    account_state: PaperAccountLedgerState,
) -> PaperExecutionAccountHandoffReference:
    """Revalidate and copy one exact fresh M31 execution handoff."""
    valid_intent = validate_order_intent(intent)
    valid_state = validate_paper_account_ledger_state(account_state)
    if valid_state.lifecycle_status != "active":
        raise ValueError("paper execution account handoff must be active")
    account = valid_intent.account_reference
    positions = {
        position.symbol: position.quantity for position in valid_state.positions
    }
    current = positions.get(account.instrument_id, PaperQuantity.parse("0"))
    exact = {
        "account_id": valid_state.account_identity.account_id,
        "base_currency": valid_state.account_identity.base_currency,
        "lifecycle_status": valid_state.lifecycle_status,
        "account_head_version": valid_state.head_version,
        "account_head_event_id": valid_state.head_event_id,
        "account_head_chain_digest": valid_state.head_chain_digest,
        "cash_balance": valid_state.cash_balance.to_json_value(),
        "available_cash": valid_state.available_cash.to_json_value(),
        "instrument_id": account.instrument_id,
        "current_instrument_quantity": current.to_json_value(),
    }
    expected = {
        key: value
        for key, value in account.to_dict().items()
        if key not in {"schema_version", "reference_digest"}
    }
    if exact != expected:
        raise ValueError("paper execution account authority is stale or mismatched")
    return _build_account_handoff(
        account_id=exact["account_id"],
        base_currency=exact["base_currency"],
        lifecycle_status=exact["lifecycle_status"],
        account_head_version=exact["account_head_version"],
        account_head_event_id=exact["account_head_event_id"],
        account_head_chain_digest=exact["account_head_chain_digest"],
        cash_balance=valid_state.cash_balance,
        available_cash=valid_state.available_cash,
        instrument_id=exact["instrument_id"],
        current_instrument_quantity=current,
    )


def validate_paper_execution_account_handoff_reference(
    value: object,
) -> PaperExecutionAccountHandoffReference:
    if type(value) is not PaperExecutionAccountHandoffReference:
        raise ValueError("account_handoff_reference is invalid")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PAPER_EXECUTION_ACCOUNT_HANDOFF_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported account handoff schema_version")
        if value.lifecycle_status != "active":
            raise ValueError("account handoff lifecycle must be active")
        if (
            type(value.account_head_version) is not int
            or value.account_head_version < 1
        ):
            raise ValueError("account handoff version must be positive")
        account_id = normalize_bounded_string(
            value.account_id,
            field_name="account_id",
            maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
        )
        if account_id != value.account_id:
            raise ValueError("account handoff account_id is not normalized")
        if (
            not isinstance(value.base_currency, str)
            or len(value.base_currency) != 3
            or any(
                character < "A" or character > "Z" for character in value.base_currency
            )
        ):
            raise ValueError("account handoff base_currency is invalid")
        event_id = normalize_bounded_string(
            value.account_head_event_id,
            field_name="account_head_event_id",
            maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
        )
        if event_id != value.account_head_event_id:
            raise ValueError("account handoff event ID is not normalized")
        validate_digest(
            value.account_head_chain_digest,
            field_name="account_head_chain_digest",
        )
        cash = _exact_money(value.cash_balance, field_name="cash_balance")
        available = _exact_money(value.available_cash, field_name="available_cash")
        current = _exact_quantity(
            value.current_instrument_quantity,
            field_name="current_instrument_quantity",
        )
        if cash.decimal_value < 0 or available.decimal_value < 0:
            raise ValueError("account handoff cash must be non-negative")
        if cash != available:
            raise ValueError("available_cash must equal cash_balance in v1")
        if current.decimal_value < 0:
            raise ValueError("current quantity must be non-negative")
        instrument = normalize_market_instrument_id(value.instrument_id)
        if instrument != value.instrument_id:
            raise ValueError("account handoff instrument is invalid")
        validate_digest(value.reference_digest, field_name="reference_digest")
        rebuilt = _build_account_handoff(
            account_id=value.account_id,
            base_currency=value.base_currency,
            lifecycle_status=value.lifecycle_status,
            account_head_version=value.account_head_version,
            account_head_event_id=value.account_head_event_id,
            account_head_chain_digest=value.account_head_chain_digest,
            cash_balance=cash,
            available_cash=available,
            instrument_id=value.instrument_id,
            current_instrument_quantity=current,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution account handoff is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("paper execution account handoff is invalid")
    return value


def _market_payload(
    *,
    schema_version: int,
    calendar_id: str,
    calendar_version: int,
    trading_session_id: str,
    trading_date: date,
    session_open_time: datetime,
    session_close_time: datetime,
    session_type: str,
    replay_id: str,
    event_stream_digest: str,
    cursor_position: int,
    last_event_id: str,
    current_event_time: datetime,
    current_event_id: str,
    instrument_id: str,
    handoff_replay_status: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "calendar_id": calendar_id,
        "calendar_version": calendar_version,
        "trading_session_id": trading_session_id,
        "trading_date": trading_date.isoformat(),
        "session_open_time": session_open_time.isoformat(),
        "session_close_time": session_close_time.isoformat(),
        "session_type": session_type,
        "replay_id": replay_id,
        "event_stream_digest": event_stream_digest,
        "cursor_position": cursor_position,
        "last_event_id": last_event_id,
        "current_event_time": current_event_time.isoformat(),
        "current_event_id": current_event_id,
        "instrument_id": instrument_id,
        "handoff_replay_status": handoff_replay_status,
    }


@dataclass(frozen=True, init=False)
class PaperExecutionMarketHandoffReference:
    """Copied exact calendar/session/replay/current-event handoff evidence."""

    schema_version: int
    calendar_id: str
    calendar_version: int
    trading_session_id: str
    trading_date: date
    session_open_time: datetime
    session_close_time: datetime
    session_type: str
    replay_id: str
    event_stream_digest: str
    cursor_position: int
    last_event_id: str
    current_event_time: datetime
    current_event_id: str
    instrument_id: str
    handoff_replay_status: str
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_market_payload(
                schema_version=self.schema_version,
                calendar_id=self.calendar_id,
                calendar_version=self.calendar_version,
                trading_session_id=self.trading_session_id,
                trading_date=self.trading_date,
                session_open_time=self.session_open_time,
                session_close_time=self.session_close_time,
                session_type=self.session_type,
                replay_id=self.replay_id,
                event_stream_digest=self.event_stream_digest,
                cursor_position=self.cursor_position,
                last_event_id=self.last_event_id,
                current_event_time=self.current_event_time,
                current_event_id=self.current_event_id,
                instrument_id=self.instrument_id,
                handoff_replay_status=self.handoff_replay_status,
            ),
            "reference_digest": self.reference_digest,
        }


def _build_market_handoff(
    *,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
) -> PaperExecutionMarketHandoffReference:
    cursor = replay_engine.cursor
    current_event = replay_engine.events[cursor.position - 1]
    payload = _market_payload(
        schema_version=PAPER_EXECUTION_MARKET_HANDOFF_REFERENCE_SCHEMA_VERSION,
        calendar_id=calendar.id,
        calendar_version=calendar.calendar_version,
        trading_session_id=session.id,
        trading_date=session.trading_date,
        session_open_time=session.open_time,
        session_close_time=session.close_time,
        session_type=session.session_type,
        replay_id=cursor.replay_id,
        event_stream_digest=cursor.event_stream_digest,
        cursor_position=cursor.position,
        last_event_id=current_event.event_id,
        current_event_time=current_event.event_time,
        current_event_id=current_event.event_id,
        instrument_id=current_event.instrument_id,
        handoff_replay_status="running",
    )
    result = object.__new__(PaperExecutionMarketHandoffReference)
    values = {
        "schema_version": (PAPER_EXECUTION_MARKET_HANDOFF_REFERENCE_SCHEMA_VERSION),
        "calendar_id": calendar.id,
        "calendar_version": calendar.calendar_version,
        "trading_session_id": session.id,
        "trading_date": session.trading_date,
        "session_open_time": session.open_time,
        "session_close_time": session.close_time,
        "session_type": session.session_type,
        "replay_id": cursor.replay_id,
        "event_stream_digest": cursor.event_stream_digest,
        "cursor_position": cursor.position,
        "last_event_id": current_event.event_id,
        "current_event_time": current_event.event_time,
        "current_event_id": current_event.event_id,
        "instrument_id": current_event.instrument_id,
        "handoff_replay_status": "running",
        "reference_digest": canonical_digest(payload),
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def _validate_exact_market_authority(
    *,
    calendar: object,
    session: object,
    replay_engine: object,
) -> tuple[TradingCalendar, TradingSession, MarketDataReplayEngine]:
    try:
        if type(calendar) is not TradingCalendar:
            raise ValueError("calendar must be TradingCalendar")
        rebuilt_calendar = TradingCalendar(
            id=calendar.id,
            market=calendar.market,
            timezone=calendar.timezone,
            calendar_version=calendar.calendar_version,
            created_at=calendar.created_at,
        )
        if rebuilt_calendar != calendar:
            raise ValueError("calendar is not canonical")
        if type(session) is not TradingSession:
            raise ValueError("session must be TradingSession")
        rebuilt_session = TradingSession(
            id=session.id,
            calendar_id=session.calendar_id,
            trading_date=session.trading_date,
            open_time=session.open_time,
            close_time=session.close_time,
            session_type=session.session_type,
        )
        if rebuilt_session != session:
            raise ValueError("session is not canonical")
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=session,
        )
        if type(replay_engine) is not MarketDataReplayEngine:
            raise ValueError("replay_engine must be MarketDataReplayEngine")
        events = replay_engine.events
        cursor = replay_engine.cursor
        if type(events) is not tuple:
            raise ValueError("replay events must be an immutable tuple")
        rebuilt_engine = MarketDataReplayEngine(
            replay_id=cursor.replay_id,
            events=events,
            cursor=cursor,
        )
        if (
            rebuilt_engine.events != events
            or rebuilt_engine.cursor != cursor
            or rebuilt_engine.session != replay_engine.session
        ):
            raise ValueError("replay engine is not canonical")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution market authority is invalid") from exc
    return calendar, session, replay_engine


def _validate_matching_allow(
    *,
    intent: OrderIntent,
    decision: PreTradeRiskDecision,
) -> tuple[OrderIntent, PreTradeRiskDecision]:
    valid_intent = validate_order_intent(intent)
    valid_decision = validate_pre_trade_risk_decision(decision)
    intent_reference = create_order_intent_reference(valid_intent)
    snapshot = valid_decision.input_snapshot
    if snapshot.intent_reference != intent_reference:
        raise ValueError("risk decision does not reference the exact intent")
    if valid_decision.outcome != "allow" or valid_decision.reason_codes:
        raise ValueError("paper execution requires an exact allow decision")
    if (
        snapshot.market_reference != valid_intent.market_reference
        or snapshot.account_reference != valid_intent.account_reference
        or snapshot.side != valid_intent.side
        or snapshot.requested_quantity != valid_intent.requested_quantity
    ):
        raise ValueError("risk decision evidence does not match the intent")
    return valid_intent, valid_decision


def create_paper_execution_market_handoff_reference(
    *,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
    intent: OrderIntent,
    decision: PreTradeRiskDecision,
) -> PaperExecutionMarketHandoffReference:
    """Copy one exact running M32 handoff without advancing replay."""
    valid_intent, _ = _validate_matching_allow(
        intent=intent,
        decision=decision,
    )
    valid_calendar, valid_session, valid_engine = _validate_exact_market_authority(
        calendar=calendar,
        session=session,
        replay_engine=replay_engine,
    )
    cursor = valid_engine.cursor
    if cursor.status != "running" or valid_engine.session.status != "running":
        raise ValueError("paper execution replay handoff must be running")
    if cursor.position <= 0:
        raise ValueError("paper execution replay must have a current event")
    current = valid_engine.events[cursor.position - 1]
    market = valid_intent.market_reference
    if not (
        valid_calendar.id == market.calendar_id
        and valid_calendar.calendar_version == market.calendar_version
        and valid_session.id == market.trading_session_id
        and cursor.replay_id == market.replay_id
        and cursor.event_stream_digest == market.event_stream_digest
        and cursor.position == market.cursor_position
        and cursor.last_event_id == market.last_event_id
        and cursor.current_event_time == market.signal_time
        and current.event_id == market.signal_event_id
        and current.event_time == market.signal_time
        and current.instrument_id == market.instrument_id
    ):
        raise ValueError("paper execution market authority is stale or mismatched")
    if not (valid_session.open_time <= current.event_time <= valid_session.close_time):
        raise ValueError("current handoff event is outside the session")
    return _build_market_handoff(
        calendar=valid_calendar,
        session=valid_session,
        replay_engine=valid_engine,
    )


def validate_paper_execution_market_handoff_reference(
    value: object,
) -> PaperExecutionMarketHandoffReference:
    if type(value) is not PaperExecutionMarketHandoffReference:
        raise ValueError("market_handoff_reference is invalid")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PAPER_EXECUTION_MARKET_HANDOFF_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported market handoff schema_version")
        if value.handoff_replay_status != "running":
            raise ValueError("market handoff status must be running")
        if type(value.calendar_version) is not int or value.calendar_version < 1:
            raise ValueError("calendar version must be positive")
        if type(value.cursor_position) is not int or value.cursor_position < 1:
            raise ValueError("cursor position must be positive")
        if value.last_event_id != value.current_event_id:
            raise ValueError("current event must equal last consumed event")
        canonical_session = TradingSession(
            id=value.trading_session_id,
            calendar_id=value.calendar_id,
            trading_date=value.trading_date,
            open_time=value.session_open_time,
            close_time=value.session_close_time,
            session_type=value.session_type,
        )
        if not (
            canonical_session.id == value.trading_session_id
            and canonical_session.calendar_id == value.calendar_id
            and canonical_session.trading_date == value.trading_date
            and canonical_session.open_time == value.session_open_time
            and canonical_session.close_time == value.session_close_time
            and canonical_session.session_type == value.session_type
        ):
            raise ValueError("market handoff session values are not canonical")
        for field_name in (
            "calendar_id",
            "trading_session_id",
            "replay_id",
            "last_event_id",
            "current_event_id",
        ):
            item = normalize_bounded_string(
                getattr(value, field_name),
                field_name=field_name,
                maximum_length=512,
            )
            if item != getattr(value, field_name):
                raise ValueError(f"{field_name} is invalid")
        instrument = normalize_market_instrument_id(value.instrument_id)
        if instrument != value.instrument_id:
            raise ValueError("instrument_id is invalid")
        validate_digest(
            value.event_stream_digest,
            field_name="event_stream_digest",
        )
        current_time = normalize_utc_datetime(
            value.current_event_time,
            field_name="current_event_time",
        )
        if current_time != value.current_event_time or not (
            value.session_open_time <= current_time <= value.session_close_time
        ):
            raise ValueError("market handoff times are invalid")
        validate_digest(value.reference_digest, field_name="reference_digest")
        payload = _market_payload(
            schema_version=value.schema_version,
            calendar_id=value.calendar_id,
            calendar_version=value.calendar_version,
            trading_session_id=value.trading_session_id,
            trading_date=value.trading_date,
            session_open_time=value.session_open_time,
            session_close_time=value.session_close_time,
            session_type=value.session_type,
            replay_id=value.replay_id,
            event_stream_digest=value.event_stream_digest,
            cursor_position=value.cursor_position,
            last_event_id=value.last_event_id,
            current_event_time=value.current_event_time,
            current_event_id=value.current_event_id,
            instrument_id=value.instrument_id,
            handoff_replay_status=value.handoff_replay_status,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution market handoff is invalid") from exc
    if canonical_digest(payload) != value.reference_digest:
        raise ValueError("paper execution market handoff is invalid")
    return value


def _risk_payload(
    *,
    schema_version: int,
    order_intent_reference: OrderIntentReference,
    risk_decision_id: str,
    risk_decision_digest: str,
    risk_snapshot_id: str,
    risk_snapshot_digest: str,
    outcome: str,
    risk_policy_reference: PreTradeRiskPolicyReference,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "order_intent_reference": order_intent_reference.to_dict(),
        "risk_decision_id": risk_decision_id,
        "risk_decision_digest": risk_decision_digest,
        "risk_snapshot_id": risk_snapshot_id,
        "risk_snapshot_digest": risk_snapshot_digest,
        "outcome": outcome,
        "risk_policy_reference": risk_policy_reference.to_dict(),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionRiskHandoffReference:
    """Compact immutable evidence for one exact matching M33 allow result."""

    schema_version: int
    order_intent_reference: OrderIntentReference
    risk_decision_id: str
    risk_decision_digest: str
    risk_snapshot_id: str
    risk_snapshot_digest: str
    outcome: str
    risk_policy_reference: PreTradeRiskPolicyReference
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_risk_payload(
                schema_version=self.schema_version,
                order_intent_reference=self.order_intent_reference,
                risk_decision_id=self.risk_decision_id,
                risk_decision_digest=self.risk_decision_digest,
                risk_snapshot_id=self.risk_snapshot_id,
                risk_snapshot_digest=self.risk_snapshot_digest,
                outcome=self.outcome,
                risk_policy_reference=self.risk_policy_reference,
            ),
            "reference_digest": self.reference_digest,
        }


def _build_risk_handoff(
    *,
    order_intent_reference: OrderIntentReference,
    risk_decision_id: str,
    risk_decision_digest: str,
    risk_snapshot_id: str,
    risk_snapshot_digest: str,
    risk_policy_reference: PreTradeRiskPolicyReference,
) -> PaperExecutionRiskHandoffReference:
    intent_reference = _clone_intent_reference(order_intent_reference)
    policy = _clone_risk_policy(risk_policy_reference)
    payload = _risk_payload(
        schema_version=PAPER_EXECUTION_RISK_HANDOFF_REFERENCE_SCHEMA_VERSION,
        order_intent_reference=intent_reference,
        risk_decision_id=risk_decision_id,
        risk_decision_digest=risk_decision_digest,
        risk_snapshot_id=risk_snapshot_id,
        risk_snapshot_digest=risk_snapshot_digest,
        outcome="allow",
        risk_policy_reference=policy,
    )
    result = object.__new__(PaperExecutionRiskHandoffReference)
    for field_name, value in (
        (
            "schema_version",
            PAPER_EXECUTION_RISK_HANDOFF_REFERENCE_SCHEMA_VERSION,
        ),
        ("order_intent_reference", intent_reference),
        ("risk_decision_id", risk_decision_id),
        ("risk_decision_digest", risk_decision_digest),
        ("risk_snapshot_id", risk_snapshot_id),
        ("risk_snapshot_digest", risk_snapshot_digest),
        ("outcome", "allow"),
        ("risk_policy_reference", policy),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_risk_handoff_reference(
    *,
    decision: PreTradeRiskDecision,
    intent: OrderIntent,
) -> PaperExecutionRiskHandoffReference:
    """Copy exact matching allow evidence without reevaluating M33 risk."""
    valid_intent, valid_decision = _validate_matching_allow(
        intent=intent,
        decision=decision,
    )
    snapshot = valid_decision.input_snapshot
    return _build_risk_handoff(
        order_intent_reference=create_order_intent_reference(valid_intent),
        risk_decision_id=valid_decision.decision_id,
        risk_decision_digest=valid_decision.decision_digest,
        risk_snapshot_id=snapshot.snapshot_id,
        risk_snapshot_digest=snapshot.snapshot_digest,
        risk_policy_reference=snapshot.risk_policy_reference,
    )


def validate_paper_execution_risk_handoff_reference(
    value: object,
) -> PaperExecutionRiskHandoffReference:
    if type(value) is not PaperExecutionRiskHandoffReference:
        raise ValueError("risk_handoff_reference is invalid")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PAPER_EXECUTION_RISK_HANDOFF_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported risk handoff schema_version")
        validate_order_intent_reference(value.order_intent_reference)
        validate_pre_trade_risk_policy_reference(value.risk_policy_reference)
        if value.outcome != "allow":
            raise ValueError("risk handoff outcome must be allow")
        decision_digest = validate_digest(
            value.risk_decision_digest,
            field_name="risk_decision_digest",
        )
        snapshot_digest = validate_digest(
            value.risk_snapshot_digest,
            field_name="risk_snapshot_digest",
        )
        if value.risk_decision_id != f"risk_decision_{decision_digest}":
            raise ValueError("risk decision ID does not match digest")
        if value.risk_snapshot_id != f"risk_input_{snapshot_digest}":
            raise ValueError("risk snapshot ID does not match digest")
        validate_digest(value.reference_digest, field_name="reference_digest")
        rebuilt = _build_risk_handoff(
            order_intent_reference=value.order_intent_reference,
            risk_decision_id=value.risk_decision_id,
            risk_decision_digest=value.risk_decision_digest,
            risk_snapshot_id=value.risk_snapshot_id,
            risk_snapshot_digest=value.risk_snapshot_digest,
            risk_policy_reference=value.risk_policy_reference,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution risk handoff is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("paper execution risk handoff is invalid")
    return value


def _clone_account_handoff(
    value: PaperExecutionAccountHandoffReference,
) -> PaperExecutionAccountHandoffReference:
    validate_paper_execution_account_handoff_reference(value)
    return _build_account_handoff(
        account_id=value.account_id,
        base_currency=value.base_currency,
        lifecycle_status=value.lifecycle_status,
        account_head_version=value.account_head_version,
        account_head_event_id=value.account_head_event_id,
        account_head_chain_digest=value.account_head_chain_digest,
        cash_balance=value.cash_balance,
        available_cash=value.available_cash,
        instrument_id=value.instrument_id,
        current_instrument_quantity=value.current_instrument_quantity,
    )


def _clone_risk_handoff(
    value: PaperExecutionRiskHandoffReference,
) -> PaperExecutionRiskHandoffReference:
    validate_paper_execution_risk_handoff_reference(value)
    return _build_risk_handoff(
        order_intent_reference=value.order_intent_reference,
        risk_decision_id=value.risk_decision_id,
        risk_decision_digest=value.risk_decision_digest,
        risk_snapshot_id=value.risk_snapshot_id,
        risk_snapshot_digest=value.risk_snapshot_digest,
        risk_policy_reference=value.risk_policy_reference,
    )


def _clone_market_handoff(
    value: PaperExecutionMarketHandoffReference,
) -> PaperExecutionMarketHandoffReference:
    validate_paper_execution_market_handoff_reference(value)
    payload = value.to_dict()
    result = object.__new__(PaperExecutionMarketHandoffReference)
    for field_name in (
        "schema_version",
        "calendar_id",
        "calendar_version",
        "trading_session_id",
        "trading_date",
        "session_open_time",
        "session_close_time",
        "session_type",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "last_event_id",
        "current_event_time",
        "current_event_id",
        "instrument_id",
        "handoff_replay_status",
        "reference_digest",
    ):
        object.__setattr__(result, field_name, getattr(value, field_name))
    if result.to_dict() != payload:
        raise ValueError("paper execution market handoff is invalid")
    return result
