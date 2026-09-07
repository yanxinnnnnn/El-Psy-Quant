"""Focused Sprint 220 runtime lifecycle and durable control evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import text

from el_psy_quant.application import (
    PaperAccountApplicationService,
    PaperExecutionApplicationService,
    PaperRuntimeAlreadyExistsError,
    PaperRuntimeBindingMismatchError,
    PaperRuntimeControlIdempotencyConflictError,
    PaperRuntimeLifecycleConflictError,
    PaperRuntimeLifecycleService,
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeOwnershipService,
    PaperRuntimeTerminalContinuationError,
)
from el_psy_quant.paper_account import PaperMoney
from el_psy_quant.paper_runtime import PaperRuntime
from el_psy_quant.persistence import (
    PaperExecutionReconciliationRequiredError,
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimePersistenceCorruptionError,
    SqlAlchemyPaperAccountRepository,
    SqlAlchemyPaperRuntimeRepository,
)
from test_paper_execution_persistence import _step_command
from test_paper_runtime_persistence import AUDIT, _authorities


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


def _fixture(path, monkeypatch, *, terminal: bool = False):
    engine, factory, order, _commit, _runtime, _work, _event, _receipt = _authorities(
        path, monkeypatch, step=terminal
    )
    clock = _Clock(AUDIT + timedelta(hours=1))
    service = PaperRuntimeLifecycleService(session_factory=factory, clock=clock)
    return engine, factory, order, clock, service


def _create(service, order, *, key: str = "create-runtime", actor: str = "founder"):
    return service.create_runtime(
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        logical_actor="paper-runtime",
        runtime_policy_id="durable-runtime-v1",
        runtime_policy_version=1,
        command_idempotency_key=key,
        command_actor=actor,
    )


def _command(runtime: PaperRuntime, *, key: str, actor: str = "founder"):
    return {
        "runtime_id": runtime.runtime_id,
        "runtime_binding_digest": runtime.runtime_binding_digest,
        "expected_runtime_version": runtime.row_version,
        "command_idempotency_key": key,
        "command_actor": actor,
    }


def _read(factory, runtime_id: str):
    with factory() as session:
        repository = SqlAlchemyPaperRuntimeRepository(session=session)
        return (
            repository.get_runtime(runtime_id=runtime_id),
            repository.list_events(runtime_id=runtime_id),
            repository.list_receipts(runtime_id=runtime_id),
            repository.list_work(runtime_id=runtime_id),
            repository.list_checkpoints(runtime_id=runtime_id),
        )


def _replace(factory, runtime: PaperRuntime, **changes: object) -> PaperRuntime:
    replacement = _copy(
        runtime,
        row_version=runtime.row_version + 1,
        updated_at=runtime.updated_at + timedelta(seconds=1),
        **changes,
    )
    with factory.begin() as session:
        return SqlAlchemyPaperRuntimeRepository(
            session=session
        ).compare_and_swap_runtime(
            expected_runtime=runtime, replacement_runtime=replacement
        )


def _downstream_authority_snapshot(engine):
    tables = (
        "paper_runtime_work",
        "paper_runtime_checkpoints",
        "paper_execution_orders",
        "paper_execution_attempts",
        "paper_execution_fills",
        "paper_execution_settlement_links",
        "paper_execution_command_receipts",
        "paper_accounts",
        "paper_account_events",
        "paper_cash_ledger_entries",
        "paper_position_ledger_entries",
        "paper_account_creation_keys",
        "paper_account_projections",
        "paper_account_position_projections",
        "paper_account_snapshots",
        "paper_account_reconciliations",
        "market_data_replays",
        "market_data_replay_events",
    )
    with engine.connect() as connection:
        return tuple(
            (
                table,
                tuple(
                    tuple(row)
                    for row in connection.execute(
                        text(f"SELECT * FROM {table} ORDER BY rowid")
                    )
                ),
            )
            for table in tables
        )


def _assert_exact_lifecycle_race(
    *,
    factory,
    engine,
    results,
    namespace: str,
    event_type: str,
    command_key: str,
    expected_runtime_version: int,
    expected_states: tuple[str, str],
    downstream_before,
) -> None:
    assert sorted(result.replayed for result in results) == [False, True]
    assert results[0].runtime == results[1].runtime
    assert results[0].event == results[1].event
    assert results[0].receipt == results[1].receipt
    assert results[0].receipt.command_digest == results[1].receipt.command_digest
    assert results[0].receipt.command_idempotency_key == command_key
    assert results[0].receipt.namespace == namespace

    canonical = results[0]
    current, events, receipts, work, checkpoints = _read(
        factory, canonical.runtime.runtime_id
    )
    command_events = tuple(event for event in events if event.event_type == event_type)
    command_receipts = tuple(
        receipt
        for receipt in receipts
        if receipt.namespace == namespace
        and receipt.command_idempotency_key == command_key
    )
    assert current == canonical.runtime
    assert current.row_version == expected_runtime_version
    assert (current.desired_state, current.observed_state) == expected_states
    assert command_events == (canonical.event,)
    assert command_receipts == (canonical.receipt,)
    assert canonical.receipt.result_event_id == canonical.event.event_id
    assert not work and not checkpoints
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM paper_runtimes")) == 1
    assert _downstream_authority_snapshot(engine) == downstream_before


def _diverge_account(factory, order) -> None:
    with factory() as session:
        account = SqlAlchemyPaperAccountRepository(session=session).get_account(
            account_id=order.account_id
        )
    assert account is not None
    PaperAccountApplicationService(
        session_factory=factory,
        clock=lambda: AUDIT + timedelta(hours=2),
    ).post_cash_movement(
        account_id=order.account_id,
        expected_account_version=account.head_version,
        command_idempotency_key="external-runtime-divergence",
        actor="founder",
        reason="deterministic S220 live-head divergence",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("1"),
    )


def test_create_has_exact_initial_runtime_event_receipt_and_no_execution_side_effects(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "create.sqlite3", monkeypatch
    )
    try:
        result = _create(service, order)
        runtime = result.runtime
        assert result.replayed is False
        assert (runtime.desired_state, runtime.observed_state) == ("stopped", "ready")
        assert runtime.owner_id is None
        assert runtime.fencing_token == runtime.row_version == 0
        assert runtime.created_at == runtime.updated_at == clock.value
        assert result.event.event_type == "runtime_created"
        assert result.event.event_sequence == 0
        assert result.receipt.namespace == "create_paper_runtime"
        assert result.receipt.result_event_id == result.event.event_id
        current, events, receipts, work, checkpoints = _read(
            factory, runtime.runtime_id
        )
        assert (current, events, receipts) == (
            runtime,
            (result.event,),
            (result.receipt,),
        )
        assert not work and not checkpoints
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


def test_create_replay_convergence_conflict_and_one_runtime_per_order(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "create-idempotency.sqlite3", monkeypatch
    )
    try:
        first = _create(service, order)
        clock.value += timedelta(minutes=1)
        exact = _create(service, order)
        converged = _create(service, order, key="same-create-new-key")
        assert exact.replayed and converged.replayed
        assert exact.runtime == converged.runtime == first.runtime
        assert exact.event == converged.event == first.event
        with pytest.raises(PaperRuntimeControlIdempotencyConflictError):
            _create(service, order, actor="another-founder")
        with pytest.raises(PaperRuntimeAlreadyExistsError):
            service.create_runtime(
                execution_order_id=order.execution_order_id,
                execution_order_digest=order.execution_order_digest,
                logical_actor="different-logical-actor",
                runtime_policy_id="durable-runtime-v1",
                runtime_policy_version=1,
                command_idempotency_key="different-create",
                command_actor="founder",
            )
        _current, events, receipts, _work, _checkpoints = _read(
            factory, first.runtime.runtime_id
        )
        assert len(events) == len(receipts) == 1
    finally:
        engine.dispose()


def test_create_rejects_wrong_digest_terminal_and_live_stale_order(
    tmp_path, monkeypatch
):
    wrong = tmp_path / "wrong.sqlite3"
    engine, _factory, order, _clock, service = _fixture(wrong, monkeypatch)
    try:
        with pytest.raises(PaperRuntimeBindingMismatchError):
            service.create_runtime(
                execution_order_id=order.execution_order_id,
                execution_order_digest="f" * 64,
                logical_actor="paper-runtime",
                runtime_policy_id="durable-runtime-v1",
                runtime_policy_version=1,
                command_idempotency_key="wrong-digest",
                command_actor="founder",
            )
    finally:
        engine.dispose()

    terminal_engine, _factory, terminal_order, _clock, terminal_service = _fixture(
        tmp_path / "terminal.sqlite3", monkeypatch, terminal=True
    )
    try:
        with pytest.raises(PaperRuntimeTerminalContinuationError):
            _create(terminal_service, terminal_order)
    finally:
        terminal_engine.dispose()

    stale_engine, stale_factory, stale_order, _clock, stale_service = _fixture(
        tmp_path / "stale.sqlite3", monkeypatch
    )
    try:
        _diverge_account(stale_factory, stale_order)
        with pytest.raises(PaperExecutionReconciliationRequiredError):
            _create(stale_service, stale_order)
    finally:
        stale_engine.dispose()


@pytest.mark.parametrize("failure", ("event", "receipt"))
def test_create_rolls_back_runtime_event_and_receipt_together(
    tmp_path, monkeypatch, failure
):
    engine, factory, order, _clock, service = _fixture(
        tmp_path / f"create-rollback-{failure}.sqlite3", monkeypatch
    )

    def fail(self, **_kwargs):
        del self
        raise RuntimeError(f"injected {failure} failure")

    monkeypatch.setattr(
        SqlAlchemyPaperRuntimeRepository,
        "append_event" if failure == "event" else "append_receipt",
        fail,
    )
    try:
        with pytest.raises(RuntimeError, match=f"injected {failure} failure"):
            _create(service, order)
        with engine.connect() as connection:
            for table in (
                "paper_runtimes",
                "paper_runtime_events",
                "paper_runtime_command_receipts",
            ):
                assert connection.scalar(text(f"SELECT COUNT(*) FROM {table}")) == 0
    finally:
        engine.dispose()


def test_start_stop_and_historical_replay_preserve_exact_snapshots(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "start-stop.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        assert (started.runtime.desired_state, started.runtime.observed_state) == (
            "running",
            "ready",
        )
        assert started.runtime.row_version == 1
        assert started.event.event_type == "start_requested"
        clock.value += timedelta(minutes=1)
        stopped = service.stop_runtime(**_command(started.runtime, key="stop"))
        assert (stopped.runtime.desired_state, stopped.runtime.observed_state) == (
            "stopped",
            "ready",
        )
        assert stopped.runtime.row_version == 2
        historical = service.start_runtime(**_command(created.runtime, key="start"))
        assert historical.replayed
        assert historical.runtime == started.runtime
        converged = service.start_runtime(
            **_command(created.runtime, key="same-start-new-key")
        )
        assert converged.replayed and converged.event == started.event
        with pytest.raises(PaperRuntimeControlIdempotencyConflictError):
            service.start_runtime(
                **_command(created.runtime, key="start", actor="another-founder")
            )
        with pytest.raises(PaperRuntimeControlIdempotencyConflictError):
            service.start_runtime(**_command(stopped.runtime, key="start"))
        assert _read(factory, created.runtime.runtime_id)[:3] == (
            stopped.runtime,
            (created.event, started.event, stopped.event),
            (created.receipt, started.receipt, stopped.receipt),
        )
        restarted = service.start_runtime(
            **_command(stopped.runtime, key="second-start")
        )
        with pytest.raises(PaperRuntimeLifecycleConflictError):
            service.start_runtime(**_command(restarted.runtime, key="invalid-start"))
    finally:
        engine.dispose()


def test_stop_preserves_active_claim_and_succeeds_after_live_head_divergence(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "safe-stop.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        ownership = PaperRuntimeOwnershipService(
            session_factory=factory,
            lease_duration=timedelta(minutes=10),
            clock=clock,
        )
        claimed = ownership.claim_runtime(
            runtime_id=started.runtime.runtime_id, owner_id="worker-a"
        ).runtime
        _diverge_account(factory, order)
        clock.value += timedelta(minutes=1)
        stopped = service.stop_runtime(**_command(claimed, key="safe-stop"))
        assert stopped.runtime.desired_state == "stopped"
        assert stopped.runtime.observed_state == claimed.observed_state == "ready"
        for field in (
            "owner_id",
            "claimed_at",
            "heartbeat_at",
            "lease_expires_at",
            "fencing_token",
        ):
            assert getattr(stopped.runtime, field) == getattr(claimed, field)
    finally:
        engine.dispose()


def test_resume_requires_observed_stopped_and_live_freshness(tmp_path, monkeypatch):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "resume.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        ownership = PaperRuntimeOwnershipService(
            session_factory=factory,
            lease_duration=timedelta(minutes=10),
            clock=clock,
        )
        claimed = ownership.claim_runtime(
            runtime_id=created.runtime.runtime_id, owner_id="worker-a"
        ).runtime
        observed_stopped = _replace(factory, claimed, observed_state="stopped")
        clock.value = observed_stopped.updated_at + timedelta(minutes=1)
        resumed = service.resume_runtime(**_command(observed_stopped, key="resume"))
        assert (resumed.runtime.desired_state, resumed.runtime.observed_state) == (
            "running",
            "stopped",
        )
        for field in (
            "owner_id",
            "claimed_at",
            "heartbeat_at",
            "lease_expires_at",
            "fencing_token",
        ):
            assert getattr(resumed.runtime, field) == getattr(observed_stopped, field)
        with pytest.raises(PaperRuntimeLifecycleConflictError):
            service.resume_runtime(**_command(resumed.runtime, key="resume-again"))
    finally:
        engine.dispose()

    stale_engine, stale_factory, stale_order, stale_clock, stale_service = _fixture(
        tmp_path / "resume-stale.sqlite3", monkeypatch
    )
    try:
        created = _create(stale_service, stale_order)
        stopped = _replace(stale_factory, created.runtime, observed_state="stopped")
        _diverge_account(stale_factory, stale_order)
        stale_clock.value = stopped.updated_at + timedelta(hours=2)
        with pytest.raises(PaperExecutionReconciliationRequiredError):
            stale_service.resume_runtime(**_command(stopped, key="stale-resume"))
        assert _read(stale_factory, stopped.runtime_id)[0] == stopped
    finally:
        stale_engine.dispose()


@pytest.mark.parametrize("owner", ("none", "expired"))
def test_recover_request_preserves_state_claim_and_fence(tmp_path, monkeypatch, owner):
    engine, factory, order, clock, service = _fixture(
        tmp_path / f"recover-{owner}.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        current = started.runtime
        if owner == "expired":
            ownership = PaperRuntimeOwnershipService(
                session_factory=factory,
                lease_duration=timedelta(seconds=10),
                clock=clock,
            )
            current = ownership.claim_runtime(
                runtime_id=current.runtime_id, owner_id="stale-worker"
            ).runtime
            clock.value = current.lease_expires_at
        before = current
        recovered = service.recover_runtime(**_command(before, key="recover"))
        assert recovered.runtime.row_version == before.row_version + 1
        assert recovered.event.event_type == "recover_requested"
        for field in (
            "desired_state",
            "observed_state",
            "owner_id",
            "claimed_at",
            "heartbeat_at",
            "lease_expires_at",
            "fencing_token",
        ):
            assert getattr(recovered.runtime, field) == getattr(before, field)
        _current, _events, _receipts, work, checkpoints = _read(
            factory, before.runtime_id
        )
        assert not work and not checkpoints
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT COUNT(*) FROM paper_execution_attempts"))
                == 0
            )
    finally:
        engine.dispose()


def test_recover_rejects_active_owner_and_stopped_runtime(tmp_path, monkeypatch):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "recover-busy.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        ownership = PaperRuntimeOwnershipService(
            session_factory=factory,
            lease_duration=timedelta(minutes=1),
            clock=clock,
        )
        claimed = ownership.claim_runtime(
            runtime_id=started.runtime.runtime_id, owner_id="active-worker"
        ).runtime
        with pytest.raises(PaperRuntimeOwnershipBusyError):
            service.recover_runtime(**_command(claimed, key="busy-recover"))
        stopped = service.stop_runtime(**_command(claimed, key="stop"))
        with pytest.raises(PaperRuntimeLifecycleConflictError):
            service.recover_runtime(**_command(stopped.runtime, key="stopped-recover"))
        assert _read(factory, claimed.runtime_id)[0] == stopped.runtime
    finally:
        engine.dispose()


@pytest.mark.parametrize("failure", ("event", "receipt"))
def test_lifecycle_mutation_rolls_back_with_event_or_receipt_failure(
    tmp_path, monkeypatch, failure
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / f"lifecycle-rollback-{failure}.sqlite3", monkeypatch
    )
    created = _create(service, order)
    before = _read(factory, created.runtime.runtime_id)

    def fail(self, **_kwargs):
        del self
        raise RuntimeError(f"injected {failure} failure")

    monkeypatch.setattr(
        SqlAlchemyPaperRuntimeRepository,
        "append_event" if failure == "event" else "append_receipt",
        fail,
    )
    clock.value += timedelta(minutes=1)
    try:
        with pytest.raises(RuntimeError, match=f"injected {failure} failure"):
            service.start_runtime(**_command(created.runtime, key="start"))
        assert _read(factory, created.runtime.runtime_id) == before
    finally:
        engine.dispose()


def test_exact_start_race_has_one_mutation_and_one_historical_replay(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "start-race.sqlite3", monkeypatch
    )
    created = _create(service, order)
    clock.value += timedelta(minutes=1)
    barrier = Barrier(2)
    command = _command(created.runtime, key="racing-start")
    downstream_before = _downstream_authority_snapshot(engine)

    def start(_index):
        barrier.wait(timeout=10)
        return PaperRuntimeLifecycleService(
            session_factory=factory, clock=clock
        ).start_runtime(**command)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(pool.submit(start, index) for index in range(2))
            results = tuple(future.result(timeout=15) for future in futures)
        _assert_exact_lifecycle_race(
            factory=factory,
            engine=engine,
            results=results,
            namespace="start_paper_runtime",
            event_type="start_requested",
            command_key="racing-start",
            expected_runtime_version=created.runtime.row_version + 1,
            expected_states=("running", "ready"),
            downstream_before=downstream_before,
        )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("operation", "namespace", "event_type", "expected_states"),
    (
        (
            "create",
            "create_paper_runtime",
            "runtime_created",
            ("stopped", "ready"),
        ),
        (
            "stop",
            "stop_paper_runtime",
            "stop_requested",
            ("stopped", "ready"),
        ),
        (
            "resume",
            "resume_paper_runtime",
            "resume_requested",
            ("running", "stopped"),
        ),
        (
            "recover",
            "recover_paper_runtime",
            "recover_requested",
            ("running", "ready"),
        ),
    ),
)
def test_exact_same_key_lifecycle_races_converge_to_one_historical_result(
    tmp_path,
    monkeypatch,
    operation,
    namespace,
    event_type,
    expected_states,
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / f"{operation}-same-key-race.sqlite3", monkeypatch
    )
    command_key = f"racing-{operation}"
    command = None
    before = None
    try:
        if operation != "create":
            created = _create(service, order)
            before = created.runtime
            if operation in ("stop", "recover"):
                clock.value += timedelta(minutes=1)
                before = service.start_runtime(
                    **_command(before, key=f"prepare-{operation}-start")
                ).runtime
            elif operation == "resume":
                before = _replace(factory, before, observed_state="stopped")
                assert (before.desired_state, before.observed_state) == (
                    "stopped",
                    "stopped",
                )
            clock.value = before.updated_at + timedelta(minutes=1)
            command = _command(before, key=command_key)

        expected_runtime_version = 0 if before is None else before.row_version + 1
        downstream_before = _downstream_authority_snapshot(engine)
        barrier = Barrier(2)

        def mutate(_index):
            barrier.wait(timeout=10)
            race_service = PaperRuntimeLifecycleService(
                session_factory=factory, clock=clock
            )
            if operation == "create":
                return _create(race_service, order, key=command_key)
            assert command is not None
            return getattr(race_service, f"{operation}_runtime")(**command)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(pool.submit(mutate, index) for index in range(2))
            results = tuple(future.result(timeout=15) for future in futures)

        _assert_exact_lifecycle_race(
            factory=factory,
            engine=engine,
            results=results,
            namespace=namespace,
            event_type=event_type,
            command_key=command_key,
            expected_runtime_version=expected_runtime_version,
            expected_states=expected_states,
            downstream_before=downstream_before,
        )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("operation", "namespace", "event_type"),
    (
        ("create", "create_paper_runtime", "runtime_created"),
        ("start", "start_paper_runtime", "start_requested"),
        ("stop", "stop_paper_runtime", "stop_requested"),
        ("resume", "resume_paper_runtime", "resume_requested"),
        ("recover", "recover_paper_runtime", "recover_requested"),
    ),
)
def test_changed_material_digest_conflicts_without_second_lifecycle_mutation(
    tmp_path, monkeypatch, operation, namespace, event_type
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / f"{operation}-changed-digest.sqlite3", monkeypatch
    )
    command_key = f"{operation}-changed-digest"
    command = None
    try:
        if operation == "create":
            canonical = _create(service, order, key=command_key)
        else:
            created = _create(service, order)
            before = created.runtime
            if operation in ("stop", "recover"):
                clock.value += timedelta(minutes=1)
                before = service.start_runtime(
                    **_command(before, key=f"prepare-{operation}-start")
                ).runtime
            elif operation == "resume":
                before = _replace(factory, before, observed_state="stopped")
            clock.value = before.updated_at + timedelta(minutes=1)
            command = _command(before, key=command_key)
            canonical = getattr(service, f"{operation}_runtime")(**command)

        before_conflict = _read(factory, canonical.runtime.runtime_id)
        downstream_before = _downstream_authority_snapshot(engine)
        with pytest.raises(PaperRuntimeControlIdempotencyConflictError):
            if operation == "create":
                service.create_runtime(
                    execution_order_id=order.execution_order_id,
                    execution_order_digest=order.execution_order_digest,
                    logical_actor="changed-paper-runtime",
                    runtime_policy_id="durable-runtime-v1",
                    runtime_policy_version=1,
                    command_idempotency_key=command_key,
                    command_actor="founder",
                )
            else:
                assert command is not None
                changed_command = {
                    **command,
                    "expected_runtime_version": command["expected_runtime_version"] + 1,
                }
                getattr(service, f"{operation}_runtime")(**changed_command)

        after_conflict = _read(factory, canonical.runtime.runtime_id)
        current, events, receipts, work, checkpoints = after_conflict
        assert after_conflict == before_conflict
        assert current == canonical.runtime
        assert tuple(event for event in events if event.event_type == event_type) == (
            canonical.event,
        )
        assert tuple(
            receipt
            for receipt in receipts
            if receipt.namespace == namespace
            and receipt.command_idempotency_key == command_key
        ) == (canonical.receipt,)
        assert not work and not checkpoints
        assert _downstream_authority_snapshot(engine) == downstream_before
    finally:
        engine.dispose()


def test_expected_version_fences_conflicting_controls_and_event_sequence_is_independent(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "version-and-sequence.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        with pytest.raises(PaperRuntimeConcurrencyConflictError):
            service.stop_runtime(**_command(created.runtime, key="stale-stop"))

        ownership = PaperRuntimeOwnershipService(
            session_factory=factory,
            lease_duration=timedelta(minutes=1),
            clock=clock,
        )
        claimed = ownership.claim_runtime(
            runtime_id=started.runtime.runtime_id, owner_id="worker"
        ).runtime
        clock.value += timedelta(seconds=1)
        heartbeat = ownership.renew_runtime_claim(
            runtime_id=claimed.runtime_id,
            owner_id="worker",
            fencing_token=claimed.fencing_token,
        )
        clock.value += timedelta(seconds=1)
        stopped = service.stop_runtime(**_command(heartbeat, key="stop"))
        _current, events, _receipts, _work, _checkpoints = _read(
            factory, stopped.runtime.runtime_id
        )
        assert tuple(event.event_sequence for event in events) == tuple(range(4))
        assert tuple(event.resulting_runtime_version for event in events) == (
            0,
            1,
            2,
            4,
        )
    finally:
        engine.dispose()


def test_start_and_recover_require_live_nonterminal_m34_authority(
    tmp_path, monkeypatch
):
    stale_engine, stale_factory, stale_order, stale_clock, stale_service = _fixture(
        tmp_path / "start-stale.sqlite3", monkeypatch
    )
    try:
        created = _create(stale_service, stale_order)
        _diverge_account(stale_factory, stale_order)
        stale_clock.value += timedelta(minutes=1)
        with pytest.raises(PaperExecutionReconciliationRequiredError):
            stale_service.start_runtime(**_command(created.runtime, key="start"))
        assert _read(stale_factory, created.runtime.runtime_id)[0] == created.runtime
    finally:
        stale_engine.dispose()

    recover_engine, recover_factory, recover_order, recover_clock, recover_service = (
        _fixture(tmp_path / "recover-stale.sqlite3", monkeypatch)
    )
    try:
        created = _create(recover_service, recover_order)
        recover_clock.value += timedelta(minutes=1)
        started = recover_service.start_runtime(
            **_command(created.runtime, key="start")
        )
        _diverge_account(recover_factory, recover_order)
        recover_clock.value += timedelta(minutes=1)
        with pytest.raises(PaperExecutionReconciliationRequiredError):
            recover_service.recover_runtime(**_command(started.runtime, key="recover"))
        assert _read(recover_factory, started.runtime.runtime_id)[0] == started.runtime
    finally:
        recover_engine.dispose()


def test_terminal_m34_and_terminal_runtime_states_refuse_continuation(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "terminal-continuation.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        execution = PaperExecutionApplicationService(
            session_factory=factory, clock=lambda: clock.value
        )
        execution.step_order(_step_command(order, version=0, key="terminal-step-0"))
        execution.step_order(_step_command(order, version=1, key="terminal-step-1"))
        clock.value += timedelta(minutes=1)
        with pytest.raises(PaperRuntimeTerminalContinuationError):
            service.start_runtime(**_command(created.runtime, key="terminal-start"))
    finally:
        engine.dispose()

    blocked_engine, blocked_factory, blocked_order, blocked_clock, blocked_service = (
        _fixture(tmp_path / "blocked-runtime.sqlite3", monkeypatch)
    )
    try:
        created = _create(blocked_service, blocked_order)
        blocked = _replace(
            blocked_factory,
            created.runtime,
            desired_state="running",
            observed_state="blocked",
            block_reason_code="deterministic_block",
        )
        completed = _copy(
            blocked,
            observed_state="completed",
            block_reason_code=None,
            row_version=blocked.row_version + 1,
            updated_at=blocked.updated_at + timedelta(seconds=1),
        )
        blocked_clock.value = completed.updated_at + timedelta(minutes=1)
        with pytest.raises(PaperRuntimeTerminalContinuationError):
            blocked_service.recover_runtime(**_command(blocked, key="blocked-recover"))
        with blocked_factory.begin() as session:
            SqlAlchemyPaperRuntimeRepository(session=session).compare_and_swap_runtime(
                expected_runtime=blocked, replacement_runtime=completed
            )
        with pytest.raises(PaperRuntimeTerminalContinuationError):
            blocked_service.recover_runtime(
                **_command(completed, key="completed-recover")
            )
    finally:
        blocked_engine.dispose()


def test_stop_fails_closed_on_historical_m34_corruption(tmp_path, monkeypatch):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "stop-corrupt.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        with engine.begin() as connection:
            connection.execute(
                text("DROP TRIGGER trg_paper_execution_orders_no_update")
            )
            connection.execute(
                text(
                    "UPDATE paper_execution_orders SET payload_json='{}' "
                    "WHERE execution_order_id=:order_id"
                ),
                {"order_id": order.execution_order_id},
            )
        with pytest.raises(PaperRuntimePersistenceCorruptionError):
            service.stop_runtime(**_command(started.runtime, key="corrupt-stop"))
    finally:
        engine.dispose()


def test_create_and_lifecycle_clock_are_sampled_after_write_acquisition(
    tmp_path, monkeypatch
):
    engine, _factory, order, clock, service = _fixture(
        tmp_path / "post-lock-clock.sqlite3", monkeypatch
    )
    before = clock.value
    after = before + timedelta(minutes=1)
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
            clock.value = after
            yield session

    monkeypatch.setattr(service, "_clock", observed_clock)
    monkeypatch.setattr(service, "_write", post_acquisition_write)
    try:
        created = _create(service, order)
        assert observations == [after]
        assert created.runtime.created_at == created.runtime.updated_at == after
    finally:
        engine.dispose()


def test_concurrent_create_with_different_keys_converges_to_one_runtime(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, _service = _fixture(
        tmp_path / "create-race.sqlite3", monkeypatch
    )
    barrier = Barrier(2)

    def create(key: str):
        barrier.wait(timeout=10)
        service = PaperRuntimeLifecycleService(session_factory=factory, clock=clock)
        return _create(service, order, key=key)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(
                pool.submit(create, key) for key in ("create-a", "create-b")
            )
            results = tuple(future.result(timeout=15) for future in futures)
        assert sorted(result.replayed for result in results) == [False, True]
        assert results[0].runtime == results[1].runtime
        _current, events, receipts, _work, _checkpoints = _read(
            factory, results[0].runtime.runtime_id
        )
        assert len(events) == len(receipts) == 1
    finally:
        engine.dispose()


def test_every_lifecycle_namespace_replays_immutable_history_after_progression(
    tmp_path, monkeypatch
):
    engine, factory, order, clock, service = _fixture(
        tmp_path / "all-historical-replays.sqlite3", monkeypatch
    )
    try:
        created = _create(service, order)
        clock.value += timedelta(minutes=1)
        started = service.start_runtime(**_command(created.runtime, key="start"))
        clock.value += timedelta(minutes=1)
        recovered = service.recover_runtime(**_command(started.runtime, key="recover"))
        clock.value += timedelta(minutes=1)
        stopped = service.stop_runtime(**_command(recovered.runtime, key="stop"))
        observed_stopped = _replace(factory, stopped.runtime, observed_state="stopped")
        clock.value = observed_stopped.updated_at + timedelta(minutes=1)
        resumed = service.resume_runtime(**_command(observed_stopped, key="resume"))
        before = _read(factory, resumed.runtime.runtime_id)

        replays = (
            _create(service, order),
            service.start_runtime(**_command(created.runtime, key="start")),
            service.recover_runtime(**_command(started.runtime, key="recover")),
            service.stop_runtime(**_command(recovered.runtime, key="stop")),
            service.resume_runtime(**_command(observed_stopped, key="resume")),
        )
        expected = (created, started, recovered, stopped, resumed)
        assert all(result.replayed for result in replays)
        assert tuple(result.runtime for result in replays) == tuple(
            result.runtime for result in expected
        )
        assert tuple(result.event for result in replays) == tuple(
            result.event for result in expected
        )
        assert _read(factory, resumed.runtime.runtime_id) == before
    finally:
        engine.dispose()
