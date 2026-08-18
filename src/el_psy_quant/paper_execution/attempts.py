"""Immutable one-step Paper execution Attempt authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from el_psy_quant.market_time import ReplayCursor
from el_psy_quant.paper_execution._canonical import (
    canonical_digest,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.paper_execution.execution_risk import (
    PaperExecutionRiskRevalidation,
    _clone_risk_revalidation,
    validate_paper_execution_risk_revalidation,
)
from el_psy_quant.paper_execution.lifecycle import (
    PaperExecutionOrderState,
    _clone_order_state,
    validate_paper_execution_order_state,
)
from el_psy_quant.paper_execution.market_events import (
    PaperExecutionEventReference,
    _clone_event_reference,
    validate_paper_execution_event_reference,
)
from el_psy_quant.paper_execution.orders import (
    PaperExecutionOrderReference,
    _clone_order_reference,
    validate_paper_execution_order_reference,
)

PAPER_EXECUTION_ATTEMPT_SCHEMA_VERSION = 1
PAPER_EXECUTION_ATTEMPT_REFERENCE_SCHEMA_VERSION = 1

PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL = "no_fill"
PAPER_EXECUTION_ATTEMPT_RESULT_FILL = "fill"
PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED = "risk_rejected"
PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED = "boundary_rejected"

PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH = "instrument_mismatch"
PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE = "event_type_not_trade"
PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID = "trade_price_invalid"

PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED = (
    "execution_risk_rejected"
)
PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED = "replay_exhausted"
PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED = "session_exhausted"

SUPPORTED_PAPER_EXECUTION_ATTEMPT_RESULTS = (
    PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED,
    PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED,
)
SUPPORTED_PAPER_EXECUTION_NO_FILL_REASONS = (
    PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH,
    PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE,
    PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID,
)
SUPPORTED_PAPER_EXECUTION_TERMINAL_REASONS = (
    PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED,
    PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED,
    PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED,
)

PaperExecutionAttemptResult = Literal[
    "no_fill", "fill", "risk_rejected", "boundary_rejected"
]


def _clone_cursor(value: ReplayCursor) -> ReplayCursor:
    if type(value) is not ReplayCursor:
        raise ValueError("attempt cursor must be ReplayCursor")
    return ReplayCursor(
        replay_id=value.replay_id,
        event_stream_digest=value.event_stream_digest,
        position=value.position,
        last_event_id=value.last_event_id,
        current_event_time=value.current_event_time,
        status=value.status,
    )


def _payload(
    *,
    schema_version: int,
    execution_order_reference: PaperExecutionOrderReference,
    execution_version_before: int,
    execution_version_after: int,
    prior_order_state: PaperExecutionOrderState,
    pre_step_cursor: ReplayCursor,
    post_step_cursor: ReplayCursor,
    consumed_event_reference: PaperExecutionEventReference | None,
    attempt_result: PaperExecutionAttemptResult,
    no_fill_reason_code: str | None,
    terminal_reason_code: str | None,
    risk_revalidation: PaperExecutionRiskRevalidation | None,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "execution_order_reference": execution_order_reference.to_dict(),
        "execution_version_before": execution_version_before,
        "execution_version_after": execution_version_after,
        "prior_order_state": prior_order_state.to_dict(),
        "pre_step_cursor": pre_step_cursor.to_dict(),
        "post_step_cursor": post_step_cursor.to_dict(),
        "consumed_event_reference": (
            None
            if consumed_event_reference is None
            else consumed_event_reference.to_dict()
        ),
        "attempt_result": attempt_result,
        "no_fill_reason_code": no_fill_reason_code,
        "terminal_reason_code": terminal_reason_code,
        "risk_revalidation": (
            None if risk_revalidation is None else risk_revalidation.to_dict()
        ),
    }


@dataclass(frozen=True, init=False)
class PaperExecutionAttempt:
    """One immutable committed execution-version transition."""

    schema_version: int
    attempt_id: str
    attempt_digest: str
    execution_order_reference: PaperExecutionOrderReference
    execution_version_before: int
    execution_version_after: int
    prior_order_state: PaperExecutionOrderState
    pre_step_cursor: ReplayCursor
    post_step_cursor: ReplayCursor
    consumed_event_reference: PaperExecutionEventReference | None
    attempt_result: PaperExecutionAttemptResult
    no_fill_reason_code: str | None
    terminal_reason_code: str | None
    risk_revalidation: PaperExecutionRiskRevalidation | None
    created_at: datetime

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            **_payload(
                schema_version=self.schema_version,
                execution_order_reference=self.execution_order_reference,
                execution_version_before=self.execution_version_before,
                execution_version_after=self.execution_version_after,
                prior_order_state=self.prior_order_state,
                pre_step_cursor=self.pre_step_cursor,
                post_step_cursor=self.post_step_cursor,
                consumed_event_reference=self.consumed_event_reference,
                attempt_result=self.attempt_result,
                no_fill_reason_code=self.no_fill_reason_code,
                terminal_reason_code=self.terminal_reason_code,
                risk_revalidation=self.risk_revalidation,
            ),
            "attempt_id": self.attempt_id,
            "attempt_digest": self.attempt_digest,
            "created_at": self.created_at.isoformat(),
        }


def _build_attempt(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    prior_order_state: PaperExecutionOrderState,
    pre_step_cursor: ReplayCursor,
    post_step_cursor: ReplayCursor,
    consumed_event_reference: PaperExecutionEventReference | None,
    attempt_result: PaperExecutionAttemptResult,
    no_fill_reason_code: str | None,
    terminal_reason_code: str | None,
    risk_revalidation: PaperExecutionRiskRevalidation | None,
    created_at: datetime,
) -> PaperExecutionAttempt:
    order_ref = _clone_order_reference(execution_order_reference)
    state = _clone_order_state(prior_order_state)
    pre_cursor = _clone_cursor(pre_step_cursor)
    post_cursor = _clone_cursor(post_step_cursor)
    event_ref = (
        None
        if consumed_event_reference is None
        else _clone_event_reference(consumed_event_reference)
    )
    risk = (
        None
        if risk_revalidation is None
        else _clone_risk_revalidation(risk_revalidation)
    )
    before = state.execution_version
    after = before + 1
    payload = _payload(
        schema_version=PAPER_EXECUTION_ATTEMPT_SCHEMA_VERSION,
        execution_order_reference=order_ref,
        execution_version_before=before,
        execution_version_after=after,
        prior_order_state=state,
        pre_step_cursor=pre_cursor,
        post_step_cursor=post_cursor,
        consumed_event_reference=event_ref,
        attempt_result=attempt_result,
        no_fill_reason_code=no_fill_reason_code,
        terminal_reason_code=terminal_reason_code,
        risk_revalidation=risk,
    )
    digest = canonical_digest(payload)
    result = object.__new__(PaperExecutionAttempt)
    values = {
        "schema_version": PAPER_EXECUTION_ATTEMPT_SCHEMA_VERSION,
        "attempt_id": f"pea_{digest}",
        "attempt_digest": digest,
        "execution_order_reference": order_ref,
        "execution_version_before": before,
        "execution_version_after": after,
        "prior_order_state": state,
        "pre_step_cursor": pre_cursor,
        "post_step_cursor": post_cursor,
        "consumed_event_reference": event_ref,
        "attempt_result": attempt_result,
        "no_fill_reason_code": no_fill_reason_code,
        "terminal_reason_code": terminal_reason_code,
        "risk_revalidation": risk,
        "created_at": created_at,
    }
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    return result


def _create_paper_execution_attempt(
    *,
    execution_order_reference: PaperExecutionOrderReference,
    prior_order_state: PaperExecutionOrderState,
    pre_step_cursor: ReplayCursor,
    post_step_cursor: ReplayCursor,
    consumed_event_reference: PaperExecutionEventReference | None,
    attempt_result: PaperExecutionAttemptResult,
    no_fill_reason_code: str | None,
    terminal_reason_code: str | None,
    risk_revalidation: PaperExecutionRiskRevalidation | None,
    created_at: datetime,
) -> PaperExecutionAttempt:
    """Internal creation seam used only after the step preflight succeeds."""
    if attempt_result not in SUPPORTED_PAPER_EXECUTION_ATTEMPT_RESULTS:
        raise ValueError("unsupported paper execution attempt result")
    if no_fill_reason_code is not None and (
        no_fill_reason_code not in SUPPORTED_PAPER_EXECUTION_NO_FILL_REASONS
    ):
        raise ValueError("unsupported no-fill reason code")
    if terminal_reason_code is not None and (
        terminal_reason_code not in SUPPORTED_PAPER_EXECUTION_TERMINAL_REASONS
    ):
        raise ValueError("unsupported terminal reason code")
    audit_time = normalize_utc_datetime(created_at, field_name="created_at")
    result = _build_attempt(
        execution_order_reference=execution_order_reference,
        prior_order_state=prior_order_state,
        pre_step_cursor=pre_step_cursor,
        post_step_cursor=post_step_cursor,
        consumed_event_reference=consumed_event_reference,
        attempt_result=attempt_result,
        no_fill_reason_code=no_fill_reason_code,
        terminal_reason_code=terminal_reason_code,
        risk_revalidation=risk_revalidation,
        created_at=audit_time,
    )
    return validate_paper_execution_attempt(result)


def _validate_semantics(value: PaperExecutionAttempt) -> None:
    event = value.consumed_event_reference
    risk = value.risk_revalidation
    if event is None:
        if (
            value.attempt_result != PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED
            or value.no_fill_reason_code is not None
            or risk is not None
            or value.terminal_reason_code
            not in {
                PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED,
                PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED,
            }
            or value.pre_step_cursor != value.post_step_cursor
        ):
            raise ValueError("boundary attempt semantics are invalid")
        return
    if not (
        value.post_step_cursor.position == value.pre_step_cursor.position + 1
        and event.replay_id == value.pre_step_cursor.replay_id
        and event.event_stream_digest == value.pre_step_cursor.event_stream_digest
        and event.pre_step_cursor_position == value.pre_step_cursor.position
        and event.post_step_cursor_position == value.post_step_cursor.position
        and event.post_step_last_event_id == value.post_step_cursor.last_event_id
        and event.post_step_current_event_time
        == value.post_step_cursor.current_event_time
        and event.post_step_replay_status == value.post_step_cursor.status
    ):
        raise ValueError("attempt event cursor transition is invalid")
    if value.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL:
        if (
            value.no_fill_reason_code
            not in SUPPORTED_PAPER_EXECUTION_NO_FILL_REASONS
            or risk is not None
            or value.terminal_reason_code
            not in {None, PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED}
        ):
            raise ValueError("no-fill attempt semantics are invalid")
    elif value.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL:
        if (
            value.no_fill_reason_code is not None
            or risk is None
            or risk.outcome != "allow"
            or value.terminal_reason_code
            not in {None, PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED}
        ):
            raise ValueError("fill attempt semantics are invalid")
    elif value.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED:
        if (
            value.no_fill_reason_code is not None
            or risk is None
            or risk.outcome != "reject"
            or value.terminal_reason_code
            != PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED
        ):
            raise ValueError("risk-rejected attempt semantics are invalid")
    else:
        raise ValueError("consumed event cannot be a boundary attempt")
    if (
        value.post_step_cursor.status == "completed"
        and value.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL
        and value.terminal_reason_code
        != PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
    ):
        raise ValueError("final consumed no-fill event must carry replay exhaustion")


def validate_paper_execution_attempt(value: object) -> PaperExecutionAttempt:
    if type(value) is not PaperExecutionAttempt:
        raise ValueError("attempt must be PaperExecutionAttempt")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version != PAPER_EXECUTION_ATTEMPT_SCHEMA_VERSION
            or value.attempt_result not in SUPPORTED_PAPER_EXECUTION_ATTEMPT_RESULTS
            or type(value.execution_version_before) is not int
            or type(value.execution_version_after) is not int
            or value.execution_version_after != value.execution_version_before + 1
        ):
            raise ValueError("attempt metadata is invalid")
        validate_paper_execution_order_reference(value.execution_order_reference)
        state = validate_paper_execution_order_state(value.prior_order_state)
        if (
            state.execution_order_reference != value.execution_order_reference
            or state.execution_version != value.execution_version_before
            or state.terminal
        ):
            raise ValueError("attempt prior state is invalid")
        _clone_cursor(value.pre_step_cursor)
        _clone_cursor(value.post_step_cursor)
        if value.consumed_event_reference is not None:
            validate_paper_execution_event_reference(
                value.consumed_event_reference
            )
        if value.risk_revalidation is not None:
            risk = validate_paper_execution_risk_revalidation(
                value.risk_revalidation
            )
            if (
                risk.execution_order_reference != value.execution_order_reference
                or risk.execution_version != value.execution_version_before
                or value.consumed_event_reference
                != risk.execution_price_evidence.execution_event_reference
            ):
                raise ValueError("attempt risk evidence is incompatible")
        _validate_semantics(value)
        audit_time = normalize_utc_datetime(value.created_at, field_name="created_at")
        if audit_time != value.created_at:
            raise ValueError("attempt created_at must be normalized")
        validate_digest(value.attempt_digest, field_name="attempt_digest")
        if value.attempt_id != f"pea_{value.attempt_digest}":
            raise ValueError("attempt ID does not match digest")
        expected = _build_attempt(
            execution_order_reference=value.execution_order_reference,
            prior_order_state=value.prior_order_state,
            pre_step_cursor=value.pre_step_cursor,
            post_step_cursor=value.post_step_cursor,
            consumed_event_reference=value.consumed_event_reference,
            attempt_result=value.attempt_result,
            no_fill_reason_code=value.no_fill_reason_code,
            terminal_reason_code=value.terminal_reason_code,
            risk_revalidation=value.risk_revalidation,
            created_at=value.created_at,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution attempt is invalid") from exc
    if expected != value or expected.to_dict() != value.to_dict():
        raise ValueError("paper execution attempt is invalid")
    return value


@dataclass(frozen=True, init=False)
class PaperExecutionAttemptReference:
    schema_version: int
    attempt_id: str
    attempt_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "attempt_id": self.attempt_id,
            "attempt_digest": self.attempt_digest,
        }


def create_paper_execution_attempt_reference(
    attempt: PaperExecutionAttempt,
) -> PaperExecutionAttemptReference:
    valid = validate_paper_execution_attempt(attempt)
    result = object.__new__(PaperExecutionAttemptReference)
    object.__setattr__(
        result,
        "schema_version",
        PAPER_EXECUTION_ATTEMPT_REFERENCE_SCHEMA_VERSION,
    )
    object.__setattr__(result, "attempt_id", valid.attempt_id)
    object.__setattr__(result, "attempt_digest", valid.attempt_digest)
    return result


def validate_paper_execution_attempt_reference(
    value: object,
) -> PaperExecutionAttemptReference:
    if type(value) is not PaperExecutionAttemptReference:
        raise ValueError("attempt reference must be PaperExecutionAttemptReference")
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != PAPER_EXECUTION_ATTEMPT_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported attempt reference schema_version")
        validate_digest(value.attempt_digest, field_name="attempt_digest")
        if value.attempt_id != f"pea_{value.attempt_digest}":
            raise ValueError("attempt reference ID does not match digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution attempt reference is invalid") from exc
    return value


def _clone_attempt_reference(
    value: PaperExecutionAttemptReference,
) -> PaperExecutionAttemptReference:
    validate_paper_execution_attempt_reference(value)
    result = object.__new__(PaperExecutionAttemptReference)
    object.__setattr__(result, "schema_version", value.schema_version)
    object.__setattr__(result, "attempt_id", value.attempt_id)
    object.__setattr__(result, "attempt_digest", value.attempt_digest)
    return result
