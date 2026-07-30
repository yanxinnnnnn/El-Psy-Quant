"""Closed runtime adapters for deterministic Strategy Signal evaluation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real
from typing import ClassVar, Protocol, cast, runtime_checkable

import pandas as pd
from pandas.api.types import is_bool_dtype

from el_psy_quant.market_time import (
    MarketDataEvent,
    TradingSession,
    sort_and_validate_market_data_events,
)
from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.strategies import (
    Strategy,
    resolve_strategy,
    validate_strategy_result,
)
from el_psy_quant.strategy_order.market_references import (
    StrategySignalMarketReference,
    validate_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.runtime import (
    MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
    MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
    MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
    StrategyRuntimeReference,
    validate_strategy_runtime_reference,
)


@runtime_checkable
class StrategySignalRuntimeAdapter(Protocol):
    """Closed pure boundary from exact market input to one target quantity."""

    strategy_name: str
    strategy_version: str
    adapter_version: str

    def evaluate_target(
        self,
        *,
        runtime_reference: StrategyRuntimeReference,
        replay_prefix: tuple[MarketDataEvent, ...],
        market_reference: StrategySignalMarketReference,
        session: TradingSession,
    ) -> PaperQuantity:
        """Evaluate one exact long-only target from a consumed M32 prefix."""
        ...


def _validate_exact_event(value: object) -> MarketDataEvent:
    if type(value) is not MarketDataEvent:
        raise ValueError("replay events must be MarketDataEvent values")
    try:
        rebuilt = MarketDataEvent(
            event_id=value.event_id,
            instrument_id=value.instrument_id,
            event_time=value.event_time,
            event_type=value.event_type,
            payload=value.payload,
            schema_version=value.schema_version,
            source=value.source,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("replay event is invalid") from exc
    if rebuilt != value or rebuilt.to_json() != value.to_json():
        raise ValueError("replay event is invalid")
    return value


def _validate_exact_session(value: object) -> TradingSession:
    if type(value) is not TradingSession:
        raise ValueError("session must be a TradingSession")
    try:
        rebuilt = TradingSession(
            id=value.id,
            calendar_id=value.calendar_id,
            trading_date=value.trading_date,
            open_time=value.open_time,
            close_time=value.close_time,
            session_type=value.session_type,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("session must be a valid TradingSession") from exc
    if rebuilt != value:
        raise ValueError("session must be a valid TradingSession")
    return value


def _validated_prefix(
    replay_prefix: object,
    *,
    market_reference: StrategySignalMarketReference,
    session: TradingSession,
) -> tuple[MarketDataEvent, ...]:
    if type(replay_prefix) is not tuple:
        raise ValueError("replay_prefix must be a tuple of MarketDataEvent values")
    if not replay_prefix:
        raise ValueError("replay_prefix must contain a consumed event")
    try:
        validated = tuple(
            _validate_exact_event(event) for event in replay_prefix
        )
        ordered = sort_and_validate_market_data_events(validated)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("replay_prefix is invalid") from exc
    if ordered != replay_prefix:
        raise ValueError("replay_prefix must preserve exact M32 event order")

    current = replay_prefix[-1]
    if current.event_id != market_reference.signal_event_id:
        raise ValueError("replay_prefix current event does not match market reference")
    if current.event_time != market_reference.signal_time:
        raise ValueError("replay_prefix current time does not match market reference")
    if current.instrument_id != market_reference.instrument_id:
        raise ValueError("replay_prefix current instrument does not match market reference")
    if market_reference.cursor_position != len(replay_prefix):
        raise ValueError("replay_prefix length does not match market reference cursor")
    _validate_exact_session(session)
    if session.id != market_reference.trading_session_id:
        raise ValueError("session does not match market reference")
    if session.calendar_id != market_reference.calendar_id:
        raise ValueError("session calendar does not match market reference")
    if not session.open_time <= current.event_time <= session.close_time:
        raise ValueError("current event must fall within the trading session")
    return replay_prefix


def _trade_prices(
    events: Sequence[MarketDataEvent],
    *,
    instrument_id: str,
) -> pd.DataFrame:
    event_ids: list[str] = []
    prices: list[float] = []
    for event in events:
        if event.instrument_id != instrument_id or event.event_type != "trade":
            continue
        payload = event.payload
        if "price" not in payload:
            raise ValueError("selected trade event must contain top-level price")
        value = payload["price"]
        if type(value) not in (int, float):
            raise ValueError("selected trade price must be a JSON integer or float")
        try:
            price = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError("selected trade price cannot enter research input") from exc
        if not math.isfinite(price) or price <= 0:
            raise ValueError("selected trade price must be finite and positive")
        event_ids.append(event.event_id)
        prices.append(price)
    return pd.DataFrame(
        {"Close": prices},
        index=pd.Index(event_ids, name="market_event_id"),
    )


def _latest_long_only_position(
    strategy: Strategy,
    prices: pd.DataFrame,
    *,
    fast_window: int,
    slow_window: int,
) -> int:
    try:
        result = strategy.run(
            prices,
            {
                "fast_window": fast_window,
                "slow_window": slow_window,
            },
        )
        validate_strategy_result(result)
    except Exception as exc:
        raise ValueError("research strategy evaluation failed") from exc
    if type(result) is not pd.DataFrame:
        raise ValueError("strategy result must be an exact pandas DataFrame")
    if len(result) != len(prices) or not result.index.equals(prices.index):
        raise ValueError("strategy result must align exactly with strategy input")
    if "position" not in result.columns:
        raise ValueError("strategy result must contain position")

    position = result["position"]
    if position.isna().any() or is_bool_dtype(position.dtype):
        raise ValueError("strategy position must contain closed long-only states")
    for value in position.tolist():
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("strategy position must contain numeric 0 or 1 states")
        if value not in (0, 1):
            raise ValueError("strategy position must contain only 0 or 1")
    return int(position.iloc[-1])


@dataclass(frozen=True)
class MovingAverageCrossoverSignalAdapter:
    """The only closed S199 runtime adapter: moving-average crossover v1."""

    strategy_name: ClassVar[str] = MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME
    strategy_version: ClassVar[str] = MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION
    adapter_version: ClassVar[str] = MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION

    def evaluate_target(
        self,
        *,
        runtime_reference: StrategyRuntimeReference,
        replay_prefix: tuple[MarketDataEvent, ...],
        market_reference: StrategySignalMarketReference,
        session: TradingSession,
    ) -> PaperQuantity:
        """Map the validated research strategy's latest position to a target."""
        validate_strategy_runtime_reference(runtime_reference)
        validate_strategy_signal_market_reference(market_reference)
        identity = (
            runtime_reference.strategy_name,
            runtime_reference.strategy_version,
            runtime_reference.adapter_version,
        )
        if identity != (
            self.strategy_name,
            self.strategy_version,
            self.adapter_version,
        ):
            raise ValueError("runtime reference does not match adapter identity")
        prefix = _validated_prefix(
            replay_prefix,
            market_reference=market_reference,
            session=session,
        )
        parameters = runtime_reference.parameters
        fast_window = cast(int, parameters["fast_window"])
        slow_window = cast(int, parameters["slow_window"])
        prices = _trade_prices(
            prefix,
            instrument_id=market_reference.instrument_id,
        )
        if len(prices) < slow_window + 1:
            raise ValueError(
                "insufficient trade-price history: slow_window + 1 required"
            )

        try:
            strategy = resolve_strategy(self.strategy_name)
        except Exception as exc:
            raise ValueError("research strategy resolution failed") from exc
        if not isinstance(strategy, Strategy):
            raise ValueError("resolved research strategy is invalid")
        if strategy.name != self.strategy_name:
            raise ValueError("resolved research strategy identity is invalid")
        latest_position = _latest_long_only_position(
            strategy,
            prices,
            fast_window=fast_window,
            slow_window=slow_window,
        )
        if latest_position == 0:
            return PaperQuantity.parse("0")
        configured = cast(str, parameters["target_position_quantity"])
        return PaperQuantity.parse(configured)


def resolve_strategy_signal_runtime_adapter(
    runtime_reference: StrategyRuntimeReference,
) -> StrategySignalRuntimeAdapter:
    """Resolve the single supported adapter by its exact closed identity tuple."""
    validate_strategy_runtime_reference(runtime_reference)
    identity = (
        runtime_reference.strategy_name,
        runtime_reference.strategy_version,
        runtime_reference.adapter_version,
    )
    supported = (
        MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
        MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
        MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
    )
    if identity != supported:
        raise ValueError("unsupported strategy signal runtime adapter")
    return MovingAverageCrossoverSignalAdapter()
