"""Strict deterministic contracts for the M35 durable runtime foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from el_psy_quant.paper_execution import (
    ExecutionSettlementLink,
    PaperExecutionAttempt,
    PaperExecutionFill,
    PaperExecutionOrder,
    validate_execution_settlement_link,
    validate_paper_execution_attempt,
    validate_paper_execution_fill,
    validate_paper_execution_order,
)
from el_psy_quant.paper_runtime._canonical import (
    bounded_string,
    canonical_digest,
    canonical_json,
    digest,
    load_canonical_json,
    non_negative_int,
    reject_public_construction,
    utc_datetime,
)

PAPER_RUNTIME_SCHEMA_VERSION = 1
PAPER_RUNTIME_WORK_SCHEMA_VERSION = 1
PAPER_RUNTIME_CHECKPOINT_SCHEMA_VERSION = 1
PAPER_RUNTIME_EVENT_SCHEMA_VERSION = 1
PAPER_RUNTIME_COMMAND_RECEIPT_SCHEMA_VERSION = 1

PAPER_RUNTIME_DESIRED_STATES = ("running", "stopped")
PAPER_RUNTIME_OBSERVED_STATES = (
    "ready",
    "running",
    "stopped",
    "completed",
    "blocked",
)
PAPER_RUNTIME_EVENT_TYPES = (
    "runtime_created",
    "start_requested",
    "stop_requested",
    "resume_requested",
    "recover_requested",
    "claim_acquired",
    "claim_released",
    "claim_taken_over",
    "work_created",
    "work_observed",
    "runtime_completed",
    "runtime_blocked",
)
PAPER_RUNTIME_COMMAND_NAMESPACES = (
    "create_paper_runtime",
    "start_paper_runtime",
    "stop_paper_runtime",
    "resume_paper_runtime",
    "recover_paper_runtime",
)
COMMAND_EVENT_COMPATIBILITY = {
    "create_paper_runtime": "runtime_created",
    "start_paper_runtime": "start_requested",
    "stop_paper_runtime": "stop_requested",
    "resume_paper_runtime": "resume_requested",
    "recover_paper_runtime": "recover_requested",
}

DesiredState = Literal["running", "stopped"]
ObservedState = Literal["ready", "running", "stopped", "completed", "blocked"]
RuntimeEventType = Literal[
    "runtime_created",
    "start_requested",
    "stop_requested",
    "resume_requested",
    "recover_requested",
    "claim_acquired",
    "claim_released",
    "claim_taken_over",
    "work_created",
    "work_observed",
    "runtime_completed",
    "runtime_blocked",
]
RuntimeCommandNamespace = Literal[
    "create_paper_runtime",
    "start_paper_runtime",
    "stop_paper_runtime",
    "resume_paper_runtime",
    "recover_paper_runtime",
]


def _runtime_binding_payload(
    *,
    execution_order_id: str,
    execution_order_digest: str,
    account_id: str,
    replay_id: str,
    trading_session_id: str,
    logical_actor: str,
    runtime_policy_id: str,
    runtime_policy_version: int,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_RUNTIME_SCHEMA_VERSION,
        "execution_order_id": execution_order_id,
        "execution_order_digest": execution_order_digest,
        "account_id": account_id,
        "replay_id": replay_id,
        "trading_session_id": trading_session_id,
        "logical_actor": logical_actor,
        "runtime_policy_id": runtime_policy_id,
        "runtime_policy_version": runtime_policy_version,
    }


@dataclass(frozen=True, init=False)
class PaperRuntime:
    schema_version: int
    runtime_id: str
    runtime_binding_digest: str
    execution_order_id: str
    execution_order_digest: str
    account_id: str
    replay_id: str
    trading_session_id: str
    logical_actor: str
    runtime_policy_id: str
    runtime_policy_version: int
    desired_state: DesiredState
    observed_state: ObservedState
    owner_id: str | None
    fencing_token: int
    claimed_at: datetime | None
    heartbeat_at: datetime | None
    lease_expires_at: datetime | None
    row_version: int
    block_reason_code: str | None
    created_at: datetime
    updated_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "runtime_id": self.runtime_id,
            "runtime_binding_digest": self.runtime_binding_digest,
            "execution_order_id": self.execution_order_id,
            "execution_order_digest": self.execution_order_digest,
            "account_id": self.account_id,
            "replay_id": self.replay_id,
            "trading_session_id": self.trading_session_id,
            "logical_actor": self.logical_actor,
            "runtime_policy_id": self.runtime_policy_id,
            "runtime_policy_version": self.runtime_policy_version,
            "desired_state": self.desired_state,
            "observed_state": self.observed_state,
            "owner_id": self.owner_id,
            "fencing_token": self.fencing_token,
            "claimed_at": None
            if self.claimed_at is None
            else self.claimed_at.isoformat(),
            "heartbeat_at": None
            if self.heartbeat_at is None
            else self.heartbeat_at.isoformat(),
            "lease_expires_at": None
            if self.lease_expires_at is None
            else self.lease_expires_at.isoformat(),
            "row_version": self.row_version,
            "block_reason_code": self.block_reason_code,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def _build_runtime(**values: object) -> PaperRuntime:
    result = object.__new__(PaperRuntime)
    for name in PaperRuntime.__dataclass_fields__:
        object.__setattr__(result, name, values[name])
    return result


def create_paper_runtime(
    *,
    execution_order: PaperExecutionOrder,
    logical_actor: str,
    runtime_policy_id: str,
    runtime_policy_version: int,
    created_at: datetime,
) -> PaperRuntime:
    order = validate_paper_execution_order(execution_order)
    actor = bounded_string(logical_actor, "logical_actor", 256)
    policy = bounded_string(runtime_policy_id, "runtime_policy_id", 128)
    version = non_negative_int(runtime_policy_version, "runtime_policy_version")
    timestamp = utc_datetime(created_at, "created_at")
    market = order.market_handoff_reference
    binding = _runtime_binding_payload(
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        account_id=order.account_id,
        replay_id=market.replay_id,
        trading_session_id=market.trading_session_id,
        logical_actor=actor,
        runtime_policy_id=policy,
        runtime_policy_version=version,
    )
    binding_digest = canonical_digest(binding)
    return _build_runtime(
        schema_version=1,
        runtime_id=f"prt_{binding_digest}",
        runtime_binding_digest=binding_digest,
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        account_id=order.account_id,
        replay_id=market.replay_id,
        trading_session_id=market.trading_session_id,
        logical_actor=actor,
        runtime_policy_id=policy,
        runtime_policy_version=version,
        desired_state="stopped",
        observed_state="ready",
        owner_id=None,
        fencing_token=0,
        claimed_at=None,
        heartbeat_at=None,
        lease_expires_at=None,
        row_version=0,
        block_reason_code=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def validate_paper_runtime(value: object) -> PaperRuntime:
    if type(value) is not PaperRuntime:
        raise ValueError("runtime must be PaperRuntime")
    try:
        if value.schema_version != 1:
            raise ValueError("unsupported runtime schema")
        order_id = bounded_string(value.execution_order_id, "execution_order_id", 96)
        order_digest = digest(value.execution_order_digest, "execution_order_digest")
        account_id = bounded_string(value.account_id, "account_id", 512)
        replay_id = bounded_string(value.replay_id, "replay_id", 512)
        session_id = bounded_string(value.trading_session_id, "trading_session_id", 512)
        actor = bounded_string(value.logical_actor, "logical_actor", 256)
        policy = bounded_string(value.runtime_policy_id, "runtime_policy_id", 128)
        policy_version = non_negative_int(
            value.runtime_policy_version, "runtime_policy_version"
        )
        if value.desired_state not in PAPER_RUNTIME_DESIRED_STATES:
            raise ValueError("invalid desired state")
        if value.observed_state not in PAPER_RUNTIME_OBSERVED_STATES:
            raise ValueError("invalid observed state")
        if value.owner_id is None:
            if any(
                item is not None
                for item in (
                    value.claimed_at,
                    value.heartbeat_at,
                    value.lease_expires_at,
                )
            ):
                raise ValueError("unowned runtime cannot carry lease timestamps")
        else:
            bounded_string(value.owner_id, "owner_id", 256)
            if any(
                item is None
                for item in (
                    value.claimed_at,
                    value.heartbeat_at,
                    value.lease_expires_at,
                )
            ):
                raise ValueError("owned runtime requires all lease timestamps")
            utc_datetime(value.claimed_at, "claimed_at")
            utc_datetime(value.heartbeat_at, "heartbeat_at")
            utc_datetime(value.lease_expires_at, "lease_expires_at")
        non_negative_int(value.fencing_token, "fencing_token")
        non_negative_int(value.row_version, "row_version")
        if value.observed_state == "blocked":
            bounded_string(value.block_reason_code, "block_reason_code", 128)
        elif value.block_reason_code is not None:
            raise ValueError("non-blocked runtime cannot carry block reason")
        created = utc_datetime(value.created_at, "created_at")
        updated = utc_datetime(value.updated_at, "updated_at")
        if updated < created:
            raise ValueError("updated_at precedes created_at")
        binding = _runtime_binding_payload(
            execution_order_id=order_id,
            execution_order_digest=order_digest,
            account_id=account_id,
            replay_id=replay_id,
            trading_session_id=session_id,
            logical_actor=actor,
            runtime_policy_id=policy,
            runtime_policy_version=policy_version,
        )
        expected = canonical_digest(binding)
        digest(value.runtime_binding_digest, "runtime_binding_digest")
        if (
            value.runtime_binding_digest != expected
            or value.runtime_id != f"prt_{expected}"
        ):
            raise ValueError("runtime binding identity is invalid")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper runtime is invalid") from exc
    return value


def _work_identity_payload(runtime: PaperRuntime, version: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "runtime_id": runtime.runtime_id,
        "execution_order_id": runtime.execution_order_id,
        "execution_order_digest": runtime.execution_order_digest,
        "expected_execution_version": version,
        "m34_step_actor": runtime.logical_actor,
    }


@dataclass(frozen=True, init=False)
class PaperRuntimeWork:
    schema_version: int
    work_id: str
    work_digest: str
    runtime_id: str
    execution_order_id: str
    execution_order_digest: str
    expected_execution_version: int
    m34_step_idempotency_key: str
    m34_step_actor: str
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "work_id": self.work_id,
            "work_digest": self.work_digest,
            "runtime_id": self.runtime_id,
            "execution_order_id": self.execution_order_id,
            "execution_order_digest": self.execution_order_digest,
            "expected_execution_version": self.expected_execution_version,
            "m34_step_idempotency_key": self.m34_step_idempotency_key,
            "m34_step_actor": self.m34_step_actor,
            "created_at": self.created_at.isoformat(),
        }


def _build_work(**values: object) -> PaperRuntimeWork:
    result = object.__new__(PaperRuntimeWork)
    for name in PaperRuntimeWork.__dataclass_fields__:
        object.__setattr__(result, name, values[name])
    return result


def create_paper_runtime_work(
    *, runtime: PaperRuntime, expected_execution_version: int, created_at: datetime
) -> PaperRuntimeWork:
    valid = validate_paper_runtime(runtime)
    version = non_negative_int(expected_execution_version, "expected_execution_version")
    identity_digest = canonical_digest(_work_identity_payload(valid, version))
    key = f"m35-step-{identity_digest}"
    payload = {
        **_work_identity_payload(valid, version),
        "m34_step_idempotency_key": key,
    }
    work_digest = canonical_digest(payload)
    return _build_work(
        schema_version=1,
        work_id=f"prw_{work_digest}",
        work_digest=work_digest,
        runtime_id=valid.runtime_id,
        execution_order_id=valid.execution_order_id,
        execution_order_digest=valid.execution_order_digest,
        expected_execution_version=version,
        m34_step_idempotency_key=key,
        m34_step_actor=valid.logical_actor,
        created_at=utc_datetime(created_at, "created_at"),
    )


def validate_paper_runtime_work(
    value: object, *, runtime: PaperRuntime
) -> PaperRuntimeWork:
    if type(value) is not PaperRuntimeWork:
        raise ValueError("work must be PaperRuntimeWork")
    try:
        valid_runtime = validate_paper_runtime(runtime)
        if value.schema_version != 1 or value.runtime_id != valid_runtime.runtime_id:
            raise ValueError("work runtime mismatch")
        version = non_negative_int(
            value.expected_execution_version, "expected_execution_version"
        )
        if (
            value.execution_order_id != valid_runtime.execution_order_id
            or value.execution_order_digest != valid_runtime.execution_order_digest
            or value.m34_step_actor != valid_runtime.logical_actor
        ):
            raise ValueError("work binding mismatch")
        identity_digest = canonical_digest(
            _work_identity_payload(valid_runtime, version)
        )
        key = f"m35-step-{identity_digest}"
        if value.m34_step_idempotency_key != key:
            raise ValueError("work Step key mismatch")
        expected = canonical_digest(
            {
                **_work_identity_payload(valid_runtime, version),
                "m34_step_idempotency_key": key,
            }
        )
        if value.work_digest != expected or value.work_id != f"prw_{expected}":
            raise ValueError("work identity mismatch")
        utc_datetime(value.created_at, "created_at")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper runtime work is invalid") from exc
    return value


@dataclass(frozen=True, init=False)
class PaperRuntimeCheckpoint:
    schema_version: int
    checkpoint_id: str
    checkpoint_digest: str
    runtime_id: str
    work_id: str
    execution_order_id: str
    execution_order_digest: str
    observed_execution_version: int
    attempt_id: str
    attempt_digest: str
    fill_id: str | None
    fill_digest: str | None
    settlement_link_id: str | None
    settlement_link_evidence_digest: str | None
    account_event_id: str | None
    replay_id: str
    event_stream_digest: str
    post_cursor_position: int
    post_cursor_last_event_id: str | None
    observed_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **{
                name: getattr(self, name)
                for name in self.__dataclass_fields__
                if name != "observed_at"
            },
            "observed_at": self.observed_at.isoformat(),
        }


def _build_checkpoint(**values: object) -> PaperRuntimeCheckpoint:
    result = object.__new__(PaperRuntimeCheckpoint)
    for name in PaperRuntimeCheckpoint.__dataclass_fields__:
        object.__setattr__(result, name, values[name])
    return result


def _checkpoint_payload(**values: object) -> dict[str, object]:
    return {"schema_version": 1, **values}


def create_paper_runtime_checkpoint(
    *,
    runtime: PaperRuntime,
    work: PaperRuntimeWork,
    attempt: PaperExecutionAttempt,
    fill: PaperExecutionFill | None,
    settlement_link: ExecutionSettlementLink | None,
    observed_at: datetime,
) -> PaperRuntimeCheckpoint:
    rt = validate_paper_runtime(runtime)
    wk = validate_paper_runtime_work(work, runtime=rt)
    att = validate_paper_execution_attempt(attempt)
    order_ref = create_paper_execution_order_reference_from_runtime(rt)
    if (
        att.execution_order_reference != order_ref
        or att.execution_version_before != wk.expected_execution_version
        or att.execution_version_after != wk.expected_execution_version + 1
    ):
        raise ValueError("Attempt does not match runtime work")
    valid_fill = None if fill is None else validate_paper_execution_fill(fill)
    valid_link = (
        None
        if settlement_link is None
        else validate_execution_settlement_link(settlement_link)
    )
    if (valid_fill is None) is not (valid_link is None):
        raise ValueError("Fill and settlement link must be paired")
    if valid_fill is not None:
        if att.attempt_result != "fill":
            raise ValueError("non-fill Attempt cannot carry Fill evidence")
        if (
            valid_fill.attempt_reference.attempt_id != att.attempt_id
            or valid_link.execution_fill_reference.fill_id != valid_fill.fill_id
            or valid_link.execution_attempt_reference.attempt_id != att.attempt_id
        ):
            raise ValueError("Fill settlement references do not match Attempt")
    elif att.attempt_result == "fill":
        raise ValueError("fill Attempt requires Fill settlement evidence")
    cursor = att.post_step_cursor
    values = {
        "runtime_id": rt.runtime_id,
        "work_id": wk.work_id,
        "execution_order_id": rt.execution_order_id,
        "execution_order_digest": rt.execution_order_digest,
        "observed_execution_version": att.execution_version_after,
        "attempt_id": att.attempt_id,
        "attempt_digest": att.attempt_digest,
        "fill_id": None if valid_fill is None else valid_fill.fill_id,
        "fill_digest": None if valid_fill is None else valid_fill.fill_digest,
        "settlement_link_id": None
        if valid_link is None
        else valid_link.settlement_link_id,
        "settlement_link_evidence_digest": None
        if valid_link is None
        else valid_link.settlement_link_evidence_digest,
        "account_event_id": None if valid_link is None else valid_link.account_event_id,
        "replay_id": rt.replay_id,
        "event_stream_digest": cursor.event_stream_digest,
        "post_cursor_position": cursor.position,
        "post_cursor_last_event_id": cursor.last_event_id,
        "observed_at": utc_datetime(observed_at, "observed_at").isoformat(),
    }
    checkpoint_digest = canonical_digest(_checkpoint_payload(**values))
    return _build_checkpoint(
        schema_version=1,
        checkpoint_id=f"prc_{checkpoint_digest}",
        checkpoint_digest=checkpoint_digest,
        **{**values, "observed_at": datetime.fromisoformat(values["observed_at"])},
    )


def create_paper_execution_order_reference_from_runtime(runtime: PaperRuntime):
    from el_psy_quant.paper_execution.orders import PaperExecutionOrderReference

    result = object.__new__(PaperExecutionOrderReference)
    object.__setattr__(result, "schema_version", 1)
    object.__setattr__(result, "execution_order_id", runtime.execution_order_id)
    object.__setattr__(result, "execution_order_digest", runtime.execution_order_digest)
    return result


def validate_paper_runtime_checkpoint(
    value: object, *, runtime: PaperRuntime, work: PaperRuntimeWork
) -> PaperRuntimeCheckpoint:
    if type(value) is not PaperRuntimeCheckpoint:
        raise ValueError("checkpoint must be PaperRuntimeCheckpoint")
    try:
        rt = validate_paper_runtime(runtime)
        wk = validate_paper_runtime_work(work, runtime=rt)
        if (
            value.schema_version != 1
            or value.runtime_id != rt.runtime_id
            or value.work_id != wk.work_id
        ):
            raise ValueError("checkpoint work binding mismatch")
        if (
            value.execution_order_id != rt.execution_order_id
            or value.execution_order_digest != rt.execution_order_digest
        ):
            raise ValueError("checkpoint Order binding mismatch")
        if value.observed_execution_version != wk.expected_execution_version + 1:
            raise ValueError("checkpoint execution version mismatch")
        bounded_string(value.attempt_id, "attempt_id", 96)
        digest(value.attempt_digest, "attempt_digest")
        group = (
            value.fill_id,
            value.fill_digest,
            value.settlement_link_id,
            value.settlement_link_evidence_digest,
            value.account_event_id,
        )
        if any(item is None for item in group) and any(
            item is not None for item in group
        ):
            raise ValueError("checkpoint optional authority group is incomplete")
        if value.fill_id is not None:
            bounded_string(value.fill_id, "fill_id", 96)
            digest(value.fill_digest, "fill_digest")
            bounded_string(value.settlement_link_id, "settlement_link_id", 96)
            digest(
                value.settlement_link_evidence_digest, "settlement_link_evidence_digest"
            )
            bounded_string(value.account_event_id, "account_event_id", 512)
        if value.replay_id != rt.replay_id:
            raise ValueError("checkpoint replay mismatch")
        digest(value.event_stream_digest, "event_stream_digest")
        non_negative_int(value.post_cursor_position, "post_cursor_position")
        if value.post_cursor_last_event_id is not None:
            bounded_string(
                value.post_cursor_last_event_id, "post_cursor_last_event_id", 512
            )
        observed = utc_datetime(value.observed_at, "observed_at")
        raw = {
            name: getattr(value, name)
            for name in value.__dataclass_fields__
            if name
            not in {
                "schema_version",
                "checkpoint_id",
                "checkpoint_digest",
                "observed_at",
            }
        }
        raw["observed_at"] = observed.isoformat()
        expected = canonical_digest(_checkpoint_payload(**raw))
        if (
            value.checkpoint_digest != expected
            or value.checkpoint_id != f"prc_{expected}"
        ):
            raise ValueError("checkpoint identity mismatch")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper runtime checkpoint is invalid") from exc
    return value


@dataclass(frozen=True, init=False)
class PaperRuntimeEvent:
    schema_version: int
    event_id: str
    event_digest: str
    runtime_id: str
    event_sequence: int
    event_type: RuntimeEventType
    resulting_runtime_version: int
    payload_json: str
    recorded_at: datetime
    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_digest": self.event_digest,
            "runtime_id": self.runtime_id,
            "event_sequence": self.event_sequence,
            "event_type": self.event_type,
            "resulting_runtime_version": self.resulting_runtime_version,
            "payload": load_canonical_json(self.payload_json),
            "recorded_at": self.recorded_at.isoformat(),
        }


def _event_business(
    runtime_id: str,
    sequence: int,
    event_type: str,
    version: int,
    payload_json: str,
    recorded_at: datetime,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "runtime_id": runtime_id,
        "event_sequence": sequence,
        "event_type": event_type,
        "resulting_runtime_version": version,
        "payload": load_canonical_json(payload_json),
        "recorded_at": recorded_at.isoformat(),
    }


def create_paper_runtime_event(
    *,
    runtime: PaperRuntime,
    event_sequence: int,
    event_type: RuntimeEventType,
    resulting_runtime_version: int,
    payload: object,
    recorded_at: datetime,
) -> PaperRuntimeEvent:
    rt = validate_paper_runtime(runtime)
    sequence = non_negative_int(event_sequence, "event_sequence")
    version = non_negative_int(resulting_runtime_version, "resulting_runtime_version")
    if event_type not in PAPER_RUNTIME_EVENT_TYPES:
        raise ValueError("unsupported runtime event type")
    payload_json = canonical_json(payload)
    load_canonical_json(payload_json)
    timestamp = utc_datetime(recorded_at, "recorded_at")
    event_digest = canonical_digest(
        _event_business(
            rt.runtime_id, sequence, event_type, version, payload_json, timestamp
        )
    )
    result = object.__new__(PaperRuntimeEvent)
    for name, item in (
        ("schema_version", 1),
        ("event_id", f"pre_{event_digest}"),
        ("event_digest", event_digest),
        ("runtime_id", rt.runtime_id),
        ("event_sequence", sequence),
        ("event_type", event_type),
        ("resulting_runtime_version", version),
        ("payload_json", payload_json),
        ("recorded_at", timestamp),
    ):
        object.__setattr__(result, name, item)
    return result


def validate_paper_runtime_event(
    value: object, *, runtime: PaperRuntime
) -> PaperRuntimeEvent:
    if type(value) is not PaperRuntimeEvent:
        raise ValueError("event must be PaperRuntimeEvent")
    try:
        rt = validate_paper_runtime(runtime)
        if (
            value.schema_version != 1
            or value.runtime_id != rt.runtime_id
            or value.event_type not in PAPER_RUNTIME_EVENT_TYPES
        ):
            raise ValueError("event binding is invalid")
        sequence = non_negative_int(value.event_sequence, "event_sequence")
        version = non_negative_int(
            value.resulting_runtime_version, "resulting_runtime_version"
        )
        timestamp = utc_datetime(value.recorded_at, "recorded_at")
        load_canonical_json(value.payload_json)
        expected = canonical_digest(
            _event_business(
                rt.runtime_id,
                sequence,
                value.event_type,
                version,
                value.payload_json,
                timestamp,
            )
        )
        if value.event_digest != expected or value.event_id != f"pre_{expected}":
            raise ValueError("event identity mismatch")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper runtime event is invalid") from exc
    return value


@dataclass(frozen=True)
class PaperRuntimeCommandReceipt:
    namespace: RuntimeCommandNamespace
    command_idempotency_key: str
    command_digest: str
    command_actor: str
    runtime_id: str
    result_event_id: str
    result_event_digest: str
    resulting_runtime_version: int
    created_at: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1
            or self.namespace not in PAPER_RUNTIME_COMMAND_NAMESPACES
        ):
            raise ValueError("unsupported runtime receipt schema or namespace")
        bounded_string(self.command_idempotency_key, "command_idempotency_key", 128)
        digest(self.command_digest, "command_digest")
        bounded_string(self.command_actor, "command_actor", 256)
        bounded_string(self.runtime_id, "runtime_id", 96)
        bounded_string(self.result_event_id, "result_event_id", 96)
        digest(self.result_event_digest, "result_event_digest")
        non_negative_int(self.resulting_runtime_version, "resulting_runtime_version")
        utc_datetime(self.created_at, "created_at")


def create_paper_runtime_command_receipt(
    *,
    namespace: RuntimeCommandNamespace,
    command_idempotency_key: str,
    command_digest: str,
    command_actor: str,
    runtime: PaperRuntime,
    result_event: PaperRuntimeEvent,
    created_at: datetime,
) -> PaperRuntimeCommandReceipt:
    rt = validate_paper_runtime(runtime)
    event = validate_paper_runtime_event(result_event, runtime=rt)
    if COMMAND_EVENT_COMPATIBILITY.get(namespace) != event.event_type:
        raise ValueError("receipt namespace is incompatible with result event")
    return PaperRuntimeCommandReceipt(
        namespace=namespace,
        command_idempotency_key=command_idempotency_key,
        command_digest=command_digest,
        command_actor=command_actor,
        runtime_id=rt.runtime_id,
        result_event_id=event.event_id,
        result_event_digest=event.event_digest,
        resulting_runtime_version=event.resulting_runtime_version,
        created_at=utc_datetime(created_at, "created_at"),
    )


def validate_paper_runtime_command_receipt(
    value: object, *, runtime: PaperRuntime, result_event: PaperRuntimeEvent
) -> PaperRuntimeCommandReceipt:
    if type(value) is not PaperRuntimeCommandReceipt:
        raise ValueError("receipt must be PaperRuntimeCommandReceipt")
    rt = validate_paper_runtime(runtime)
    event = validate_paper_runtime_event(result_event, runtime=rt)
    if (
        value.runtime_id != rt.runtime_id
        or value.result_event_id != event.event_id
        or value.result_event_digest != event.event_digest
        or value.resulting_runtime_version != event.resulting_runtime_version
        or COMMAND_EVENT_COMPATIBILITY.get(value.namespace) != event.event_type
    ):
        raise ValueError("runtime receipt result evidence is invalid")
    return value


__all__ = [
    name
    for name in globals()
    if name.startswith("PAPER_RUNTIME_")
    or name.startswith("PaperRuntime")
    or name.startswith("create_paper_runtime")
    or name.startswith("validate_paper_runtime")
]
