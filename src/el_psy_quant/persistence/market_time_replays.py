"""Validated durable wrapper for market-data replay recovery state."""

from __future__ import annotations

import json
from dataclasses import dataclass

from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    ReplaySession,
    sort_and_validate_market_data_events,
)

MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class MarketDataReplayRecord:
    """Persistence-only grouping of one exact stream and engine-owned state."""

    session: ReplaySession
    events: tuple[MarketDataEvent, ...]

    def __post_init__(self) -> None:
        if type(self.session) is not ReplaySession:
            raise ValueError("session must be a ReplaySession")
        if type(self.events) is not tuple:
            raise ValueError("events must be a canonical event tuple")
        ordered = sort_and_validate_market_data_events(self.events)
        if ordered != self.events:
            raise ValueError("events must use canonical replay order")
        restored = MarketDataReplayEngine(
            replay_id=self.session.replay_id,
            events=self.events,
            cursor=self.session.cursor,
        )
        if restored.session != self.session:
            raise ValueError("session does not match the exact event stream")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible persisted replay state."""
        return {
            "record_schema_version": (
                MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
            ),
            "session": self.session.to_dict(),
            "events": [event.to_dict() for event in self.events],
        }

    def to_json(self) -> str:
        """Return canonical UTF-8-compatible persisted replay JSON."""
        return json.dumps(
            self.to_dict(),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def create_market_data_replay_record(
    *,
    session: ReplaySession,
    events: tuple[MarketDataEvent, ...] | list[MarketDataEvent],
) -> MarketDataReplayRecord:
    """Bind one engine-owned session to its exact canonical event stream."""
    return MarketDataReplayRecord(
        session=session,
        events=sort_and_validate_market_data_events(events),
    )


__all__ = [
    "MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "MarketDataReplayRecord",
    "create_market_data_replay_record",
]
