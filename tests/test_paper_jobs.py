"""Tests for the strict request codec and immutable paper-job product model."""

import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import el_psy_quant.paper.run_execution as paper_execution
from el_psy_quant.paper import (
    PaperRunRequest,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_run_request,
)
from el_psy_quant.persistence import (
    PaperJobRecord,
    PreparedPaperRunRequest,
    create_queued_paper_job_record,
    deserialize_paper_run_request,
    prepare_paper_run_request_for_persistence,
    serialize_paper_run_request,
    transition_paper_job_record,
)

JOB_ID = "12345678-1234-4abc-8def-1234567890ab"
SUBMITTED = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


def _request(*, run_id: str = "run-1") -> PaperRunRequest:
    return create_paper_run_request(
        run_id=run_id,
        created_timestamp="2026-07-13T11:59:00Z",
        starting_account_state=create_paper_account_state(
            timestamp="2026-07-13T11:50:00Z",
            starting_cash=10_000,
            current_cash=10_000,
            positions={"MSFT": 1, "aapl": 2},
        ),
        ending_account_state=create_paper_account_state(
            timestamp="2026-07-13T11:58:00Z",
            starting_cash=10_000,
            current_cash=9_000,
            positions={"MSFT": 0.5, "aapl": 12},
        ),
        orders=(
            create_paper_order_record(
                order_id="order-2",
                timestamp="2026-07-13T11:52:00Z",
                symbol="MSFT",
                side="sell",
                quantity=0.5,
                status="filled",
            ),
            create_paper_order_record(
                order_id="order-1",
                timestamp="2026-07-13T11:51:00Z",
                symbol="AAPL",
                side="buy",
                quantity=10,
                status="filled",
            ),
        ),
        fills=(
            create_paper_fill(
                timestamp="2026-07-13T11:54:00Z",
                symbol="MSFT",
                side="sell",
                quantity=0.5,
                price=200,
            ),
            create_paper_fill(
                timestamp="2026-07-13T11:53:00Z",
                symbol="AAPL",
                side="buy",
                quantity=10,
                price=100,
                order_id="order-1",
            ),
        ),
    )


def test_request_codec_is_canonical_deterministic_and_round_trips() -> None:
    request = _request()

    first = serialize_paper_run_request(request)
    second = serialize_paper_run_request(request)
    restored = deserialize_paper_run_request(first)

    assert first == second
    assert first == json.dumps(
        request.to_dict(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert restored.to_dict() == request.to_dict()
    assert tuple(order.order_id for order in restored.orders) == (
        "order-2",
        "order-1",
    )
    assert tuple(fill.symbol for fill in restored.fills) == ("MSFT", "AAPL")


def test_codec_requires_domain_request_and_string_snapshot() -> None:
    with pytest.raises(ValueError, match="PaperRunRequest"):
        serialize_paper_run_request({})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="snapshot is invalid"):
        deserialize_paper_run_request({})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.pop("run_id"),
        lambda payload: payload.__setitem__("unexpected", True),
        lambda payload: payload.__setitem__("schema_version", 2),
        lambda payload: payload.__setitem__("schema_version", True),
        lambda payload: payload["starting_account_state"].__setitem__(
            "unexpected", True
        ),
        lambda payload: payload["orders"][0].pop("side"),
        lambda payload: payload["fills"][0].__setitem__("unexpected", True),
        lambda payload: payload["starting_account_state"].__setitem__(
            "current_cash", True
        ),
        lambda payload: payload["orders"][0].__setitem__("quantity", -1),
        lambda payload: payload["fills"][0].__setitem__("price", -1),
    ),
)
def test_codec_rejects_missing_extra_schema_and_invalid_nested_values(
    mutate,
) -> None:
    payload = _request().to_dict()
    mutate(payload)

    with pytest.raises(ValueError, match="snapshot is invalid"):
        deserialize_paper_run_request(json.dumps(payload))


@pytest.mark.parametrize(
    "payload",
    (
        "not-json",
        "[]",
        '{"schema_version":1,"schema_version":1}',
        serialize_paper_run_request(_request()).replace("10000.0", "NaN", 1),
        serialize_paper_run_request(_request()).replace("10000.0", "Infinity", 1),
    ),
)
def test_codec_rejects_malformed_duplicates_nan_and_infinity(payload: str) -> None:
    with pytest.raises(ValueError, match="snapshot is invalid"):
        deserialize_paper_run_request(payload)


def test_codec_performs_no_execution_or_filesystem_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("codec side effect")

    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(paper_execution, "run_paper_trading_request", forbidden)
    payload = serialize_paper_run_request(_request())
    restored = deserialize_paper_run_request(payload)

    assert restored.run_id == "run-1"
    assert list(tmp_path.iterdir()) == []


def test_prepared_persistence_input_is_codec_created_bound_and_immutable() -> None:
    request = _request()
    prepared = prepare_paper_run_request_for_persistence(request)

    assert prepared.request is request
    assert serialize_paper_run_request(request) not in repr(prepared)
    with pytest.raises(FrozenInstanceError):
        prepared.request = _request(run_id="other")  # type: ignore[misc]
    with pytest.raises(TypeError, match="must be created through"):
        PreparedPaperRunRequest()


