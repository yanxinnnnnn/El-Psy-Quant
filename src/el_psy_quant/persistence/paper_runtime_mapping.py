"""Canonical row/contract mapping for M35 durable runtime evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from el_psy_quant.paper_runtime import (
    PaperRuntime,
    PaperRuntimeCheckpoint,
    PaperRuntimeCommandReceipt,
    PaperRuntimeEvent,
    PaperRuntimeWork,
    validate_paper_runtime,
    validate_paper_runtime_checkpoint,
    validate_paper_runtime_command_receipt,
    validate_paper_runtime_event,
    validate_paper_runtime_work,
)
from el_psy_quant.paper_runtime._canonical import canonical_json, load_canonical_json
from el_psy_quant.persistence.paper_runtime_model import (
    PaperRuntimeCheckpointRow,
    PaperRuntimeCommandReceiptRow,
    PaperRuntimeEventRow,
    PaperRuntimeRow,
    PaperRuntimeWorkRow,
)
from el_psy_quant.persistence.paper_runtime_records import (
    PAPER_RUNTIME_PERSISTENCE_RECORD_SCHEMA_VERSION,
    PaperRuntimePersistenceCorruptionError,
)


def _sqlite_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("persisted timestamp is invalid")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _column_equal(actual: object, expected: object) -> bool:
    if type(actual) is datetime and type(expected) is datetime:
        return _sqlite_utc(actual) == _sqlite_utc(expected)
    return actual == expected


def _exact_object(payload_json: object, expected_fields: set[str]) -> dict[str, object]:
    value = load_canonical_json(payload_json)
    if type(value) is not dict or set(value) != expected_fields:
        raise ValueError("persisted payload fields are invalid")
    return value


def _datetime(value: object, field: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field} is invalid")
    return datetime.fromisoformat(value)


def runtime_row(runtime: PaperRuntime) -> PaperRuntimeRow:
    validate_paper_runtime(runtime)
    values = {
        name: value
        for name, value in runtime.__dict__.items()
        if name != "schema_version"
    }
    return PaperRuntimeRow(
        record_schema_version=PAPER_RUNTIME_PERSISTENCE_RECORD_SCHEMA_VERSION,
        runtime_schema_version=runtime.schema_version,
        payload_json=canonical_json(runtime.to_dict()),
        **values,
    )


def runtime_from_row(row: PaperRuntimeRow) -> PaperRuntime:
    try:
        if row.record_schema_version != 1 or row.runtime_schema_version != 1:
            raise ValueError("unsupported runtime record schema")
        payload = _exact_object(
            row.payload_json, set(PaperRuntime.__dataclass_fields__)
        )
        for field in ("created_at", "updated_at"):
            payload[field] = _datetime(payload[field], field)
        for field in ("claimed_at", "heartbeat_at", "lease_expires_at"):
            if payload[field] is not None:
                payload[field] = _datetime(payload[field], field)
        runtime = object.__new__(PaperRuntime)
        for name in PaperRuntime.__dataclass_fields__:
            object.__setattr__(runtime, name, payload[name])
        validate_paper_runtime(runtime)
        expected = runtime_row(runtime)
        for name in PaperRuntimeRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("runtime payload/index mismatch")
        return runtime
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperRuntimePersistenceCorruptionError() from exc


def work_row(work: PaperRuntimeWork) -> PaperRuntimeWorkRow:
    values = {
        name: value for name, value in work.__dict__.items() if name != "schema_version"
    }
    return PaperRuntimeWorkRow(
        record_schema_version=1,
        work_schema_version=work.schema_version,
        payload_json=canonical_json(work.to_dict()),
        **values,
    )


def work_from_row(
    row: PaperRuntimeWorkRow, *, runtime: PaperRuntime
) -> PaperRuntimeWork:
    try:
        if row.record_schema_version != 1 or row.work_schema_version != 1:
            raise ValueError("unsupported work record schema")
        payload = _exact_object(
            row.payload_json, set(PaperRuntimeWork.__dataclass_fields__)
        )
        payload["created_at"] = _datetime(payload["created_at"], "created_at")
        work = object.__new__(PaperRuntimeWork)
        for name in PaperRuntimeWork.__dataclass_fields__:
            object.__setattr__(work, name, payload[name])
        validate_paper_runtime_work(work, runtime=runtime)
        expected = work_row(work)
        for name in PaperRuntimeWorkRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("work payload/index mismatch")
        return work
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperRuntimePersistenceCorruptionError() from exc


def checkpoint_row(checkpoint: PaperRuntimeCheckpoint) -> PaperRuntimeCheckpointRow:
    values = {
        name: value
        for name, value in checkpoint.__dict__.items()
        if name != "schema_version"
    }
    return PaperRuntimeCheckpointRow(
        record_schema_version=1,
        checkpoint_schema_version=checkpoint.schema_version,
        payload_json=canonical_json(checkpoint.to_dict()),
        **values,
    )


def checkpoint_from_row(
    row: PaperRuntimeCheckpointRow, *, runtime: PaperRuntime, work: PaperRuntimeWork
) -> PaperRuntimeCheckpoint:
    try:
        if row.record_schema_version != 1 or row.checkpoint_schema_version != 1:
            raise ValueError("unsupported checkpoint record schema")
        payload = _exact_object(
            row.payload_json, set(PaperRuntimeCheckpoint.__dataclass_fields__)
        )
        payload["observed_at"] = _datetime(payload["observed_at"], "observed_at")
        checkpoint = object.__new__(PaperRuntimeCheckpoint)
        for name in PaperRuntimeCheckpoint.__dataclass_fields__:
            object.__setattr__(checkpoint, name, payload[name])
        validate_paper_runtime_checkpoint(checkpoint, runtime=runtime, work=work)
        expected = checkpoint_row(checkpoint)
        for name in PaperRuntimeCheckpointRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("checkpoint payload/index mismatch")
        return checkpoint
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperRuntimePersistenceCorruptionError() from exc


def event_row(event: PaperRuntimeEvent) -> PaperRuntimeEventRow:
    values = {
        name: value
        for name, value in event.__dict__.items()
        if name != "schema_version"
    }
    return PaperRuntimeEventRow(
        record_schema_version=1,
        event_schema_version=event.schema_version,
        **values,
    )


def event_from_row(
    row: PaperRuntimeEventRow, *, runtime: PaperRuntime
) -> PaperRuntimeEvent:
    try:
        if row.record_schema_version != 1 or row.event_schema_version != 1:
            raise ValueError("unsupported event record schema")
        load_canonical_json(row.payload_json)
        event = object.__new__(PaperRuntimeEvent)
        for name in PaperRuntimeEvent.__dataclass_fields__:
            value = (
                row.event_schema_version
                if name == "schema_version"
                else getattr(row, name)
            )
            if name == "recorded_at":
                value = _sqlite_utc(value)
            object.__setattr__(event, name, value)
        validate_paper_runtime_event(event, runtime=runtime)
        expected = event_row(event)
        for name in PaperRuntimeEventRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("event row mismatch")
        return event
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperRuntimePersistenceCorruptionError() from exc


def receipt_row(receipt: PaperRuntimeCommandReceipt) -> PaperRuntimeCommandReceiptRow:
    values = {
        name: value
        for name, value in receipt.__dict__.items()
        if name != "schema_version"
    }
    return PaperRuntimeCommandReceiptRow(
        record_schema_version=1,
        receipt_schema_version=receipt.schema_version,
        **values,
    )


def receipt_from_row(
    row: PaperRuntimeCommandReceiptRow,
    *,
    runtime: PaperRuntime,
    result_event: PaperRuntimeEvent,
) -> PaperRuntimeCommandReceipt:
    try:
        values = {
            name: (
                row.receipt_schema_version
                if name == "schema_version"
                else getattr(row, name)
            )
            for name in PaperRuntimeCommandReceipt.__dataclass_fields__
        }
        values["created_at"] = _sqlite_utc(values["created_at"])
        receipt = PaperRuntimeCommandReceipt(**values)
        validate_paper_runtime_command_receipt(
            receipt, runtime=runtime, result_event=result_event
        )
        expected = receipt_row(receipt)
        for name in PaperRuntimeCommandReceiptRow.__table__.columns.keys():
            if not _column_equal(getattr(row, name), getattr(expected, name)):
                raise ValueError("receipt row mismatch")
        return receipt
    except (AttributeError, TypeError, ValueError) as exc:
        raise PaperRuntimePersistenceCorruptionError() from exc


__all__ = [
    "checkpoint_from_row",
    "checkpoint_row",
    "event_from_row",
    "event_row",
    "receipt_from_row",
    "receipt_row",
    "runtime_from_row",
    "runtime_row",
    "work_from_row",
    "work_row",
]
