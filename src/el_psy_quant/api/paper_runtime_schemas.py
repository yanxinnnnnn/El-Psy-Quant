"""Strict public schemas for the M35 Paper Runtime v1 boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

BoundedId = Annotated[
    StrictStr, Field(min_length=1, max_length=512, pattern=r"^\S(?:.*\S)?$")
]
BoundedActor = Annotated[
    StrictStr, Field(min_length=1, max_length=256, pattern=r"^\S(?:.*\S)?$")
]
RuntimePolicyId = Annotated[
    StrictStr, Field(min_length=1, max_length=128, pattern=r"^\S(?:.*\S)?$")
]
Sha256Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
RuntimeId = Annotated[StrictStr, Field(pattern=r"^prt_[0-9a-f]{64}$")]
WorkId = Annotated[StrictStr, Field(pattern=r"^prw_[0-9a-f]{64}$")]
CheckpointId = Annotated[StrictStr, Field(pattern=r"^prc_[0-9a-f]{64}$")]
RuntimeEventId = Annotated[StrictStr, Field(pattern=r"^pre_[0-9a-f]{64}$")]
ExecutionOrderId = Annotated[StrictStr, Field(pattern=r"^peo_[0-9a-f]{64}$")]
DesiredState = Literal["running", "stopped"]
ObservedState = Literal["ready", "running", "stopped", "completed", "blocked"]
LeaseStatus = Literal["unowned", "active", "expired"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def _normalized_utc(value: object) -> object:
    if value is None:
        return None
    if type(value) is datetime:
        parsed = value
    elif type(value) is str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (OverflowError, ValueError) as exc:
            raise ValueError("timestamp must be normalized UTC") from exc
    else:
        raise ValueError("timestamp must be normalized UTC")
    offset = parsed.utcoffset()
    if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp must be normalized UTC")
    return parsed.astimezone(timezone.utc)


class PaperRuntimeCreateRequest(_StrictModel):
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    logical_actor: BoundedActor
    runtime_policy_id: RuntimePolicyId
    runtime_policy_version: Annotated[StrictInt, Field(ge=0)]
    actor: BoundedActor


class PaperRuntimeControlRequest(_StrictModel):
    runtime_binding_digest: Sha256Digest
    expected_runtime_version: Annotated[StrictInt, Field(ge=0)]
    actor: BoundedActor


class PaperRuntimeResponse(_StrictModel):
    schema_version: Literal[1]
    runtime_id: RuntimeId
    runtime_binding_digest: Sha256Digest
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    account_id: BoundedId
    replay_id: BoundedId
    trading_session_id: BoundedId
    logical_actor: BoundedActor
    runtime_policy_id: RuntimePolicyId
    runtime_policy_version: Annotated[StrictInt, Field(ge=0)]
    desired_state: DesiredState
    observed_state: ObservedState
    owner_id: BoundedActor | None
    fencing_token: Annotated[StrictInt, Field(ge=0)]
    claimed_at: datetime | None
    heartbeat_at: datetime | None
    lease_expires_at: datetime | None
    row_version: Annotated[StrictInt, Field(ge=0)]
    block_reason_code: Annotated[
        StrictStr, Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_]+$")
    ] | None
    created_at: datetime
    updated_at: datetime

    _validate_claimed = field_validator("claimed_at", mode="before")(_normalized_utc)
    _validate_heartbeat = field_validator("heartbeat_at", mode="before")(
        _normalized_utc
    )
    _validate_lease = field_validator("lease_expires_at", mode="before")(
        _normalized_utc
    )
    _validate_created = field_validator("created_at", mode="before")(_normalized_utc)
    _validate_updated = field_validator("updated_at", mode="before")(_normalized_utc)


class PaperRuntimeCommandResponse(_StrictModel):
    schema_version: Literal[1]
    replayed: bool
    request_id: StrictStr
    runtime: PaperRuntimeResponse


class PaperRuntimeListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperRuntimeResponse]
    next_cursor: StrictStr | None


class PaperRuntimeHealthResponse(_StrictModel):
    schema_version: Literal[1]
    runtime_id: RuntimeId
    desired_state: DesiredState
    observed_state: ObservedState
    row_version: Annotated[StrictInt, Field(ge=0)]
    fencing_token: Annotated[StrictInt, Field(ge=0)]
    claimed: bool
    lease_status: LeaseStatus
    claimed_at: datetime | None
    heartbeat_at: datetime | None
    lease_expires_at: datetime | None
    terminal: bool
    blocked: bool
    block_reason_code: Annotated[
        StrictStr, Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_]+$")
    ] | None
    checked_at: datetime

    _validate_claimed = field_validator("claimed_at", mode="before")(_normalized_utc)
    _validate_heartbeat = field_validator("heartbeat_at", mode="before")(
        _normalized_utc
    )
    _validate_lease = field_validator("lease_expires_at", mode="before")(
        _normalized_utc
    )
    _validate_checked = field_validator("checked_at", mode="before")(_normalized_utc)


class PaperRuntimeReconciliationResponse(_StrictModel):
    schema_version: Literal[1]
    runtime_id: RuntimeId
    runtime_binding_digest: Sha256Digest
    status: Literal[
        "coherent_nonterminal",
        "coherent_terminal",
        "coherent_stopped",
        "blocked",
        "continuation_stale",
    ]
    historical_coherent: Literal[True]
    continuation_status: Literal["current", "stale", "not_applicable"]
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    execution_version: Annotated[StrictInt, Field(ge=0)]
    execution_terminal: bool
    work_count: Annotated[StrictInt, Field(ge=0)]
    checkpoint_count: Annotated[StrictInt, Field(ge=0)]
    event_count: Annotated[StrictInt, Field(ge=0)]
    pending_work_id: WorkId | None


class PaperRuntimeAuditEntryResponse(_StrictModel):
    schema_version: Literal[1]
    event_id: RuntimeEventId
    event_digest: Sha256Digest
    runtime_id: RuntimeId
    event_sequence: Annotated[StrictInt, Field(ge=0)]
    event_type: Literal[
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
    resulting_runtime_version: Annotated[StrictInt, Field(ge=0)]
    recorded_at: datetime
    work_id: WorkId | None
    checkpoint_id: CheckpointId | None

    _validate_recorded = field_validator("recorded_at", mode="before")(
        _normalized_utc
    )


class PaperRuntimeAuditListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperRuntimeAuditEntryResponse]
    next_cursor: StrictStr | None


class PaperRuntimeWorkResponse(_StrictModel):
    schema_version: Literal[1]
    work_id: WorkId
    work_digest: Sha256Digest
    runtime_id: RuntimeId
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    expected_execution_version: Annotated[StrictInt, Field(ge=0)]
    m34_step_idempotency_key: Annotated[
        StrictStr, Field(min_length=1, max_length=128)
    ]
    m34_step_actor: BoundedActor
    created_at: datetime

    _validate_created = field_validator("created_at", mode="before")(_normalized_utc)


class PaperRuntimeWorkListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperRuntimeWorkResponse]
    next_cursor: StrictStr | None


class PaperRuntimeCheckpointResponse(_StrictModel):
    schema_version: Literal[1]
    checkpoint_id: CheckpointId
    checkpoint_digest: Sha256Digest
    runtime_id: RuntimeId
    work_id: WorkId
    execution_order_id: ExecutionOrderId
    execution_order_digest: Sha256Digest
    observed_execution_version: Annotated[StrictInt, Field(gt=0)]
    attempt_id: BoundedId
    attempt_digest: Sha256Digest
    fill_id: BoundedId | None
    fill_digest: Sha256Digest | None
    settlement_link_id: BoundedId | None
    settlement_link_evidence_digest: Sha256Digest | None
    account_event_id: BoundedId | None
    replay_id: BoundedId
    event_stream_digest: Sha256Digest
    post_cursor_position: Annotated[StrictInt, Field(ge=0)]
    post_cursor_last_event_id: BoundedId | None
    observed_at: datetime

    _validate_observed = field_validator("observed_at", mode="before")(
        _normalized_utc
    )


class PaperRuntimeCheckpointListResponse(_StrictModel):
    schema_version: Literal[1]
    items: list[PaperRuntimeCheckpointResponse]
    next_cursor: StrictStr | None


__all__ = [
    "DesiredState",
    "ObservedState",
    "PaperRuntimeAuditEntryResponse",
    "PaperRuntimeAuditListResponse",
    "PaperRuntimeCheckpointListResponse",
    "PaperRuntimeCheckpointResponse",
    "PaperRuntimeCommandResponse",
    "PaperRuntimeControlRequest",
    "PaperRuntimeCreateRequest",
    "PaperRuntimeHealthResponse",
    "PaperRuntimeListResponse",
    "PaperRuntimeReconciliationResponse",
    "PaperRuntimeResponse",
    "PaperRuntimeWorkListResponse",
    "PaperRuntimeWorkResponse",
    "RuntimeId",
]