def test_queued_factory_creates_exact_frozen_product_contract() -> None:
    request = _request()
    job = create_queued_paper_job_record(
        job_id=JOB_ID,
        request=request,
        submitted_timestamp=SUBMITTED,
    )

    assert job == PaperJobRecord(
        record_schema_version=1,
        job_id=JOB_ID,
        run_id="run-1",
        status="queued",
        request=request,
        submitted_timestamp=SUBMITTED,
        updated_timestamp=SUBMITTED,
    )
    assert tuple(field.name for field in fields(job)) == (
        "record_schema_version",
        "job_id",
        "run_id",
        "status",
        "request",
        "submitted_timestamp",
        "updated_timestamp",
    )
    with pytest.raises(FrozenInstanceError):
        job.status = "running"  # type: ignore[misc]
    forbidden = {
        "artifact",
        "result",
        "result_reference",
        "error",
        "retry",
        "attempt",
        "idempotency_key",
        "worker",
        "lease",
        "lifecycle_state",
        "broker",
        "request_payload",
        "prepared_request",
    }
    assert all(not hasattr(job, field) for field in forbidden)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("record_schema_version", 2),
        ("job_id", "1234567812344abc8def1234567890ab"),
        ("job_id", "12345678-1234-4ABC-8DEF-1234567890AB"),
        ("run_id", "other-run"),
        ("status", "pending"),
        ("submitted_timestamp", datetime(2026, 7, 13, 12, 0)),
        (
            "submitted_timestamp",
            datetime(
                2026,
                7,
                13,
                12,
                0,
                tzinfo=timezone(timedelta(hours=1)),
            ),
        ),
        ("updated_timestamp", SUBMITTED - timedelta(seconds=1)),
    ),
)
def test_product_record_rejects_invalid_identity_state_and_time(
    field: str,
    value: object,
) -> None:
    job = create_queued_paper_job_record(
        job_id=JOB_ID,
        request=_request(),
        submitted_timestamp=SUBMITTED,
    )

    with pytest.raises(ValueError):
        replace(job, **{field: value})


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        ("queued", "running"),
        ("queued", "canceled"),
        ("running", "succeeded"),
        ("running", "failed"),
        ("running", "queued"),
        ("failed", "queued"),
    ),
)
def test_transition_contract_allows_only_approved_immutable_changes(
    current_status: str,
    target_status: str,
) -> None:
    original = replace(
        create_queued_paper_job_record(
            job_id=JOB_ID,
            request=_request(),
            submitted_timestamp=SUBMITTED,
        ),
        status=current_status,
    )
    updated = SUBMITTED + timedelta(seconds=1)

    transitioned = transition_paper_job_record(
        job=original,
        target_status=target_status,  # type: ignore[arg-type]
        updated_timestamp=updated,
    )

    assert transitioned is not original
    assert transitioned.status == target_status
    assert transitioned.updated_timestamp == updated
    assert replace(
        transitioned,
        status=original.status,
        updated_timestamp=original.updated_timestamp,
    ) == original
    with pytest.raises(FrozenInstanceError):
        transitioned.status = "queued"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    tuple(
        (current, target)
        for current in ("queued", "running", "succeeded", "failed", "canceled")
        for target in ("queued", "running", "succeeded", "failed", "canceled")
        if (current, target)
        not in {
            ("queued", "running"),
            ("queued", "canceled"),
            ("running", "succeeded"),
            ("running", "failed"),
            ("running", "queued"),
            ("failed", "queued"),
        }
    ),
)
def test_transition_contract_rejects_every_unapproved_transition(
    current_status: str,
    target_status: str,
) -> None:
    job = replace(
        create_queued_paper_job_record(
            job_id=JOB_ID,
            request=_request(),
            submitted_timestamp=SUBMITTED,
        ),
        status=current_status,
    )

    with pytest.raises(ValueError, match="transition is not allowed"):
        transition_paper_job_record(
            job=job,
            target_status=target_status,  # type: ignore[arg-type]
            updated_timestamp=SUBMITTED + timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "updated_timestamp",
    (
        datetime(2026, 7, 13, 12, 0, 1),
        datetime(
            2026,
            7,
            13,
            13,
            0,
            1,
            tzinfo=timezone(timedelta(hours=1)),
        ),
        SUBMITTED - timedelta(microseconds=1),
    ),
)
def test_transition_contract_rejects_naive_non_utc_and_reversed_time(
    updated_timestamp: datetime,
) -> None:
    job = create_queued_paper_job_record(
        job_id=JOB_ID,
        request=_request(),
        submitted_timestamp=SUBMITTED,
    )

    with pytest.raises(ValueError, match="updated_timestamp"):
        transition_paper_job_record(
            job=job,
            target_status="running",
            updated_timestamp=updated_timestamp,
        )
