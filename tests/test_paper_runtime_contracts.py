"""Focused deterministic contract evidence for Sprint 218 M35 values."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from el_psy_quant.application import PaperExecutionApplicationService
from el_psy_quant.paper_runtime import (
    PaperRuntimeCommandReceipt,
    create_paper_runtime,
    create_paper_runtime_command_receipt,
    create_paper_runtime_event,
    create_paper_runtime_work,
    reconstruct_paper_runtime_event_result,
    validate_paper_runtime,
    validate_paper_runtime_command_receipt,
    validate_paper_runtime_event,
    validate_paper_runtime_work,
)
from test_paper_execution_persistence import _fixture, _migrate

UTC = timezone.utc
AUDIT = datetime(2026, 8, 25, 1, tzinfo=UTC)


def _copy(value, **changes):
    result = object.__new__(type(value))
    for name in value.__dataclass_fields__:
        object.__setattr__(result, name, changes.get(name, getattr(value, name)))
    return result


def _event_payload(runtime):
    return {"resulting_runtime": runtime.to_dict()}


def _order(tmp_path, monkeypatch):
    path = tmp_path / "contracts.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, command = _fixture(path)
    order = (
        PaperExecutionApplicationService(session_factory=factory)
        .create_order(command)
        .result
    )
    return engine, order


def test_runtime_work_event_and_receipt_are_deterministic_and_strict(
    tmp_path, monkeypatch
):
    engine, order = _order(tmp_path, monkeypatch)
    try:
        runtime = create_paper_runtime(
            execution_order=order,
            logical_actor="paper-runtime",
            runtime_policy_id="durable-paper-runtime-v1",
            runtime_policy_version=1,
            created_at=AUDIT,
        )
        assert runtime == create_paper_runtime(
            execution_order=order,
            logical_actor="paper-runtime",
            runtime_policy_id="durable-paper-runtime-v1",
            runtime_policy_version=1,
            created_at=AUDIT,
        )
        assert (
            runtime.desired_state,
            runtime.observed_state,
            runtime.owner_id,
            runtime.fencing_token,
            runtime.row_version,
        ) == ("stopped", "ready", None, 0, 0)

        work = create_paper_runtime_work(
            runtime=runtime,
            expected_execution_version=0,
            created_at=AUDIT + timedelta(seconds=1),
        )
        assert work == create_paper_runtime_work(
            runtime=runtime,
            expected_execution_version=0,
            created_at=AUDIT + timedelta(seconds=1),
        )
        event = create_paper_runtime_event(
            runtime=runtime,
            event_sequence=0,
            event_type="runtime_created",
            resulting_runtime_version=0,
            payload=_event_payload(runtime),
            recorded_at=AUDIT,
        )
        assert event == create_paper_runtime_event(
            runtime=runtime,
            event_sequence=0,
            event_type="runtime_created",
            resulting_runtime_version=0,
            payload=_event_payload(runtime),
            recorded_at=AUDIT,
        )
        receipt = create_paper_runtime_command_receipt(
            namespace="create_paper_runtime",
            command_idempotency_key="create-runtime",
            command_digest="a" * 64,
            command_actor="founder",
            runtime=runtime,
            result_event=event,
            created_at=AUDIT,
        )
        assert (
            validate_paper_runtime_command_receipt(
                receipt, runtime=runtime, result_event=event
            )
            is receipt
        )
        assert validate_paper_runtime_work(work, runtime=runtime) is work
        assert validate_paper_runtime_event(event, runtime=runtime) is event
        assert reconstruct_paper_runtime_event_result(event, runtime=runtime) == runtime
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"desired_state": "paused"}, "paper runtime is invalid"),
        ({"observed_state": "unknown"}, "paper runtime is invalid"),
        ({"block_reason_code": "blocked"}, "paper runtime is invalid"),
        ({"owner_id": "worker"}, "paper runtime is invalid"),
        ({"created_at": datetime(2026, 8, 25, 1)}, "paper runtime is invalid"),
        ({"runtime_binding_digest": "A" * 64}, "paper runtime is invalid"),
    ),
)
def test_runtime_rejects_invalid_state_lease_reason_timestamp_and_digest(
    tmp_path, monkeypatch, changes, message
):
    engine, order = _order(tmp_path, monkeypatch)
    try:
        runtime = create_paper_runtime(
            execution_order=order,
            logical_actor="paper-runtime",
            runtime_policy_id="runtime-v1",
            runtime_policy_version=1,
            created_at=AUDIT,
        )
        with pytest.raises(ValueError, match=message):
            validate_paper_runtime(_copy(runtime, **changes))
    finally:
        engine.dispose()


def test_work_and_receipt_refuse_transient_actor_key_and_semantic_cross_wire(
    tmp_path, monkeypatch
):
    engine, order = _order(tmp_path, monkeypatch)
    try:
        runtime = create_paper_runtime(
            execution_order=order,
            logical_actor="stable-runtime",
            runtime_policy_id="runtime-v1",
            runtime_policy_version=1,
            created_at=AUDIT,
        )
        work = create_paper_runtime_work(
            runtime=runtime, expected_execution_version=0, created_at=AUDIT
        )
        for corrupt in (
            _copy(work, m34_step_actor="worker-123"),
            _copy(work, m34_step_idempotency_key="different"),
            _copy(work, expected_execution_version=-1),
        ):
            with pytest.raises(ValueError, match="paper runtime work is invalid"):
                validate_paper_runtime_work(corrupt, runtime=runtime)
        event = create_paper_runtime_event(
            runtime=runtime,
            event_sequence=0,
            event_type="runtime_created",
            resulting_runtime_version=0,
            payload=_event_payload(runtime),
            recorded_at=AUDIT,
        )
        with pytest.raises(ValueError, match="incompatible"):
            create_paper_runtime_command_receipt(
                namespace="start_paper_runtime",
                command_idempotency_key="start",
                command_digest="b" * 64,
                command_actor="founder",
                runtime=runtime,
                result_event=event,
                created_at=AUDIT,
            )
        with pytest.raises(ValueError):
            PaperRuntimeCommandReceipt(
                namespace="unknown",
                command_idempotency_key="x",
                command_digest="b" * 64,
                command_actor="founder",
                runtime_id=runtime.runtime_id,
                result_event_id=event.event_id,
                result_event_digest=event.event_digest,
                resulting_runtime_version=0,
                created_at=AUDIT,
            )
    finally:
        engine.dispose()


def test_event_vocabulary_has_exact_bounded_type_compatible_payloads(
    tmp_path, monkeypatch
):
    engine, order = _order(tmp_path, monkeypatch)
    try:
        runtime = create_paper_runtime(
            execution_order=order,
            logical_actor="stable-runtime",
            runtime_policy_id="runtime-v1",
            runtime_policy_version=1,
            created_at=AUDIT,
        )
        claimed = _copy(
            runtime,
            owner_id="worker-1",
            fencing_token=1,
            claimed_at=AUDIT + timedelta(seconds=1),
            heartbeat_at=AUDIT + timedelta(seconds=1),
            lease_expires_at=AUDIT + timedelta(minutes=1),
            row_version=1,
            updated_at=AUDIT + timedelta(seconds=1),
        )
        released = _copy(
            runtime,
            fencing_token=1,
            row_version=2,
            updated_at=AUDIT + timedelta(seconds=2),
        )
        completed = _copy(
            released,
            observed_state="completed",
            row_version=3,
            updated_at=AUDIT + timedelta(seconds=3),
        )
        blocked = _copy(
            released,
            observed_state="blocked",
            block_reason_code="upstream_corruption",
            row_version=3,
            updated_at=AUDIT + timedelta(seconds=3),
        )
        work = create_paper_runtime_work(
            runtime=runtime, expected_execution_version=0, created_at=AUDIT
        )
        work_evidence = {
            "work_id": work.work_id,
            "work_digest": work.work_digest,
            "expected_execution_version": work.expected_execution_version,
        }
        cases = (
            ("runtime_created", runtime, _event_payload(runtime)),
            ("start_requested", runtime, _event_payload(runtime)),
            ("stop_requested", runtime, _event_payload(runtime)),
            ("resume_requested", runtime, _event_payload(runtime)),
            ("recover_requested", runtime, _event_payload(runtime)),
            ("claim_acquired", claimed, _event_payload(claimed)),
            ("claim_released", released, _event_payload(released)),
            ("claim_taken_over", claimed, _event_payload(claimed)),
            (
                "work_created",
                runtime,
                {**_event_payload(runtime), "work": work_evidence},
            ),
            (
                "work_observed",
                runtime,
                {
                    **_event_payload(runtime),
                    "work": work_evidence,
                    "checkpoint": {
                        "checkpoint_id": "prc_" + "1" * 64,
                        "checkpoint_digest": "1" * 64,
                        "observed_execution_version": 1,
                    },
                },
            ),
            ("runtime_completed", completed, _event_payload(completed)),
            ("runtime_blocked", blocked, _event_payload(blocked)),
        )
        for sequence, (event_type, result, payload) in enumerate(cases):
            event = create_paper_runtime_event(
                runtime=result,
                event_sequence=sequence,
                event_type=event_type,
                resulting_runtime_version=result.row_version,
                payload=payload,
                recorded_at=AUDIT + timedelta(minutes=sequence),
            )
            assert reconstruct_paper_runtime_event_result(event, runtime=runtime) == result

        invalid = (
            ("runtime_created", runtime, {}),
            (
                "start_requested",
                runtime,
                {**_event_payload(runtime), "arbitrary": "not-allowed"},
            ),
            ("claim_acquired", runtime, _event_payload(runtime)),
            ("runtime_completed", runtime, _event_payload(runtime)),
            ("runtime_blocked", runtime, _event_payload(runtime)),
            ("work_created", runtime, _event_payload(runtime)),
        )
        for event_type, result, payload in invalid:
            with pytest.raises(ValueError):
                create_paper_runtime_event(
                    runtime=result,
                    event_sequence=0,
                    event_type=event_type,
                    resulting_runtime_version=result.row_version,
                    payload=payload,
                    recorded_at=AUDIT,
                )
    finally:
        engine.dispose()
