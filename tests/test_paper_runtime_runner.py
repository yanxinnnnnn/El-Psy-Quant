"""Focused Sprint 221 durable Paper Runtime runner evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import text

from el_psy_quant.application import (
    PaperExecutionApplicationService,
    PaperRuntimeClaimMismatchError,
    PaperRuntimeLeaseExpiredError,
    PaperRuntimeLifecycleService,
    PaperRuntimeObservationRequiredError,
    PaperRuntimeOwnershipService,
    PaperRuntimeRunnerService,
)
from el_psy_quant.persistence import (
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStorageFailureError,
    SqlAlchemyPaperExecutionRepository,
    SqlAlchemyPaperRuntimeRepository,
)
from test_paper_execution_persistence import _fixture, _migrate, _step_command
from test_paper_runtime_lifecycle import _diverge_account
from test_paper_runtime_persistence import AUDIT


@dataclass
class _Clock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


def _runner_fixture(path, monkeypatch, *, lease: timedelta = timedelta(minutes=10)):
    _migrate(path, monkeypatch, "head")
    engine, factory, create_order_command = _fixture(path)
    clock = _Clock(AUDIT + timedelta(hours=1))
    execution = PaperExecutionApplicationService(session_factory=factory, clock=clock)
    order = execution.create_order(create_order_command).result
    lifecycle = PaperRuntimeLifecycleService(session_factory=factory, clock=clock)
    created = lifecycle.create_runtime(
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        logical_actor="stable-paper-runtime",
        runtime_policy_id="durable-runtime-v1",
        runtime_policy_version=1,
        command_idempotency_key="create-runtime-s221",
        command_actor="founder",
    ).runtime
    started = lifecycle.start_runtime(
        runtime_id=created.runtime_id,
        runtime_binding_digest=created.runtime_binding_digest,
        expected_runtime_version=created.row_version,
        command_idempotency_key="start-runtime-s221",
        command_actor="founder",
    ).runtime
    ownership = PaperRuntimeOwnershipService(
        session_factory=factory,
        lease_duration=lease,
        clock=clock,
    )
    claim = ownership.claim_runtime(
        runtime_id=started.runtime_id, owner_id="worker-s221"
    ).runtime
    runner = PaperRuntimeRunnerService(
        session_factory=factory,
        execution_service=execution,
        ownership_service=ownership,
        clock=clock,
    )
    return engine, factory, order, lifecycle, ownership, runner, clock, claim


def _read(factory, runtime_id):
    with factory() as session:
        runtime = SqlAlchemyPaperRuntimeRepository(session=session)
        execution = SqlAlchemyPaperExecutionRepository(session=session)
        stored = runtime.get_runtime(runtime_id=runtime_id)
        assert stored is not None
        return (
            stored,
            runtime.list_all_work(runtime_id=runtime_id),
            runtime.list_checkpoints(runtime_id=runtime_id),
            runtime.list_all_events(runtime_id=runtime_id),
            execution.load_historical_history(
                execution_order_id=stored.execution_order_id
            ),
        )


def _run_one(runner, claim):
    return runner.run_one_claimed_iteration(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )


def test_phase_a_work_commits_before_exact_m34_step_and_phase_c_observes_no_fill(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "phases.sqlite3", monkeypatch)
    )
    called = []
    original = runner._execution_service.step_order

    def inspected_step(command):
        stored, work, checkpoints, events, history = _read(factory, claim.runtime_id)
        assert stored.observed_state == "running"
        assert len(work) == 1
        assert checkpoints == ()
        assert history.attempts == ()
        assert command.expected_execution_version == work[0].expected_execution_version
        assert command.command_idempotency_key == work[0].m34_step_idempotency_key
        assert command.actor == work[0].m34_step_actor == stored.logical_actor
        assert command.actor != claim.owner_id
        assert [event.event_type for event in events].count("work_created") == 1
        called.append(command.command_idempotency_key)
        return original(command)

    monkeypatch.setattr(runner._execution_service, "step_order", inspected_step)
    result = _run_one(runner, claim)
    stored, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "running"
    assert called == [work[0].m34_step_idempotency_key]
    assert result.checkpoint == checkpoints[0]
    assert checkpoints[0].fill_id is None
    assert len(history.attempts) == 1
    assert history.attempts[0].post_step_cursor.position == 5
    assert [event.event_type for event in events].count("work_observed") == 1
    assert stored.owner_id == claim.owner_id
    assert stored.fencing_token == claim.fencing_token
    assert stored.heartbeat_at == result.runtime.heartbeat_at
    engine.dispose()


def test_loop_observes_fill_settlement_completion_then_releases_claim(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "complete.sqlite3", monkeypatch)
    )
    result = runner.run_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
        iteration_budget=3,
    )
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "completed"
    assert result.iterations == 2
    assert runtime.observed_state == "completed"
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == len(history.attempts) == 2
    assert checkpoints[0].fill_id is None
    assert checkpoints[1].fill_id == history.fills[0].fill_id
    assert (
        checkpoints[1].settlement_link_id
        == history.settlement_links[0].settlement_link_id
    )
    assert history.state.terminal
    assert [event.event_type for event in events].count("work_created") == 2
    assert [event.event_type for event in events].count("work_observed") == 2
    assert [event.event_type for event in events].count("runtime_completed") == 1
    assert [event.event_type for event in events].count("claim_released") == 1
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_account_events "
                    "WHERE event_type='execution_fill_posted'"
                )
            )
            == 1
        )
        assert (
            connection.scalar(
                text(
                    "SELECT position FROM market_data_replays "
                    "WHERE replay_id=:replay_id"
                ),
                {"replay_id": order.market_handoff_reference.replay_id},
            )
            == 6
        )
    engine.dispose()


def test_stop_before_step_creates_no_work_or_attempt_and_releases_claim(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "stop-before.sqlite3", monkeypatch)
    )
    stopped = lifecycle.stop_runtime(
        runtime_id=claim.runtime_id,
        runtime_binding_digest=claim.runtime_binding_digest,
        expected_runtime_version=claim.row_version,
        command_idempotency_key="stop-before-step-s221",
        command_actor="founder",
    ).runtime
    result = _run_one(runner, claim)
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert stopped.desired_state == "stopped"
    assert result.outcome == "stopped"
    assert runtime.observed_state == "stopped"
    assert runtime.owner_id is None
    assert work == checkpoints == history.attempts == ()
    engine.dispose()


def test_stop_after_work_commit_but_before_step_keeps_work_without_attempt(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "stop-after-work.sqlite3", monkeypatch)
    )
    original = runner._confirm_step_entry

    def stop_then_confirm(**kwargs):
        runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
        assert len(work) == 1
        assert checkpoints == history.attempts == ()
        lifecycle.stop_runtime(
            runtime_id=runtime.runtime_id,
            runtime_binding_digest=runtime.runtime_binding_digest,
            expected_runtime_version=runtime.row_version,
            command_idempotency_key="stop-after-work-s221",
            command_actor="founder",
        )
        return original(**kwargs)

    monkeypatch.setattr(runner, "_confirm_step_entry", stop_then_confirm)
    result = _run_one(runner, claim)
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "stopped"
    assert runtime.owner_id is None
    assert len(work) == 1
    assert checkpoints == history.attempts == ()
    assert [event.event_type for event in events].count("work_created") == 1
    assert [event.event_type for event in events].count("work_observed") == 0
    engine.dispose()


def test_pre_step_requires_exact_active_owner_and_fence_without_mutation(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "pre-step-fence.sqlite3", monkeypatch)
    )
    for owner, fence in (
        ("other-worker", claim.fencing_token),
        (claim.owner_id, claim.fencing_token + 1),
    ):
        with pytest.raises(PaperRuntimeClaimMismatchError):
            runner.run_one_claimed_iteration(
                runtime_id=claim.runtime_id,
                owner_id=owner,
                fencing_token=fence,
            )
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert runtime == claim
    assert work == checkpoints == history.attempts == ()
    engine.dispose()


def test_work_and_work_created_roll_back_together_on_event_failure(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "work-rollback.sqlite3", monkeypatch)
    )
    original = SqlAlchemyPaperRuntimeRepository.append_event

    def fail_work_event(self, *, event):
        if event.event_type == "work_created":
            raise RuntimeError("simulated work event failure")
        return original(self, event=event)

    monkeypatch.setattr(
        SqlAlchemyPaperRuntimeRepository, "append_event", fail_work_event
    )
    with pytest.raises(RuntimeError, match="simulated work event failure"):
        _run_one(runner, claim)
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert runtime == claim
    assert work == checkpoints == history.attempts == ()
    assert [event.event_type for event in events].count("work_created") == 0
    engine.dispose()


def test_stop_racing_entered_step_observes_it_then_stops_without_next_work(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "stop-in-flight.sqlite3", monkeypatch)
    )
    original = runner._execution_service.step_order

    def step_then_stop(command):
        committed = original(command)
        runtime, *_ = _read(factory, claim.runtime_id)
        lifecycle.stop_runtime(
            runtime_id=runtime.runtime_id,
            runtime_binding_digest=runtime.runtime_binding_digest,
            expected_runtime_version=runtime.row_version,
            command_idempotency_key="stop-in-flight-s221",
            command_actor="founder",
        )
        return committed

    monkeypatch.setattr(runner._execution_service, "step_order", step_then_stop)
    result = _run_one(runner, claim)
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "stopped"
    assert runtime.desired_state == runtime.observed_state == "stopped"
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert history.state.terminal is False
    engine.dispose()


def test_stop_after_observation_prevents_heartbeat_and_releases_claim(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "stop-before-heartbeat.sqlite3", monkeypatch)
    )
    original = ownership.assert_active_runtime_claim
    calls = 0

    def stop_on_post_observation_guard(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            runtime, work, checkpoints, _events, history = _read(
                factory, claim.runtime_id
            )
            assert len(work) == len(checkpoints) == len(history.attempts) == 1
            lifecycle.stop_runtime(
                runtime_id=runtime.runtime_id,
                runtime_binding_digest=runtime.runtime_binding_digest,
                expected_runtime_version=runtime.row_version,
                command_idempotency_key="stop-before-heartbeat-s221",
                command_actor="founder",
            )
        return original(**kwargs)

    monkeypatch.setattr(
        ownership, "assert_active_runtime_claim", stop_on_post_observation_guard
    )
    result = _run_one(runner, claim)
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert result.outcome == "stopped"
    assert calls == 2
    assert runtime.desired_state == runtime.observed_state == "stopped"
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    engine.dispose()


def test_m34_failure_leaves_stable_work_durable_and_retry_reuses_exact_identity(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "retry.sqlite3", monkeypatch)
    )
    original = runner._execution_service.step_order

    def fail(_command):
        raise PaperExecutionStorageFailureError()

    monkeypatch.setattr(runner._execution_service, "step_order", fail)
    with pytest.raises(PaperExecutionStorageFailureError):
        _run_one(runner, claim)
    runtime, first_work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert runtime.observed_state == "running"
    assert len(first_work) == 1
    assert checkpoints == history.attempts == ()
    assert [event.event_type for event in events].count("work_created") == 1

    monkeypatch.setattr(runner._execution_service, "step_order", original)
    result = _run_one(runner, claim)
    _runtime, second_work, checkpoints, events, history = _read(
        factory, claim.runtime_id
    )
    assert result.outcome == "running"
    assert second_work == first_work
    assert (
        result.work.m34_step_idempotency_key == first_work[0].m34_step_idempotency_key
    )
    assert len(checkpoints) == len(history.attempts) == 1
    assert [event.event_type for event in events].count("work_created") == 1
    engine.dispose()


def test_committed_but_unobserved_step_requires_s222_and_never_starts_next_step(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "missing-observation.sqlite3", monkeypatch)
    )
    original = runner._execution_service.step_order

    def commit_then_lose_return(command):
        original(command)
        raise RuntimeError("simulated process loss after M34 commit")

    monkeypatch.setattr(
        runner._execution_service, "step_order", commit_then_lose_return
    )
    with pytest.raises(RuntimeError, match="simulated process loss"):
        _run_one(runner, claim)
    monkeypatch.setattr(runner._execution_service, "step_order", original)
    with pytest.raises(PaperRuntimeObservationRequiredError):
        _run_one(runner, claim)
    _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert len(work) == len(history.attempts) == 1
    assert checkpoints == ()
    assert [event.event_type for event in events].count("work_observed") == 0
    engine.dispose()


@pytest.mark.parametrize("loss", ("lease", "fence"))
def test_post_step_lease_or_fence_loss_preserves_m34_and_writes_no_m35_observation(
    tmp_path, monkeypatch, loss
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(
            tmp_path / f"post-step-{loss}.sqlite3",
            monkeypatch,
            lease=timedelta(seconds=10),
        )
    )
    original = runner._execution_service.step_order

    def lose_authority(command):
        committed = original(command)
        clock.value += timedelta(seconds=10)
        if loss == "fence":
            ownership.claim_runtime(
                runtime_id=claim.runtime_id, owner_id="replacement-worker"
            )
        return committed

    monkeypatch.setattr(runner._execution_service, "step_order", lose_authority)
    expected_error = (
        PaperRuntimeLeaseExpiredError
        if loss == "lease"
        else PaperRuntimeClaimMismatchError
    )
    with pytest.raises(expected_error):
        _run_one(runner, claim)
    _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert len(work) == len(history.attempts) == 1
    assert checkpoints == ()
    assert [event.event_type for event in events].count("work_observed") == 0
    engine.dispose()


def test_same_claim_runners_converge_to_one_attempt_checkpoint_and_heartbeat(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "race.sqlite3", monkeypatch)
    )
    barrier = Barrier(2)
    original = runner._execution_service.step_order

    def racing_step(command):
        barrier.wait(timeout=10)
        return original(command)

    monkeypatch.setattr(runner._execution_service, "step_order", racing_step)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = tuple(pool.submit(_run_one, runner, claim) for _index in range(2))
        results = tuple(future.result(timeout=15) for future in futures)
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert {result.outcome for result in results} == {"running"}
    assert {result.work.work_id for result in results} == {work[0].work_id}
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert len(history.fills) == len(history.settlement_links) == 0
    assert [event.event_type for event in events].count("work_created") == 1
    assert [event.event_type for event in events].count("work_observed") == 1
    assert runtime.owner_id == claim.owner_id
    assert runtime.fencing_token == claim.fencing_token
    engine.dispose()


def test_budget_exhaustion_leaves_running_claim_and_terminal_before_step_completes(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "budget.sqlite3", monkeypatch)
    )
    budgeted = runner.run_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
        iteration_budget=1,
    )
    assert budgeted.outcome == "iteration_budget_exhausted"
    runtime, *_ = _read(factory, claim.runtime_id)
    assert runtime.desired_state == runtime.observed_state == "running"
    assert runtime.owner_id == claim.owner_id

    direct = PaperExecutionApplicationService(
        session_factory=factory, clock=lambda: AUDIT + timedelta(hours=3)
    )
    direct.step_order(_step_command(order, version=1, key="direct-terminal-s221"))
    completed = _run_one(runner, claim)
    runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert completed.outcome == "completed"
    assert runtime.owner_id is None
    assert len(work) == len(checkpoints) == 1
    assert len(history.attempts) == 2
    assert [event.event_type for event in events].count("runtime_completed") == 1
    engine.dispose()


def test_stale_live_continuation_refuses_before_work_creation(tmp_path, monkeypatch):
    engine, factory, order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "stale.sqlite3", monkeypatch)
    )
    _diverge_account(factory, order)
    with pytest.raises(PaperExecutionReconciliationRequiredError):
        _run_one(runner, claim)
    _runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert work == checkpoints == history.attempts == ()
    engine.dispose()


def test_post_step_live_divergence_is_observed_before_next_step_refuses(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "post-step-live-divergence.sqlite3", monkeypatch)
    )
    original = runner._execution_service.step_order
    step_calls = []

    def step_then_diverge_account(command):
        _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
        assert len(work) == 1
        assert work[0].expected_execution_version == command.expected_execution_version
        assert checkpoints == history.attempts == ()
        assert [event.event_type for event in events].count("work_created") == 1

        committed = original(command)
        _runtime, committed_work, checkpoints, _events, history = _read(
            factory, claim.runtime_id
        )
        assert committed_work == work
        assert checkpoints == ()
        assert len(history.attempts) == 1
        assert history.attempts[0] == committed.result.step_result.attempt
        assert history.attempts[0].execution_version_after == 1
        assert history.attempts[0].post_step_cursor.position == 5
        step_calls.append(command.command_idempotency_key)
        _diverge_account(factory, order)
        return committed

    monkeypatch.setattr(
        runner._execution_service, "step_order", step_then_diverge_account
    )
    observed = _run_one(runner, claim)
    _runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
    assert observed.outcome == "running"
    assert observed.checkpoint == checkpoints[0]
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    assert checkpoints[0].attempt_id == history.attempts[0].attempt_id
    assert checkpoints[0].attempt_digest == history.attempts[0].attempt_digest
    assert checkpoints[0].post_cursor_position == 5
    assert history.fills == history.settlement_links == ()
    assert [event.event_type for event in events].count("work_created") == 1
    assert [event.event_type for event in events].count("work_observed") == 1
    assert len(step_calls) == 1

    with pytest.raises(PaperExecutionReconciliationRequiredError) as stale:
        _run_one(runner, claim)
    assert type(stale.value) is PaperExecutionReconciliationRequiredError

    _runtime, later_work, later_checkpoints, later_events, later_history = _read(
        factory, claim.runtime_id
    )
    assert later_work == work
    assert later_checkpoints == checkpoints
    assert later_history.attempts == history.attempts
    assert later_history.fills == later_history.settlement_links == ()
    assert [event.event_type for event in later_events].count("work_created") == 1
    assert [event.event_type for event in later_events].count("work_observed") == 1
    assert len(step_calls) == 1
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM paper_account_events "
                    "WHERE event_type='execution_fill_posted'"
                )
            )
            == 0
        )
        assert (
            connection.scalar(
                text(
                    "SELECT position FROM market_data_replays "
                    "WHERE replay_id=:replay_id"
                ),
                {"replay_id": order.market_handoff_reference.replay_id},
            )
            == 5
        )
    engine.dispose()
