"""Typed durable M34 persistence records and fail-closed errors."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

from el_psy_quant.paper_execution import (
    ExecutionSettlementLink,
    PaperExecutionAttempt,
    PaperExecutionFill,
    PaperExecutionOrder,
    PaperExecutionOrderState,
    PaperExecutionStepResult,
)

PAPER_EXECUTION_PERSISTENCE_RECORD_SCHEMA_VERSION = 1
PAPER_EXECUTION_LIST_LIMIT_MAXIMUM = 200

COMMAND_NAMESPACE_CREATE_ORDER = "create_paper_execution_order"
COMMAND_NAMESPACE_STEP_ORDER = "step_paper_execution_order"
SUPPORTED_PAPER_EXECUTION_COMMAND_NAMESPACES = (
    COMMAND_NAMESPACE_CREATE_ORDER,
    COMMAND_NAMESPACE_STEP_ORDER,
)

RESULT_KIND_ORDER = "paper_execution_order"
RESULT_KIND_STEP = "paper_execution_step"
SUPPORTED_PAPER_EXECUTION_RESULT_KINDS = (RESULT_KIND_ORDER, RESULT_KIND_STEP)

PaperExecutionCommandNamespace = Literal[
    "create_paper_execution_order", "step_paper_execution_order"
]
PaperExecutionResultKind = Literal["paper_execution_order", "paper_execution_step"]


class PaperExecutionNotFoundError(Exception):
    """Requested durable execution authority does not exist."""


class PaperExecutionIdempotencyConflictError(Exception):
    """A scoped idempotency key owns a different command."""


class PaperExecutionStaleAuthorityError(Exception):
    """Expected M31, M32, M33, or M34 authority is stale."""


class PaperExecutionReconciliationRequiredError(Exception):
    """Current upstream projection or durable history is not reconcilable."""


class PaperExecutionConcurrencyConflictError(Exception):
    """A CAS or integrity loser did not commit execution authority."""


class PaperExecutionOperationConflictError(Exception):
    """The requested operation conflicts with valid current authority."""


class PaperExecutionCorruptAuthorityError(Exception):
    """Durable execution authority is incomplete or corrupt."""


class PaperExecutionStorageBusyError(Exception):
    """SQLite could not grant the one-winner transaction."""


class PaperExecutionStorageFailureError(Exception):
    """Durable storage failed without leaking implementation details."""


def bounded_string(value: object, field: str, maximum: int = 512) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{field} is invalid")
    return value


def digest(value: object, field: str) -> str:
    result = bounded_string(value, field, 64)
    if len(result) != 64 or any(c not in "0123456789abcdef" for c in result):
        raise ValueError(f"{field} is invalid")
    return result


def exact_utc(value: object, field: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field} is invalid")
    normalized = value.astimezone(timezone.utc)
    if normalized != value:
        raise ValueError(f"{field} is invalid")
    return normalized


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON is invalid")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON keys are invalid")
        result[key] = value
    return result


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def load_canonical_json(payload: object) -> object:
    if type(payload) is not str:
        raise PaperExecutionCorruptAuthorityError()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if canonical_json(value) != payload:
            raise ValueError("payload is not canonical")
        return value
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise PaperExecutionCorruptAuthorityError() from exc


@dataclass(frozen=True)
class PaperExecutionCommandReceipt:
    """Append-only command-to-result mapping, never execution authority."""

    namespace: PaperExecutionCommandNamespace
    command_idempotency_key: str
    command_digest: str
    command_actor: str
    result_kind: PaperExecutionResultKind
    execution_order_id: str
    execution_order_digest: str
    attempt_id: str | None
    attempt_digest: str | None
    fill_id: str | None
    fill_digest: str | None
    settlement_link_id: str | None
    settlement_link_evidence_digest: str | None
    account_event_id: str | None
    created_at: datetime
    record_schema_version: int = PAPER_EXECUTION_PERSISTENCE_RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.record_schema_version != 1:
            raise ValueError("unsupported execution receipt schema")
        if self.namespace not in SUPPORTED_PAPER_EXECUTION_COMMAND_NAMESPACES:
            raise ValueError("unsupported execution command namespace")
        bounded_string(self.command_idempotency_key, "command key", 128)
        digest(self.command_digest, "command digest")
        bounded_string(self.command_actor, "command actor", 256)
        if self.result_kind not in SUPPORTED_PAPER_EXECUTION_RESULT_KINDS:
            raise ValueError("unsupported execution result kind")
        bounded_string(self.execution_order_id, "execution order ID", 96)
        digest(self.execution_order_digest, "execution order digest")
        exact_utc(self.created_at, "created_at")
        optional_pairs = (
            (self.attempt_id, self.attempt_digest),
            (self.fill_id, self.fill_digest),
            (self.settlement_link_id, self.settlement_link_evidence_digest),
        )
        for identity, content_digest in optional_pairs:
            if (identity is None) is not (content_digest is None):
                raise ValueError("receipt result identity is incomplete")
            if identity is not None:
                bounded_string(identity, "receipt result ID", 96)
                digest(content_digest, "receipt result digest")
        if self.account_event_id is not None:
            bounded_string(self.account_event_id, "account event ID", 512)
        if self.result_kind == RESULT_KIND_ORDER:
            if self.namespace != COMMAND_NAMESPACE_CREATE_ORDER or any(
                value is not None
                for value in (
                    self.attempt_id,
                    self.fill_id,
                    self.settlement_link_id,
                    self.account_event_id,
                )
            ):
                raise ValueError("create receipt has invalid result references")
        elif self.namespace != COMMAND_NAMESPACE_STEP_ORDER or self.attempt_id is None:
            raise ValueError("step receipt requires one Attempt")
        if (self.fill_id is None) is not (self.settlement_link_id is None):
            raise ValueError("Fill and settlement receipt references must be paired")
        if (self.fill_id is None) is not (self.account_event_id is None):
            raise ValueError("Fill and account event receipt references must be paired")


@dataclass(frozen=True)
class PaperExecutionHistory:
    order: PaperExecutionOrder
    attempts: tuple[PaperExecutionAttempt, ...]
    fills: tuple[PaperExecutionFill, ...]
    settlement_links: tuple[ExecutionSettlementLink, ...]
    state: PaperExecutionOrderState


@dataclass(frozen=True)
class PaperExecutionStepCommit:
    step_result: PaperExecutionStepResult
    settlement_link: ExecutionSettlementLink | None
    account_event_id: str | None


T = TypeVar("T")


@dataclass(frozen=True)
class PaperExecutionStoredResult(Generic[T]):
    result: T
    replayed: bool

    def __post_init__(self) -> None:
        if type(self.replayed) is not bool:
            raise ValueError("replayed must be bool")


__all__ = [
    "COMMAND_NAMESPACE_CREATE_ORDER",
    "COMMAND_NAMESPACE_STEP_ORDER",
    "PAPER_EXECUTION_LIST_LIMIT_MAXIMUM",
    "PAPER_EXECUTION_PERSISTENCE_RECORD_SCHEMA_VERSION",
    "RESULT_KIND_ORDER",
    "RESULT_KIND_STEP",
    "PaperExecutionCommandReceipt",
    "PaperExecutionConcurrencyConflictError",
    "PaperExecutionCorruptAuthorityError",
    "PaperExecutionHistory",
    "PaperExecutionIdempotencyConflictError",
    "PaperExecutionNotFoundError",
    "PaperExecutionOperationConflictError",
    "PaperExecutionReconciliationRequiredError",
    "PaperExecutionStaleAuthorityError",
    "PaperExecutionStepCommit",
    "PaperExecutionStorageBusyError",
    "PaperExecutionStorageFailureError",
    "PaperExecutionStoredResult",
    "canonical_json",
    "load_canonical_json",
]
