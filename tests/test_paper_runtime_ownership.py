"""Focused Sprint 219 ownership, fencing, CAS, and idempotency evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import text

from el_psy_quant.application import (
    PaperRuntimeClaimMismatchError,
    PaperRuntimeControlIdempotencyConflictError,
    PaperRuntimeLeaseExpiredError,
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeOwnershipService,
)
from el_psy_quant.paper_runtime import (
    PaperRuntime,
    create_paper_runtime_command_receipt,
    create_paper_runtime_event,
    digest_paper_runtime_control_command,
)
from el_psy_quant.persistence import (
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimePersistenceCorruptionError,
    PaperRuntimeStorageBusyError,
    SqlAlchemyPaperRuntimeRepository,
)
from el_psy_quant.persistence.paper_runtime_mapping import runtime_row
from test_paper_runtime_persistence import AUDIT, _authorities

LEASE = timedelta(seconds=30)


@dataclass
class _Clock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


def _copy(runtime: PaperRuntime, **changes: object) -> PaperRuntime:
    result = object.__new__(PaperRuntime)
    for name in PaperRuntime.__dataclass_fields__:
        object.__setattr__(result, name, changes.get(name, getattr(runtime, name)))
    return result


def _stored_runtime(path, monkeypatch):
    engine, factory, _order, _commit, runtime, _work, event, receipt = _authorities(
        path, monkeypatch, step=False
    )
    with factory.begin() as session:
        repository = SqlAlchemyPaperRuntimeRepository(session=session)
        repository.append_runtime(runtime=runtime)
        repository.append_event(event=event)
        repository.append_receipt(receipt=receipt)
    return engine, factory, runtime, event, receipt


def _service(factory, clock: _Clock) -> PaperRuntimeOwnershipService:
    return PaperRuntimeOwnershipService(
        session_factory=factory,
        lease_duration=LEASE,
        clock=clock,
    )


def _read(factory, runtime_id: str):
    with factory() as session:
        repository = SqlAlchemyPaperRuntimeRepository(session=session)
        return (
            repository.get_runtime(runtime_id=runtime_id),
            repository.list_events(runtime_id=runtime_id),
            repository.list_receipts(runtime_id=runtime_id),
        )


def test_exact_cas_updates_payload_and_indexes_and_remains_caller_owned(
    tmp_path, monkeypatch
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "cas.sqlite3", monkeypatch
    )
    replacement = _copy(
        runtime,
        desired_state="running",
        observed_state="running",
        row_version=1,
        updated_at=AUDIT + timedelta(seconds=1),
    )
    try:
        session = factory()
        repository = SqlAlchemyPaperRuntimeRepository(session=session)
        assert (
            repository.compare_and_swap_runtime(
                expected_runtime=runtime, replacement_runtime=replacement
            )
            == replacement
        )
        row = session.execute(
            text(
                "SELECT desired_state, observed_state, row_version, payload_json "
                "FROM paper_runtimes WHERE runtime_id=:runtime_id"
            ),
            {"runtime_id": runtime.runtime_id},
        ).one()
        assert row.desired_state == "running"
        assert row.observed_state == "running"
        assert row.row_version == 1
        assert row.payload_json == runtime_row(replacement).payload_json
        session.rollback()
        session.close()

        current, _events, _receipts = _read(factory, runtime.runtime_id)
        assert current == runtime
        with factory.begin() as session:
            SqlAlchemyPaperRuntimeRepository(session=session).compare_and_swap_runtime(
                expected_runtime=runtime, replacement_runtime=replacement
            )

        stale_expected = _copy(runtime, desired_state="running")
        stale_replacement = _copy(
            replacement,
            desired_state="stopped",
            observed_state="stopped",
            row_version=1,
        )
        with pytest.raises(PaperRuntimeConcurrencyConflictError):
            with factory.begin() as session:
                SqlAlchemyPaperRuntimeRepository(
                    session=session
                ).compare_and_swap_runtime(
                    expected_runtime=stale_expected,
                    replacement_runtime=stale_replacement,
                )
        with pytest.raises(ValueError):
            with factory.begin() as session:
                SqlAlchemyPaperRuntimeRepository(
                    session=session
                ).compare_and_swap_runtime(
                    expected_runtime=replacement,
                    replacement_runtime=_copy(
                        replacement,
                        account_id="forged-account",
                        row_version=2,
                        updated_at=AUDIT + timedelta(seconds=2),
                    ),
                )
    finally:
        engine.dispose()


def test_cas_rejects_fencing_token_regression_and_allows_same_fence(
    tmp_path, monkeypatch
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "cas-fence.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        claimed = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        regressed = _copy(
            claimed,
            fencing_token=claimed.fencing_token - 1,
            row_version=claimed.row_version + 1,
            updated_at=clock.value + timedelta(seconds=1),
        )
        with pytest.raises(ValueError, match="fencing token regresses"):
            with factory.begin() as session:
                SqlAlchemyPaperRuntimeRepository(
                    session=session
                ).compare_and_swap_runtime(
                    expected_runtime=claimed,
                    replacement_runtime=regressed,
                )
        assert _read(factory, runtime.runtime_id)[0] == claimed

        same_fence = _copy(
            claimed,
            desired_state="running",
            observed_state="running",
            row_version=claimed.row_version + 1,
            updated_at=clock.value + timedelta(seconds=1),
        )
        with factory.begin() as session:
            stored = SqlAlchemyPaperRuntimeRepository(
                session=session
            ).compare_and_swap_runtime(
                expected_runtime=claimed,
                replacement_runtime=same_fence,
            )
        assert stored == same_fence
        assert stored.fencing_token == claimed.fencing_token
        assert _read(factory, runtime.runtime_id)[0] == same_fence
    finally:
        engine.dispose()


@pytest.mark.parametrize("operation", ("claim", "renew", "release"))
def test_mutating_ownership_samples_lease_time_after_write_acquisition(
    tmp_path, monkeypatch, operation
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / f"post-lock-{operation}.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        claimed = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        clock.value = claimed.lease_expires_at - timedelta(microseconds=1)
        observations: list[datetime] = []
        original_clock = service._clock
        original_write = service._write

        def observed_clock() -> datetime:
            value = original_clock()
            observations.append(value)
            return value

        @contextmanager
        def post_acquisition_write():
            with original_write() as session:
                clock.value = claimed.lease_expires_at
                yield session

        monkeypatch.setattr(service, "_clock", observed_clock)
        monkeypatch.setattr(service, "_write", post_acquisition_write)

        if operation == "claim":
            takeover = service.claim_runtime(
                runtime_id=runtime.runtime_id, owner_id="worker-b"
            ).runtime
            assert takeover.owner_id == "worker-b"
            assert takeover.fencing_token == claimed.fencing_token + 1
            assert takeover.claimed_at == claimed.lease_expires_at
            assert takeover.heartbeat_at == claimed.lease_expires_at
            assert takeover.updated_at == claimed.lease_expires_at
        else:
            command = (
                service.renew_runtime_claim
                if operation == "renew"
                else service.release_runtime_claim
            )
            with pytest.raises(PaperRuntimeLeaseExpiredError):
                command(
                    runtime_id=runtime.runtime_id,
                    owner_id="worker-a",
                    fencing_token=claimed.fencing_token,
                )
            assert _read(factory, runtime.runtime_id)[0] == claimed
        assert observations == [claimed.lease_expires_at]
    finally:
        engine.dispose()


def test_first_claim_convergence_and_competing_owner_rejection(tmp_path, monkeypatch):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "claim.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        claimed = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        )
        assert claimed.converged is False
        assert claimed.event is not None
        assert claimed.event.event_type == "claim_acquired"
        assert claimed.event.event_sequence == 1
        assert claimed.event.resulting_runtime_version == 1
        assert claimed.runtime.owner_id == "worker-a"
        assert claimed.runtime.fencing_token == 1
        assert claimed.runtime.row_version == 1
        assert claimed.runtime.claimed_at == clock.value
        assert claimed.runtime.heartbeat_at == clock.value
        assert claimed.runtime.lease_expires_at == clock.value + LEASE

        clock.value += timedelta(seconds=5)
        converged = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        )
        assert converged.converged is True
        assert converged.event is None
        assert converged.runtime == claimed.runtime
        with pytest.raises(PaperRuntimeOwnershipBusyError):
            service.claim_runtime(runtime_id=runtime.runtime_id, owner_id="worker-b")
        current, events, _receipts = _read(factory, runtime.runtime_id)
        assert current == claimed.runtime
        assert tuple(event.event_type for event in events) == (
            "runtime_created",
            "claim_acquired",
        )
    finally:
        engine.dispose()


def test_expiry_boundary_takeover_fences_old_worker_and_owner_reuse(
    tmp_path, monkeypatch
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "takeover.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        first = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        clock.value = first.lease_expires_at
        takeover = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-b"
        )
        assert takeover.event is not None
        assert takeover.event.event_type == "claim_taken_over"
        assert takeover.runtime.fencing_token == 2
        assert takeover.runtime.row_version == 2
        assert takeover.runtime.claimed_at == clock.value

        for operation in (
            service.renew_runtime_claim,
            service.release_runtime_claim,
            service.assert_active_runtime_claim,
        ):
            with pytest.raises(PaperRuntimeClaimMismatchError):
                operation(
                    runtime_id=runtime.runtime_id,
                    owner_id="worker-a",
                    fencing_token=first.fencing_token,
                )

        clock.value += timedelta(seconds=1)
        released = service.release_runtime_claim(
            runtime_id=runtime.runtime_id,
            owner_id="worker-b",
            fencing_token=takeover.runtime.fencing_token,
        ).runtime
        assert released.owner_id is None
        assert released.fencing_token == 2
        reused = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        assert reused.fencing_token == 3
        with pytest.raises(PaperRuntimeClaimMismatchError):
            service.assert_active_runtime_claim(
                runtime_id=runtime.runtime_id,
                owner_id="worker-a",
                fencing_token=first.fencing_token,
            )
    finally:
        engine.dispose()


def test_heartbeat_requires_exact_active_claim_and_creates_no_event(
    tmp_path, monkeypatch
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "heartbeat.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        claimed = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        clock.value += timedelta(seconds=10)
        renewed = service.renew_runtime_claim(
            runtime_id=runtime.runtime_id,
            owner_id="worker-a",
            fencing_token=claimed.fencing_token,
        )
        assert renewed.claimed_at == claimed.claimed_at
        assert renewed.fencing_token == claimed.fencing_token
        assert renewed.heartbeat_at == clock.value
        assert renewed.lease_expires_at == clock.value + LEASE
        assert renewed.row_version == claimed.row_version + 1
        _current, events, _receipts = _read(factory, runtime.runtime_id)
        assert len(events) == 2

        for owner, fence in (("worker-b", 1), ("worker-a", 0)):
            with pytest.raises(PaperRuntimeClaimMismatchError):
                service.renew_runtime_claim(
                    runtime_id=runtime.runtime_id,
                    owner_id=owner,
                    fencing_token=fence,
                )
        clock.value = renewed.lease_expires_at
        for operation in (
            service.renew_runtime_claim,
            service.release_runtime_claim,
            service.assert_active_runtime_claim,
        ):
            with pytest.raises(PaperRuntimeLeaseExpiredError):
                operation(
                    runtime_id=runtime.runtime_id,
                    owner_id="worker-a",
                    fencing_token=renewed.fencing_token,
                )
        current, events, _receipts = _read(factory, runtime.runtime_id)
        assert current == renewed
        assert len(events) == 2
    finally:
        engine.dispose()


def test_release_and_guard_preserve_fence_and_do_not_mutate_on_failure(
    tmp_path, monkeypatch
):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "release.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)
    try:
        claimed = service.claim_runtime(
            runtime_id=runtime.runtime_id, owner_id="worker-a"
        ).runtime
        guarded = service.assert_active_runtime_claim(
            runtime_id=runtime.runtime_id,
            owner_id="worker-a",
            fencing_token=claimed.fencing_token,
        )
        assert guarded == claimed
        assert _read(factory, runtime.runtime_id)[0] == claimed

        with pytest.raises(PaperRuntimeClaimMismatchError):
            service.release_runtime_claim(
                runtime_id=runtime.runtime_id,
                owner_id="worker-a",
                fencing_token=claimed.fencing_token + 1,
            )
        assert _read(factory, runtime.runtime_id)[0] == claimed

        clock.value += timedelta(seconds=1)
        released = service.release_runtime_claim(
            runtime_id=runtime.runtime_id,
            owner_id="worker-a",
            fencing_token=claimed.fencing_token,
        )
        assert released.event is not None
        assert released.event.event_type == "claim_released"
        assert released.runtime.owner_id is None
        assert released.runtime.claimed_at is None
        assert released.runtime.heartbeat_at is None
        assert released.runtime.lease_expires_at is None
        assert released.runtime.fencing_token == claimed.fencing_token
        assert released.runtime.row_version == claimed.row_version + 1
        with pytest.raises(PaperRuntimeClaimMismatchError):
            service.release_runtime_claim(
                runtime_id=runtime.runtime_id,
                owner_id="worker-a",
                fencing_token=claimed.fencing_token,
            )
        _current, events, _receipts = _read(factory, runtime.runtime_id)
        assert tuple(event.event_type for event in events) == (
            "runtime_created",
            "claim_acquired",
            "claim_released",
        )
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT COUNT(*) FROM paper_execution_attempts"))
                == 0
            )
            assert (
                connection.scalar(text("SELECT COUNT(*) FROM paper_execution_fills"))
                == 0
            )
            assert (
                connection.scalar(
                    text("SELECT COUNT(*) FROM paper_execution_settlement_links")
                )
                == 0
            )
    finally:
        engine.dispose()


def test_claim_event_failure_rolls_back_runtime_mutation(tmp_path, monkeypatch):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "rollback.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    service = _service(factory, clock)

    def fail_event(self, *, event):
        del self, event
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(SqlAlchemyPaperRuntimeRepository, "append_event", fail_event)
    try:
        with pytest.raises(RuntimeError, match="injected event failure"):
            service.claim_runtime(runtime_id=runtime.runtime_id, owner_id="worker-a")
        current, events, _receipts = _read(factory, runtime.runtime_id)
        assert current == runtime
        assert tuple(event.event_type for event in events) == ("runtime_created",)
    finally:
        engine.dispose()


def test_concurrent_claim_has_one_winner_one_fence_and_one_event(tmp_path, monkeypatch):
    engine, factory, runtime, _event, _receipt = _stored_runtime(
        tmp_path / "concurrent.sqlite3", monkeypatch
    )
    clock = _Clock(AUDIT + timedelta(minutes=1))
    barrier = Barrier(2)

    def claim(owner: str):
        barrier.wait(timeout=10)
        try:
            result = _service(factory, clock).claim_runtime(
                runtime_id=runtime.runtime_id, owner_id=owner
            )
            return "won", result.runtime.owner_id
        except (PaperRuntimeOwnershipBusyError, PaperRuntimeStorageBusyError):
            return "lost", owner

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(
                pool.submit(claim, owner) for owner in ("worker-a", "worker-b")
            )
            outcomes = tuple(future.result(timeout=15) for future in futures)
        assert sorted(outcome for outcome, _owner in outcomes) == ["lost", "won"]
        current, events, _receipts = _read(factory, runtime.runtime_id)
        assert current is not None
        assert current.fencing_token == 1
        assert current.row_version == 1
        assert tuple(event.event_type for event in events).count("claim_acquired") == 1
        assert len(events) == 2
    finally:
        engine.dispose()


def test_control_digest_and_historical_key_or_digest_replay(tmp_path, monkeypatch):
    engine, factory, runtime, event, receipt = _stored_runtime(
        tmp_path / "control.sqlite3", monkeypatch
    )
    target = {
        "runtime_id": runtime.runtime_id,
        "runtime_binding_digest": runtime.runtime_binding_digest,
    }
    material = {"desired_state": "running", "reason_code": "founder_start"}
    command_digest = digest_paper_runtime_control_command(
        namespace="start_paper_runtime",
        command_actor="founder",
        command_target_identity=target,
        material_payload=material,
    )
    assert command_digest == digest_paper_runtime_control_command(
        namespace="start_paper_runtime",
        command_actor="founder",
        command_target_identity=dict(reversed(tuple(target.items()))),
        material_payload=dict(reversed(tuple(material.items()))),
    )
    assert command_digest != digest_paper_runtime_control_command(
        namespace="stop_paper_runtime",
        command_actor="founder",
        command_target_identity=target,
        material_payload=material,
    )
    assert command_digest != digest_paper_runtime_control_command(
        namespace="start_paper_runtime",
        command_actor="another-founder",
        command_target_identity=target,
        material_payload=material,
    )
    assert command_digest != digest_paper_runtime_control_command(
        namespace="start_paper_runtime",
        command_actor="founder",
        command_target_identity={**target, "runtime_id": "different-runtime"},
        material_payload=material,
    )
    assert command_digest != digest_paper_runtime_control_command(
        namespace="start_paper_runtime",
        command_actor="founder",
        command_target_identity=target,
        material_payload={**material, "desired_state": "stopped"},
    )

    service = _service(factory, _Clock(AUDIT + timedelta(minutes=2)))
    try:
        replay = service.resolve_control_replay(
            namespace=receipt.namespace,
            command_idempotency_key=receipt.command_idempotency_key,
            command_digest=receipt.command_digest,
        )
        assert replay is not None
        assert replay.runtime == runtime
        assert replay.event == event
        assert replay.receipt == receipt

        advanced = _copy(
            runtime,
            desired_state="running",
            observed_state="running",
            row_version=1,
            updated_at=AUDIT + timedelta(minutes=1),
        )
        with factory.begin() as session:
            SqlAlchemyPaperRuntimeRepository(session=session).compare_and_swap_runtime(
                expected_runtime=runtime, replacement_runtime=advanced
            )
        historical = service.resolve_control_replay(
            namespace=receipt.namespace,
            command_idempotency_key="different-key-same-material",
            command_digest=receipt.command_digest,
        )
        assert historical is not None
        assert historical.runtime == runtime
        assert historical.receipt == receipt
        assert _read(factory, runtime.runtime_id) == (
            advanced,
            (event,),
            (receipt,),
        )
        with pytest.raises(PaperRuntimeControlIdempotencyConflictError):
            service.resolve_control_replay(
                namespace=receipt.namespace,
                command_idempotency_key=receipt.command_idempotency_key,
                command_digest="d" * 64,
            )
        assert (
            service.resolve_control_replay(
                namespace="start_paper_runtime",
                command_idempotency_key=receipt.command_idempotency_key,
                command_digest=receipt.command_digest,
            )
            is None
        )
    finally:
        engine.dispose()


def test_control_namespace_isolation_can_hold_same_key_and_digest(
    tmp_path, monkeypatch
):
    engine, factory, runtime, create_event, create_receipt = _stored_runtime(
        tmp_path / "namespace.sqlite3", monkeypatch
    )
    start_event = create_paper_runtime_event(
        runtime=runtime,
        event_sequence=1,
        event_type="start_requested",
        resulting_runtime_version=runtime.row_version,
        payload={"resulting_runtime": runtime.to_dict()},
        recorded_at=AUDIT + timedelta(seconds=1),
    )
    start_receipt = create_paper_runtime_command_receipt(
        namespace="start_paper_runtime",
        command_idempotency_key=create_receipt.command_idempotency_key,
        command_digest=create_receipt.command_digest,
        command_actor="founder",
        runtime=runtime,
        result_event=start_event,
        created_at=AUDIT + timedelta(seconds=1),
    )
    try:
        with factory.begin() as session:
            repository = SqlAlchemyPaperRuntimeRepository(session=session)
            repository.append_event(event=start_event)
            repository.append_receipt(receipt=start_receipt)
        service = _service(factory, _Clock(AUDIT + timedelta(minutes=1)))
        create_replay = service.resolve_control_replay(
            namespace="create_paper_runtime",
            command_idempotency_key=create_receipt.command_idempotency_key,
            command_digest=create_receipt.command_digest,
        )
        start_replay = service.resolve_control_replay(
            namespace="start_paper_runtime",
            command_idempotency_key=start_receipt.command_idempotency_key,
            command_digest=start_receipt.command_digest,
        )
        assert create_replay is not None and create_replay.event == create_event
        assert start_replay is not None and start_replay.event == start_event
        assert len(_read(factory, runtime.runtime_id)[2]) == 2
    finally:
        engine.dispose()


@pytest.mark.parametrize("corruption", ("receipt", "event"))
def test_corrupt_control_receipt_or_event_fails_closed(
    tmp_path, monkeypatch, corruption
):
    engine, factory, runtime, event, receipt = _stored_runtime(
        tmp_path / f"corrupt-{corruption}.sqlite3", monkeypatch
    )
    try:
        with engine.begin() as connection:
            if corruption == "receipt":
                connection.execute(
                    text("DROP TRIGGER trg_paper_runtime_receipts_no_update")
                )
                connection.execute(
                    text(
                        "UPDATE paper_runtime_command_receipts "
                        "SET result_event_digest=:digest WHERE namespace=:namespace"
                    ),
                    {"digest": "e" * 64, "namespace": receipt.namespace},
                )
            else:
                connection.execute(
                    text("DROP TRIGGER trg_paper_runtime_events_no_update")
                )
                connection.execute(
                    text(
                        "UPDATE paper_runtime_events SET payload_json='{}' "
                        "WHERE event_id=:event_id"
                    ),
                    {"event_id": event.event_id},
                )
        with pytest.raises(PaperRuntimePersistenceCorruptionError):
            _service(
                factory, _Clock(AUDIT + timedelta(minutes=1))
            ).resolve_control_replay(
                namespace=receipt.namespace,
                command_idempotency_key=receipt.command_idempotency_key,
                command_digest=receipt.command_digest,
            )
    finally:
        engine.dispose()
