"""Domain coverage for deterministic market-data replay progression."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from el_psy_quant.market_time import (
    MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION,
    MarketDataEvent,
    MarketDataReplayEngine,
    ReplayCursor,
    ReplaySession,
    create_market_data_event,
)


def _event(
    event_id: str,
    *,
    minute: int,
    payload_sequence: int | None = None,
) -> MarketDataEvent:
    return create_market_data_event(
        event_id=event_id,
        instrument_id="XNYS:AAPL",
        event_time=datetime(
            2026,
            7,
            28,
            9,
            minute,
            tzinfo=timezone.utc,
        ),
        event_type="quote",
        payload={
            "sequence": (
                minute if payload_sequence is None else payload_sequence
            )
        },
        source="fixture:replay",
    )


def _events() -> list[MarketDataEvent]:
    return [
        _event("event-003", minute=31),
        _event("event-002", minute=30),
        _event("event-001", minute=30),
    ]


def test_replay_consumes_canonical_order_and_advances_lifecycle() -> None:
    engine = MarketDataReplayEngine(
        replay_id="replay-192",
        events=_events(),
    )

    assert [event.event_id for event in engine.events] == [
        "event-001",
        "event-002",
        "event-003",
    ]
    assert engine.session.status == "ready"
    assert engine.session.start_time == datetime(
        2026,
        7,
        28,
        9,
        30,
        tzinfo=timezone.utc,
    )
    assert engine.session.current_time is None

    assert engine.start().status == "running"
    consumed = [event.event_id for event in engine.iter_remaining()]

    assert consumed == ["event-001", "event-002", "event-003"]
    assert engine.cursor.position == 3
    assert engine.cursor.last_event_id == "event-003"
    assert engine.cursor.current_event_time == datetime(
        2026,
        7,
        28,
        9,
        31,
        tzinfo=timezone.utc,
    )
    assert engine.session.status == "completed"
    with pytest.raises(ValueError, match="running replay"):
        engine.next_event()


def test_identical_input_produces_identical_progression() -> None:
    first = MarketDataReplayEngine(
        replay_id="replay-identical",
        events=_events(),
    )
    second = MarketDataReplayEngine(
        replay_id="replay-identical",
        events=list(reversed(_events())),
    )
    first.start()
    second.start()

    first_progression: list[dict[str, object]] = []
    second_progression: list[dict[str, object]] = []
    while first.session.status == "running":
        assert first.next_event() == second.next_event()
        first_progression.append(first.session.to_dict())
        second_progression.append(second.session.to_dict())

    assert first_progression == second_progression
    assert first.cursor.event_stream_digest == (
        second.cursor.event_stream_digest
    )


def test_pause_and_resume_do_not_advance_cursor() -> None:
    engine = MarketDataReplayEngine(
        replay_id="replay-pause",
        events=_events(),
    )
    engine.start()
    first = engine.next_event()
    checkpoint = engine.cursor

    paused = engine.pause()
    assert paused.status == "paused"
    assert paused.cursor.position == 1
    assert paused.cursor.last_event_id == first.event_id
    with pytest.raises(ValueError, match="running replay"):
        engine.next_event()

    resumed = engine.resume()
    assert resumed.status == "running"
    assert resumed.cursor.position == checkpoint.position
    assert resumed.cursor.last_event_id == checkpoint.last_event_id
    assert engine.next_event().event_id == "event-002"


def test_cursor_restore_resumes_without_duplicate_or_skip() -> None:
    original = MarketDataReplayEngine(
        replay_id="replay-restart",
        events=_events(),
    )
    original.start()
    assert original.next_event().event_id == "event-001"
    checkpoint = original.pause().cursor

    restarted = MarketDataReplayEngine(
        replay_id="replay-restart",
        events=list(reversed(_events())),
        cursor=checkpoint,
    )
    assert restarted.session.status == "paused"
    restarted.resume()

    assert [event.event_id for event in restarted.iter_remaining()] == [
        "event-002",
        "event-003",
    ]
    assert restarted.session.status == "completed"


def test_cursor_is_bound_to_exact_event_input() -> None:
    original = MarketDataReplayEngine(
        replay_id="replay-bound",
        events=_events(),
    )
    original.start()
    original.next_event()
    checkpoint = original.pause().cursor
    changed = [
        _event("event-003", minute=31),
        _event("event-002", minute=30, payload_sequence=999),
        _event("event-001", minute=30),
    ]

    with pytest.raises(ValueError, match="event stream"):
        MarketDataReplayEngine(
            replay_id="replay-bound",
            events=changed,
            cursor=checkpoint,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"replay_id": "another-replay"}, "replay_id"),
        ({"position": 99}, "position exceeds"),
        ({"last_event_id": "event-002"}, "last_event_id"),
        (
            {
                "current_event_time": datetime(
                    2026,
                    7,
                    28,
                    9,
                    31,
                    tzinfo=timezone.utc,
                )
            },
            "current_event_time",
        ),
        ({"status": "completed"}, "completed cursor"),
    ],
)
def test_invalid_restored_cursor_fails_closed(
    change: dict[str, object],
    message: str,
) -> None:
    engine = MarketDataReplayEngine(
        replay_id="replay-invalid",
        events=_events(),
    )
    engine.start()
    engine.next_event()
    checkpoint = engine.cursor
    invalid = replace(checkpoint, **change)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=message):
        MarketDataReplayEngine(
            replay_id="replay-invalid",
            events=_events(),
            cursor=invalid,
        )


def test_invalid_lifecycle_transitions_fail_closed() -> None:
    engine = MarketDataReplayEngine(
        replay_id="replay-lifecycle",
        events=_events(),
    )

    with pytest.raises(ValueError, match="running replay"):
        engine.pause()
    with pytest.raises(ValueError, match="paused replay"):
        engine.resume()
    with pytest.raises(ValueError, match="running replay"):
        engine.next_event()

    engine.start()
    with pytest.raises(ValueError, match="ready replay"):
        engine.start()
    list(engine.iter_remaining())
    with pytest.raises(ValueError, match="paused replay"):
        engine.resume()


def test_empty_replay_completes_without_fabricating_market_time() -> None:
    engine = MarketDataReplayEngine(replay_id="replay-empty", events=[])
    restarted = MarketDataReplayEngine(
        replay_id="replay-empty",
        events=[],
        cursor=engine.cursor,
    )

    completed = restarted.start()

    assert completed.status == "completed"
    assert completed.start_time is None
    assert completed.current_time is None
    assert completed.cursor.position == 0
    assert completed.cursor.last_event_id is None


def test_cursor_and_session_are_immutable_canonical_snapshots() -> None:
    engine = MarketDataReplayEngine(
        replay_id="replay-snapshot",
        events=_events(),
    )
    cursor = engine.cursor
    session = engine.session

    assert cursor.to_dict()["schema_version"] == (
        MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION
    )
    assert session.to_dict()["cursor"] == cursor.to_dict()
    with pytest.raises(FrozenInstanceError):
        cursor.position = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        session.status = "running"  # type: ignore[misc]


def test_cursor_validates_shape_and_normalizes_time_to_utc() -> None:
    digest = "a" * 64
    cursor = ReplayCursor(
        replay_id="replay-cursor",
        event_stream_digest=digest,
        position=1,
        last_event_id="event-001",
        current_event_time=datetime(
            2026,
            7,
            28,
            17,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
        status="paused",
    )
    assert cursor.current_event_time == datetime(
        2026,
        7,
        28,
        9,
        30,
        tzinfo=timezone.utc,
    )

    with pytest.raises(ValueError, match="paired"):
        ReplayCursor(
            replay_id="replay-cursor",
            event_stream_digest=digest,
            position=1,
            last_event_id=None,
            current_event_time=cursor.current_event_time,
            status="paused",
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        ReplaySession(
            replay_id="replay-cursor",
            status="paused",
            start_time=datetime(2026, 7, 28, 9, 30),
            current_time=cursor.current_event_time,
            cursor=cursor,
        )
