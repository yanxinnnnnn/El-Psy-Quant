"""Focused Sprint 222 crash/restart and reconciliation evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import pytest
from sqlalchemy import text

from el_psy_quant.application import (
    PaperRuntimeClaimMismatchError,
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeRecoveryService,
)
from el_psy_quant.persistence import (
    PaperExecutionStorageFailureError,
    PaperRuntimePersistenceCorruptionError,
    SqlAlchemyPaperExecutionRepository,
    SqlAlchemyPaperRuntimeRepository,
)
from test_paper_runtime_lifecycle import _diverge_account
from test_paper_runtime_runner import _read, _run_one, _runner_fixture
from test_paper_execution_persistence import _step_command


def _recovery(factory, ownership, runner, clock):
    return PaperRuntimeRecoveryService(
        session_factory=factory,
        execution_service=runner._execution_service,
        ownership_service=ownership,
        clock=clock,
    )


def _expire(clock, runtime) -> None:
    clock.value = runtime.lease_expires_at


def _leave_work_without_attempt(runner, claim, monkeypatch):
    original = runner._execution_service.step_order

    def fail(_command):
        raise PaperExecutionStorageFailureError()

    monkeypatch.setattr(runner._execution_service, "step_order", fail)
    with pytest.raises(PaperExecutionStorageFailureError):
        _run_one(runner, claim)
    monkeypatch.setattr(runner._execution_service, "step_order", original)


def _commit_without_observation(runner, claim, monkeypatch):
    original = runner._execution_service.step_order

    def commit_then_lose(command):
        original(command)
        raise RuntimeError("simulated process loss after M34 commit")

    monkeypatch.setattr(runner._execution_service, "step_order", commit_then_lose)
    with pytest.raises(RuntimeError, match="simulated process loss"):
        _run_one(runner, claim)
    monkeypatch.setattr(runner._execution_service, "step_order", original)


def test_unowned_crash_a_recovers_claim_then_normal_runner_creates_work(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "crash-a.sqlite3", monkeypatch)
    )
    released = ownership.release_runtime_claim(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    ).runtime
    result = _recovery(factory, ownership, runner, _clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="restart-worker"
    )
    assert result.outcome == "runnable"
    assert result.runtime.owner_id == "restart-worker"
    assert result.runtime.fencing_token == released.fencing_token + 1
    assert result.work is result.checkpoint is None

    continued = _run_one(runner, result.runtime)
    _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert continued.work == work[0]
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert [event.event_type for event in events].count("work_created") == 1
    engine.dispose()


def test_active_foreign_owner_rejects_and_concurrent_unowned_recovery_has_one_winner(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "claim-race.sqlite3", monkeypatch)
    )
    recovery = _recovery(factory, ownership, runner, clock)
    with pytest.raises(PaperRuntimeOwnershipBusyError):
        recovery.recover_runtime(
            runtime_id=claim.runtime_id, recovery_owner_id="foreign-worker"
        )
    assert _read(factory, claim.runtime_id)[0] == claim

    ownership.release_runtime_claim(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )

    def recover(owner):
        try:
            return recovery.recover_runtime(
                runtime_id=claim.runtime_id, recovery_owner_id=owner
            )
        except PaperRuntimeOwnershipBusyError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(recover, ("worker-a", "worker-b")))
    winners = tuple(item for item in outcomes if not isinstance(item, Exception))
    losers = tuple(item for item in outcomes if isinstance(item, Exception))
    assert len(winners) == len(losers) == 1
    assert winners[0].outcome == "runnable"
    engine.dispose()


def test_crash_b_running_reuses_exact_work_across_expired_takeover(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "crash-b-running.sqlite3", monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    before = _read(factory, claim.runtime_id)
    _expire(clock, before[0])
    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="takeover-worker"
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "runnable"
    assert result.work == before[1][0] == work[0]
    assert result.work.m34_step_idempotency_key == work[0].m34_step_idempotency_key
    assert result.work.m34_step_actor == runtime.logical_actor
    assert result.work.expected_execution_version == 0
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert [event.event_type for event in events].count("work_created") == 1
    assert [event.event_type for event in events].count("work_observed") == 1
    assert runtime.fencing_token == claim.fencing_token + 1
    with factory() as session:
        receipt = SqlAlchemyPaperExecutionRepository(session=session).get_receipt(
            namespace="step_paper_execution_order",
            command_idempotency_key=work[0].m34_step_idempotency_key,
        )
    assert receipt is not None
    assert receipt.command_actor == work[0].m34_step_actor == runtime.logical_actor
    assert receipt.attempt_id == history.attempts[0].attempt_id
    engine.dispose()


def test_crash_b_stopped_pending_work_does_not_step_and_releases(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "crash-b-stopped.sqlite3", monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    lifecycle.stop_runtime(
        runtime_id=current.runtime_id,
        runtime_binding_digest=current.runtime_binding_digest,
        expected_runtime_version=current.row_version,
        command_idempotency_key="stop-before-recovery",
        command_actor="founder",
    )
    _expire(clock, _read(factory, claim.runtime_id)[0])
    calls = []

    def forbidden(_command):
        calls.append(_command)
        raise AssertionError("recovery must not start an unproven stopped Step")

    monkeypatch.setattr(runner._execution_service, "step_order", forbidden)
    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="stop-cleanup"
    )
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "stopped"
    assert runtime.desired_state == runtime.observed_state == "stopped"
    assert runtime.owner_id is None
    assert len(work) == 1
    assert checkpoints == history.attempts == ()
    assert calls == []
    engine.dispose()


def test_crash_d_committed_step_catches_up_once_then_live_divergence_blocks(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "crash-d.sqlite3", monkeypatch)
    )
    _commit_without_observation(runner, claim, monkeypatch)
    _diverge_account(factory, order)
    current, original_work, checkpoints, _events, history = _read(
        factory, claim.runtime_id
    )
    assert len(original_work) == len(history.attempts) == 1
    assert checkpoints == ()
    _expire(clock, current)

    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="catchup-worker"
    )
    runtime, work, checkpoints, events, later = _read(factory, claim.runtime_id)
    assert result.outcome == "blocked"
    assert result.work == original_work[0]
    assert result.checkpoint == checkpoints[0]
    assert result.step_replayed is True
    assert work == original_work
    assert len(checkpoints) == len(later.attempts) == 1
    assert later.attempts == history.attempts
    assert runtime.block_reason_code == "stale_live_continuation"
    assert runtime.owner_id is None
    assert [event.event_type for event in events].count("work_observed") == 1
    assert [event.event_type for event in events].count("runtime_blocked") == 1
    engine.dispose()


def test_committed_step_stopped_catches_up_then_releases_without_next_work(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "stopped-catchup.sqlite3", monkeypatch)
    )
    _commit_without_observation(runner, claim, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    lifecycle.stop_runtime(
        runtime_id=current.runtime_id,
        runtime_binding_digest=current.runtime_binding_digest,
        expected_runtime_version=current.row_version,
        command_idempotency_key="stop-after-commit",
        command_actor="founder",
    )
    _expire(clock, _read(factory, claim.runtime_id)[0])
    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="stopped-catchup-worker"
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "stopped"
    assert runtime.owner_id is None
    assert runtime.desired_state == runtime.observed_state == "stopped"
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert [event.event_type for event in events].count("work_observed") == 1
    assert [event.event_type for event in events].count("work_created") == 1
    engine.dispose()


def test_crash_f_blocks_once_without_repair_and_block_event_failure_rolls_back(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "crash-f.sqlite3", monkeypatch)
    )
    recovery = _recovery(factory, ownership, runner, clock)

    def corrupt(**_kwargs):
        raise PaperRuntimePersistenceCorruptionError()

    monkeypatch.setattr(recovery, "_phase_r1_reconcile", corrupt)
    result = recovery.reconcile_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "blocked"
    assert runtime.observed_state == "blocked"
    assert runtime.block_reason_code == "operational_authority_corrupt"
    assert runtime.owner_id is None
    assert work == checkpoints == history.attempts == ()
    assert [event.event_type for event in events].count("runtime_blocked") == 1
    repeated = recovery.recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="blocked-retry"
    )
    assert repeated.outcome == "blocked"
    assert repeated.runtime.owner_id is None
    assert [
        event.event_type
        for event in _read(factory, claim.runtime_id)[3]
    ].count("runtime_blocked") == 1
    engine.dispose()

    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "block-rollback.sqlite3", monkeypatch)
    )
    recovery = _recovery(factory, ownership, runner, clock)
    monkeypatch.setattr(recovery, "_phase_r1_reconcile", corrupt)
    original = SqlAlchemyPaperRuntimeRepository.append_event

    def fail_block_event(self, *, event):
        if event.event_type == "runtime_blocked":
            raise RuntimeError("simulated blocked event failure")
        return original(self, event=event)

    monkeypatch.setattr(SqlAlchemyPaperRuntimeRepository, "append_event", fail_block_event)
    with pytest.raises(RuntimeError, match="simulated blocked event failure"):
        recovery.reconcile_claimed_runtime(
            runtime_id=claim.runtime_id,
            owner_id=claim.owner_id,
            fencing_token=claim.fencing_token,
        )
    runtime, _work, _checkpoints, events, _history = _read(factory, claim.runtime_id)
    assert runtime.observed_state != "blocked"
    assert [event.event_type for event in events].count("runtime_blocked") == 0
    engine.dispose()


def test_recovery_never_holds_m35_transaction_while_calling_m34_step(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "transaction-boundary.sqlite3", monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    _expire(clock, current)
    recovery = _recovery(factory, ownership, runner, clock)
    active = 0
    original_write = recovery._write
    original_step = runner._execution_service.step_order

    @contextmanager
    def tracked_write():
        nonlocal active
        with original_write() as session:
            active += 1
            try:
                yield session
            finally:
                active -= 1

    def checked_step(command):
        assert active == 0
        return original_step(command)

    monkeypatch.setattr(recovery, "_write", tracked_write)
    monkeypatch.setattr(runner._execution_service, "step_order", checked_step)
    result = recovery.recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="boundary-worker"
    )
    assert result.outcome == "runnable"
    engine.dispose()


def test_stale_old_fence_cannot_observe_after_takeover(tmp_path, monkeypatch):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "old-fence.sqlite3", monkeypatch)
    )
    _commit_without_observation(runner, claim, monkeypatch)
    current, work, *_ = _read(factory, claim.runtime_id)
    _expire(clock, current)
    replacement = ownership.claim_runtime(
        runtime_id=claim.runtime_id, owner_id="replacement"
    ).runtime
    step = runner._execution_service.step_order(
        PaperRuntimeRecoveryService._work_command(replacement, work[0])
    )
    with pytest.raises(PaperRuntimeClaimMismatchError):
        runner._phase_c_observe(
            runtime_id=claim.runtime_id,
            owner_id=claim.owner_id,
            fencing_token=claim.fencing_token,
            work=work[0],
            step=step,
        )
    result = _recovery(factory, ownership, runner, clock).reconcile_claimed_runtime(
        runtime_id=replacement.runtime_id,
        owner_id=replacement.owner_id,
        fencing_token=replacement.fencing_token,
    )
    assert result.outcome == "runnable"
    assert len(_read(factory, claim.runtime_id)[2]) == 1
    engine.dispose()


def test_terminal_fill_recovery_has_one_attempt_fill_settlement_and_progression(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "terminal-fill.sqlite3", monkeypatch)
    )
    first = _run_one(runner, claim)
    assert first.outcome == "running"
    _commit_without_observation(runner, first.runtime, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    _expire(clock, current)
    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="terminal-worker"
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "completed"
    assert runtime.observed_state == "completed"
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == len(history.attempts) == 2
    assert len(history.fills) == len(history.settlement_links) == 1
    assert [event.event_type for event in events].count("work_observed") == 2
    assert [event.event_type for event in events].count("runtime_completed") == 1
    with engine.connect() as connection:
        assert connection.scalar(
            text(
                "SELECT COUNT(*) FROM paper_account_events "
                "WHERE event_type='execution_fill_posted'"
            )
        ) == 1
        assert connection.scalar(
            text(
                "SELECT position FROM market_data_replays "
                "WHERE replay_id=:replay_id"
            ),
            {"replay_id": order.market_handoff_reference.replay_id},
        ) == 6
    engine.dispose()


def test_missing_runtime_work_for_runtime_era_m34_progression_blocks_without_repair(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "missing-work.sqlite3", monkeypatch)
    )
    runner._execution_service.step_order(
        _step_command(order, version=0, key="outside-m35-runtime-step")
    )
    ownership.release_runtime_claim(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )
    result = _recovery(factory, ownership, runner, clock).recover_runtime(
        runtime_id=claim.runtime_id, recovery_owner_id="reconcile-missing-work"
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "blocked"
    assert runtime.block_reason_code == "operational_authority_corrupt"
    assert work == checkpoints == ()
    assert len(history.attempts) == 1
    assert [event.event_type for event in events].count("runtime_blocked") == 1
    engine.dispose()


def test_catchup_observation_failure_rolls_back_checkpoint_and_event(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "catchup-rollback.sqlite3", monkeypatch)
    )
    _commit_without_observation(runner, claim, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    _expire(clock, current)
    original = SqlAlchemyPaperRuntimeRepository.append_event

    def fail_observation(self, *, event):
        if event.event_type == "work_observed":
            raise RuntimeError("simulated observation event failure")
        return original(self, event=event)

    monkeypatch.setattr(SqlAlchemyPaperRuntimeRepository, "append_event", fail_observation)
    with pytest.raises(RuntimeError, match="simulated observation event failure"):
        _recovery(factory, ownership, runner, clock).recover_runtime(
            runtime_id=claim.runtime_id, recovery_owner_id="rollback-worker"
        )
    _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert len(work) == len(history.attempts) == 1
    assert checkpoints == ()
    assert [event.event_type for event in events].count("work_observed") == 0
    engine.dispose()


def test_unreconstructible_runtime_receives_no_speculative_block_write(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "unreconstructible.sqlite3", monkeypatch)
    )
    ownership.release_runtime_claim(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )
    with engine.begin() as connection:
        original_payload = connection.scalar(
            text("SELECT payload_json FROM paper_runtimes WHERE runtime_id=:id"),
            {"id": claim.runtime_id},
        )
        connection.execute(
            text("UPDATE paper_runtimes SET payload_json='{}' WHERE runtime_id=:id"),
            {"id": claim.runtime_id},
        )
    with pytest.raises(PaperRuntimePersistenceCorruptionError):
        _recovery(factory, ownership, runner, clock).recover_runtime(
            runtime_id=claim.runtime_id, recovery_owner_id="must-not-repair"
        )
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT payload_json, observed_state, owner_id FROM paper_runtimes "
                "WHERE runtime_id=:id"
            ),
            {"id": claim.runtime_id},
        ).one()
        blocked_events = connection.scalar(
            text(
                "SELECT COUNT(*) FROM paper_runtime_events "
                "WHERE runtime_id=:id AND event_type='runtime_blocked'"
            ),
            {"id": claim.runtime_id},
        )
    assert original_payload != row.payload_json == "{}"
    assert row.observed_state != "blocked"
    assert row.owner_id is None
    assert blocked_events == 0
    engine.dispose()


def test_completed_transition_event_failure_rolls_back_catchup_and_lifecycle(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(tmp_path / "completed-rollback.sqlite3", monkeypatch)
    )
    first = _run_one(runner, claim)
    _commit_without_observation(runner, first.runtime, monkeypatch)
    current = _read(factory, claim.runtime_id)[0]
    _expire(clock, current)
    recovery = _recovery(factory, ownership, runner, clock)
    original = SqlAlchemyPaperRuntimeRepository.append_event

    def fail_completion(self, *, event):
        if event.event_type == "runtime_completed":
            raise RuntimeError("simulated completion event failure")
        return original(self, event=event)

    monkeypatch.setattr(SqlAlchemyPaperRuntimeRepository, "append_event", fail_completion)
    with pytest.raises(RuntimeError, match="simulated completion event failure"):
        recovery.recover_runtime(
            runtime_id=claim.runtime_id, recovery_owner_id="completion-worker"
        )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert runtime.observed_state == "running"
    assert runtime.owner_id == "completion-worker"
    assert len(work) == len(history.attempts) == 2
    assert len(checkpoints) == 1
    assert [event.event_type for event in events].count("work_observed") == 1
    assert [event.event_type for event in events].count("runtime_completed") == 0

    monkeypatch.setattr(SqlAlchemyPaperRuntimeRepository, "append_event", original)
    completed = recovery.reconcile_claimed_runtime(
        runtime_id=runtime.runtime_id,
        owner_id=runtime.owner_id,
        fencing_token=runtime.fencing_token,
    )
    assert completed.outcome == "completed"
    assert _read(factory, claim.runtime_id)[0].owner_id is None
    engine.dispose()
