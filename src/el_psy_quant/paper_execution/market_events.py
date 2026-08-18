"""Compact immutable M32 event-consumption evidence for M34 execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.market_time import MarketDataEvent, ReplayCursor
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)

PAPER_EXECUTION_EVENT_REFERENCE_SCHEMA_VERSION = 1


def _payload(
    *,
    schema_version: int,
    replay_id: str,
    event_stream_digest: str,
    pre_step_cursor_position: int,
    consumed_event_position: int,
    event_id: str,
    event_digest: str,
    event_time: datetime,
    instrument_id: str,
    event_type: str,
    post_step_cursor_position: int,
    post_step_last_event_id: str,
    post_step_current_event_time: datetime,
    post_step_replay_status: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "replay_id": replay_id,
        "event_stream_digest": event_stream_digest,
        "pre_step_cursor_position": pre_step_cursor_position,
        "consumed_event_position": consumed_event_position,
        "event_id": event_id,
        "event_digest": event_digest,
        "event_time": event_time.isoformat(),
        "instrument_id": instrument_id,
        "event_type": event_type,
        "post_step_cursor_position": post_step_cursor_position,
        "post_step_last_event_id": post_step_last_event_id,
        "post_step_current_event_time": (
            post_step_current_event_time.isoformat()
        ),
        "post_step_replay_status": post_step_replay_status,
    }


@dataclass(frozen=True, init=False)
class PaperExecutionEventReference:
    """One exact consumed canonical M32 event and cursor transition."""

    schema_version: int
    replay_id: str
    event_stream_digest: str
    pre_step_cursor_position: int
    consumed_event_position: int
    event_id: str
    event_digest: str
    event_time: datetime
    instrument_id: str
    event_type: str
    post_step_cursor_position: int
    post_step_last_event_id: str
    post_step_current_event_time: datetime
    post_step_replay_status: str
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                replay_id=self.replay_id,
                event_stream_digest=self.event_stream_digest,
                pre_step_cursor_position=self.pre_step_cursor_position,
                consumed_event_position=self.consumed_event_position,
                event_id=self.event_id,
                event_digest=self.event_digest,
                event_time=self.event_time,
                instrument_id=self.instrument_id,
                event_type=self.event_type,
                post_step_cursor_position=self.post_step_cursor_position,
                post_step_last_event_id=self.post_step_last_event_id,
                post_step_current_event_time=(self.post_step_current_event_time),
                post_step_replay_status=self.post_step_replay_status,
            ),
            "reference_digest": self.reference_digest,
        }


def _build(
    *,
    event: MarketDataEvent,
    pre_step_cursor: ReplayCursor,
    post_step_cursor: ReplayCursor,
) -> PaperExecutionEventReference:
    event_digest = canonical_digest(event.to_dict())
    payload = _payload(
        schema_version=PAPER_EXECUTION_EVENT_REFERENCE_SCHEMA_VERSION,
        replay_id=pre_step_cursor.replay_id,
        event_stream_digest=pre_step_cursor.event_stream_digest,
        pre_step_cursor_position=pre_step_cursor.position,
        consumed_event_position=post_step_cursor.position,
        event_id=event.event_id,
        event_digest=event_digest,
        event_time=event.event_time,
        instrument_id=event.instrument_id,
        event_type=event.event_type,
        post_step_cursor_position=post_step_cursor.position,
        post_step_last_event_id=event.event_id,
        post_step_current_event_time=event.event_time,
        post_step_replay_status=post_step_cursor.status,
    )
    result = object.__new__(PaperExecutionEventReference)
    values = {
        "schema_version": PAPER_EXECUTION_EVENT_REFERENCE_SCHEMA_VERSION,
        "replay_id": pre_step_cursor.replay_id,
        "event_stream_digest": pre_step_cursor.event_stream_digest,
        "pre_step_cursor_position": pre_step_cursor.position,
        "consumed_event_position": post_step_cursor.position,
        "event_id": event.event_id,
        "event_digest": event_digest,
        "event_time": event.event_time,
        "instrument_id": event.instrument_id,
        "event_type": event.event_type,
        "post_step_cursor_position": post_step_cursor.position,
        "post_step_last_event_id": event.event_id,
        "post_step_current_event_time": event.event_time,
        "post_step_replay_status": post_step_cursor.status,
        "reference_digest": canonical_digest(payload),
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def create_paper_execution_event_reference(
    *,
    event: MarketDataEvent,
    pre_step_cursor: ReplayCursor,
    post_step_cursor: ReplayCursor,
) -> PaperExecutionEventReference:
    """Bind one event to the exact single-step cursor transition."""
    if type(event) is not MarketDataEvent:
        raise ValueError("event must be MarketDataEvent")
    if type(pre_step_cursor) is not ReplayCursor:
        raise ValueError("pre_step_cursor must be ReplayCursor")
    if type(post_step_cursor) is not ReplayCursor:
        raise ValueError("post_step_cursor must be ReplayCursor")
    if not (
        pre_step_cursor.replay_id == post_step_cursor.replay_id
        and pre_step_cursor.event_stream_digest
        == post_step_cursor.event_stream_digest
        and post_step_cursor.position == pre_step_cursor.position + 1
        and post_step_cursor.last_event_id == event.event_id
        and post_step_cursor.current_event_time == event.event_time
        and post_step_cursor.status in {"running", "completed"}
    ):
        raise ValueError("event reference cursor transition is invalid")
    return _build(
        event=event,
        pre_step_cursor=pre_step_cursor,
        post_step_cursor=post_step_cursor,
    )


def validate_paper_execution_event_reference(
    value: object,
) -> PaperExecutionEventReference:
    if type(value) is not PaperExecutionEventReference:
        raise ValueError("event reference must be PaperExecutionEventReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_EVENT_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported event reference schema_version")
        if (
            type(value.pre_step_cursor_position) is not int
            or value.pre_step_cursor_position < 0
            or type(value.consumed_event_position) is not int
            or type(value.post_step_cursor_position) is not int
            or value.consumed_event_position
            != value.pre_step_cursor_position + 1
            or value.post_step_cursor_position != value.consumed_event_position
        ):
            raise ValueError("event reference positions are invalid")
        if value.post_step_last_event_id != value.event_id:
            raise ValueError("event reference last event is invalid")
        event_time = normalize_utc_datetime(value.event_time, field_name="event_time")
        post_time = normalize_utc_datetime(
            value.post_step_current_event_time,
            field_name="post_step_current_event_time",
        )
        if event_time != value.event_time or post_time != event_time:
            raise ValueError("event reference times are invalid")
        if value.post_step_replay_status not in {"running", "completed"}:
            raise ValueError("event reference replay status is invalid")
        validate_digest(value.event_stream_digest, field_name="event_stream_digest")
        validate_digest(value.event_digest, field_name="event_digest")
        validate_digest(value.reference_digest, field_name="reference_digest")
        payload = _payload(
            schema_version=value.schema_version,
            replay_id=value.replay_id,
            event_stream_digest=value.event_stream_digest,
            pre_step_cursor_position=value.pre_step_cursor_position,
            consumed_event_position=value.consumed_event_position,
            event_id=value.event_id,
            event_digest=value.event_digest,
            event_time=value.event_time,
            instrument_id=value.instrument_id,
            event_type=value.event_type,
            post_step_cursor_position=value.post_step_cursor_position,
            post_step_last_event_id=value.post_step_last_event_id,
            post_step_current_event_time=value.post_step_current_event_time,
            post_step_replay_status=value.post_step_replay_status,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution event reference is invalid") from exc
    if canonical_digest(payload) != value.reference_digest:
        raise ValueError("paper execution event reference is invalid")
    return value


def _clone_event_reference(
    value: PaperExecutionEventReference,
) -> PaperExecutionEventReference:
    validate_paper_execution_event_reference(value)
    result = object.__new__(PaperExecutionEventReference)
    for field_name in PaperExecutionEventReference.__dataclass_fields__:
        object.__setattr__(result, field_name, getattr(value, field_name))
    return result
