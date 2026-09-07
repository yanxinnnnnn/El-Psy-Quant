"""Sprint 225 deterministic concurrency, contention, and isolation evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sqlite3
from datetime import timedelta
from threading import Barrier, Event

import pytest
from sqlalchemy import text

from el_psy_quant.application import (
    PaperExecutionApplicationService,
    PaperRuntimeClaimMismatchError,
    PaperRuntimeLifecycleService,
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeOwnershipService,
    PaperRuntimeRecoveryService,
    PaperRuntimeRunnerService,
)
from el_psy_quant.application.paper_runtime_inspection import (
    PaperRuntimeInspectionService,
)
from el_psy_quant.persistence import (
    PaperRuntimeStorageBusyError,
    SqlAlchemyPaperExecutionRepository,
    SqlAlchemyPaperRuntimeRepository,
)
from test_paper_execution_persistence import AUDIT, _fixture, _migrate
from test_paper_runtime_runner import _Clock, _read, _runner_fixture


_AUTHORITY_TABLES = (
    "paper_runtimes",
    "paper_runtime_work",
    "paper_runtime_checkpoints",
    "paper_runtime_events",
    "paper_runtime_command_receipts",
    "paper_execution_orders",
    "paper_execution_attempts",
    "paper_execution_fills",
    "paper_execution_settlement_links",
    "paper_execution_command_receipts",
    "paper_account_events",
    "market_data_replays",
)


def _authority_snapshot(
    engine,
) -> tuple[tuple[str, tuple[tuple[object, ...], ...]], ...]:
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
            for table in _AUTHORITY_TABLES
        )


def _event_count(factory, runtime_id: str, event_type: str) -> int:
    with factory() as session:
        return sum(
            event.event_type == event_type
            for event in SqlAlchemyPaperRuntimeRepository(
                session=session
            ).list_all_events(runtime_id=runtime_id)
        )


def _start_runtime(
    *,
    factory,
    execution,
    lifecycle,
    ownership,
    order,
    key: str,
):
    created = lifecycle.create_runtime(
        execution_order_id=order.execution_order_id,
        execution_order_digest=order.execution_order_digest,
        logical_actor=f"stable-actor-{key}",
        runtime_policy_id="durable-runtime-v1",
        runtime_policy_version=1,
        command_idempotency_key=f"create-{key}",
        command_actor="founder",
    ).runtime
    started = lifecycle.start_runtime(
        runtime_id=created.runtime_id,
        runtime_binding_digest=created.runtime_binding_digest,
        expected_runtime_version=created.row_version,
        command_idempotency_key=f"start-{key}",
        command_actor="founder",
    ).runtime
    claim = ownership.claim_runtime(
        runtime_id=started.runtime_id, owner_id=f"owner-{key}"
    ).runtime
    return claim, PaperRuntimeRunnerService(
        session_factory=factory,
        execution_service=execution,
        ownership_service=ownership,
        clock=ownership._clock,
    )


def test_expired_takeover_race_has_one_higher_fence_winner_and_fences_old_owner(
    tmp_path, monkeypatch
):
    engine, factory, _order, _lifecycle, ownership, runner, clock, old = (
        _runner_fixture(
            tmp_path / "takeover-race.sqlite3",
            monkeypatch,
            lease=timedelta(seconds=10),
        )
    )
    assert old.lease_expires_at is not None
    clock.value = old.lease_expires_at
    barrier = Barrier(2)

    def take_over(owner: str):
        barrier.wait(timeout=10)
        try:
            return ownership.claim_runtime(runtime_id=old.runtime_id, owner_id=owner)
        except PaperRuntimeOwnershipBusyError as exc:
            return exc

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(
                pool.submit(take_over, owner) for owner in ("takeover-a", "takeover-b")
            )
            outcomes = tuple(future.result(timeout=15) for future in futures)
        winners = tuple(item for item in outcomes if not isinstance(item, Exception))
        losers = tuple(item for item in outcomes if isinstance(item, Exception))
        assert len(winners) == len(losers) == 1
        assert type(losers[0]) is PaperRuntimeOwnershipBusyError
        replacement = winners[0].runtime
        assert replacement.fencing_token == old.fencing_token + 1
        assert _event_count(factory, old.runtime_id, "claim_taken_over") == 1

        before = _authority_snapshot(engine)
        stale_operations = (
            lambda: ownership.renew_runtime_claim(
                runtime_id=old.runtime_id,
                owner_id=old.owner_id,
                fencing_token=old.fencing_token,
            ),
            lambda: ownership.release_runtime_claim(
                runtime_id=old.runtime_id,
                owner_id=old.owner_id,
                fencing_token=old.fencing_token,
            ),
            lambda: runner.run_one_claimed_iteration(
                runtime_id=old.runtime_id,
                owner_id=old.owner_id,
                fencing_token=old.fencing_token,
            ),
        )
        for operation in stale_operations:
            with pytest.raises(PaperRuntimeClaimMismatchError):
                operation()
            assert _authority_snapshot(engine) == before
    finally:
        engine.dispose()


def test_takeover_while_old_owner_is_inside_step_converges_one_canonical_result(
    tmp_path, monkeypatch
):
    engine, factory, order, _lifecycle, ownership, runner, clock, old = _runner_fixture(
        tmp_path / "in-step-takeover.sqlite3",
        monkeypatch,
        lease=timedelta(seconds=10),
    )
    entered = Event()
    continue_step = Event()
    original_step = runner._execution_service.step_order

    def gated_step(command):
        entered.set()
        assert continue_step.wait(timeout=10)
        return original_step(command)

    monkeypatch.setattr(runner._execution_service, "step_order", gated_step)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                runner.run_one_claimed_iteration,
                runtime_id=old.runtime_id,
                owner_id=old.owner_id,
                fencing_token=old.fencing_token,
            )
            assert entered.wait(timeout=10)
            assert old.lease_expires_at is not None
            clock.value = old.lease_expires_at
            replacement = ownership.claim_runtime(
                runtime_id=old.runtime_id, owner_id="replacement-owner"
            ).runtime
            continue_step.set()
            with pytest.raises(PaperRuntimeClaimMismatchError):
                future.result(timeout=15)

        runtime, work, checkpoints, events, history = _read(factory, old.runtime_id)
        assert runtime == replacement
        assert len(work) == len(history.attempts) == 1
        assert checkpoints == ()
        assert [event.event_type for event in events].count("work_created") == 1
        assert [event.event_type for event in events].count("work_observed") == 0
        assert len(history.fills) == len(history.settlement_links) == 0
        with factory() as session:
            receipt = SqlAlchemyPaperExecutionRepository(session=session).get_receipt(
                namespace="step_paper_execution_order",
                command_idempotency_key=work[0].m34_step_idempotency_key,
            )
        assert receipt is not None
        assert receipt.attempt_id == history.attempts[0].attempt_id

        monkeypatch.setattr(runner._execution_service, "step_order", original_step)
        recovered = PaperRuntimeRecoveryService(
            session_factory=factory,
            execution_service=runner._execution_service,
            ownership_service=ownership,
            clock=clock,
        ).reconcile_claimed_runtime(
            runtime_id=replacement.runtime_id,
            owner_id=replacement.owner_id,
            fencing_token=replacement.fencing_token,
        )
        assert recovered.outcome == "runnable"
        final_runtime, final_work, final_checkpoints, final_events, final_history = (
            _read(factory, old.runtime_id)
        )
        assert final_runtime.fencing_token == old.fencing_token + 1
        assert final_work == work
        assert len(final_checkpoints) == len(final_history.attempts) == 1
        assert [event.event_type for event in final_events].count("work_observed") == 1
        assert final_history.attempts == history.attempts
        with engine.connect() as connection:
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

        before_stale_retry = _authority_snapshot(engine)
        with pytest.raises(PaperRuntimeClaimMismatchError):
            runner.run_one_claimed_iteration(
                runtime_id=old.runtime_id,
                owner_id=old.owner_id,
                fencing_token=old.fencing_token,
            )
        assert _authority_snapshot(engine) == before_stale_retry
    finally:
        continue_step.set()
        engine.dispose()


def test_gated_m34_step_allows_independent_stop_without_outer_m35_transaction(
    tmp_path, monkeypatch
):
    engine, factory, _order, lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(tmp_path / "transaction-boundary.sqlite3", monkeypatch)
    )
    entered = Event()
    continue_step = Event()
    original_step = runner._execution_service.step_order

    def gated_step(command):
        entered.set()
        assert continue_step.wait(timeout=10)
        return original_step(command)

    monkeypatch.setattr(runner._execution_service, "step_order", gated_step)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                runner.run_one_claimed_iteration,
                runtime_id=claim.runtime_id,
                owner_id=claim.owner_id,
                fencing_token=claim.fencing_token,
            )
            assert entered.wait(timeout=10)
            current = _read(factory, claim.runtime_id)[0]
            stopped = lifecycle.stop_runtime(
                runtime_id=current.runtime_id,
                runtime_binding_digest=current.runtime_binding_digest,
                expected_runtime_version=current.row_version,
                command_idempotency_key="stop-inside-gated-step",
                command_actor="founder",
            ).runtime
            assert stopped.desired_state == "stopped"
            continue_step.set()
            result = future.result(timeout=15)
        runtime, work, checkpoints, events, history = _read(factory, claim.runtime_id)
        assert result.outcome == "stopped"
        assert runtime.desired_state == runtime.observed_state == "stopped"
        assert runtime.owner_id is None
        assert len(work) == len(checkpoints) == len(history.attempts) == 1
        assert [event.event_type for event in events].count("stop_requested") == 1
        assert [event.event_type for event in events].count("work_observed") == 1
    finally:
        continue_step.set()
        engine.dispose()


def test_real_sqlite_m35_contention_has_no_partial_write_and_exact_retry(
    tmp_path, monkeypatch
):
    path = tmp_path / "m35-contention.sqlite3"
    engine, _factory, _order, lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    command = {
        "runtime_id": claim.runtime_id,
        "runtime_binding_digest": claim.runtime_binding_digest,
        "expected_runtime_version": claim.row_version,
        "command_idempotency_key": "contended-stop",
        "command_actor": "founder",
    }
    blocker = sqlite3.connect(path, timeout=0, isolation_level=None)
    try:
        before = _authority_snapshot(engine)
        blocker.execute("BEGIN IMMEDIATE")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lifecycle.stop_runtime, **command)
            with pytest.raises(PaperRuntimeStorageBusyError):
                future.result(timeout=10)
        assert _authority_snapshot(engine) == before
        blocker.rollback()
        committed = lifecycle.stop_runtime(**command)
        assert committed.replayed is False
        replayed = lifecycle.stop_runtime(**command)
        assert replayed.replayed is True
        assert replayed.runtime == committed.runtime
        assert _event_count(_factory, claim.runtime_id, "stop_requested") == 1
    finally:
        try:
            blocker.rollback()
        finally:
            blocker.close()
            engine.dispose()


def test_two_runtime_execution_chains_and_bounded_inspection_remain_isolated(
    tmp_path, monkeypatch
):
    path = tmp_path / "two-runtime-isolation.sqlite3"
    _migrate(path, monkeypatch, "head")
    engine, factory, command_a = _fixture(path, fixture_id="s225-a")
    other_engine, _other_factory, command_b = _fixture(
        path, fixture_id="s225-b", calendar_version=2
    )
    other_engine.dispose()
    clock = _Clock(AUDIT + timedelta(hours=1))
    execution = PaperExecutionApplicationService(session_factory=factory, clock=clock)
    lifecycle = PaperRuntimeLifecycleService(session_factory=factory, clock=clock)
    ownership = PaperRuntimeOwnershipService(
        session_factory=factory,
        lease_duration=timedelta(minutes=10),
        clock=clock,
    )
    try:
        order_a = execution.create_order(command_a).result
        order_b = execution.create_order(command_b).result
        claim_a, runner_a = _start_runtime(
            factory=factory,
            execution=execution,
            lifecycle=lifecycle,
            ownership=ownership,
            order=order_a,
            key="a",
        )
        claim_b, runner_b = _start_runtime(
            factory=factory,
            execution=execution,
            lifecycle=lifecycle,
            ownership=ownership,
            order=order_b,
            key="b",
        )

        completed_a = runner_a.run_claimed_runtime(
            runtime_id=claim_a.runtime_id,
            owner_id=claim_a.owner_id,
            fencing_token=claim_a.fencing_token,
            iteration_budget=3,
        )
        untouched_b = _read(factory, claim_b.runtime_id)
        assert completed_a.outcome == "completed"
        assert untouched_b[0] == claim_b
        assert untouched_b[1] == untouched_b[2] == untouched_b[4].attempts == ()

        completed_b = runner_b.run_claimed_runtime(
            runtime_id=claim_b.runtime_id,
            owner_id=claim_b.owner_id,
            fencing_token=claim_b.fencing_token,
            iteration_budget=3,
        )
        assert completed_b.outcome == "completed"
        histories = {}
        for claim, order in ((claim_a, order_a), (claim_b, order_b)):
            runtime, work, checkpoints, events, history = _read(
                factory, claim.runtime_id
            )
            histories[claim.runtime_id] = history
            assert runtime.execution_order_id == order.execution_order_id
            assert runtime.account_id == order.account_id
            assert runtime.replay_id == order.market_handoff_reference.replay_id
            assert runtime.owner_id is None
            assert len(work) == len(checkpoints) == len(history.attempts) == 2
            assert len(history.fills) == len(history.settlement_links) == 1
            assert {item.runtime_id for item in work} == {runtime.runtime_id}
            assert {item.runtime_id for item in checkpoints} == {runtime.runtime_id}
            assert [item.event_type for item in events].count("work_created") == 2
            assert [item.event_type for item in events].count("work_observed") == 2
            with engine.connect() as connection:
                assert (
                    connection.scalar(
                        text(
                            "SELECT COUNT(*) FROM paper_account_events "
                            "WHERE account_id=:account_id "
                            "AND event_type='execution_fill_posted'"
                        ),
                        {"account_id": order.account_id},
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

        assert (
            histories[claim_a.runtime_id].attempts
            != histories[claim_b.runtime_id].attempts
        )
        inspection = PaperRuntimeInspectionService(session_factory=factory, clock=clock)
        before_reads = _authority_snapshot(engine)
        page_a = inspection.list_work(runtime_id=claim_a.runtime_id, limit=1)
        assert page_a.has_more and len(page_a.items) == 1
        next_a = inspection.list_work(
            runtime_id=claim_a.runtime_id,
            limit=1,
            cursor_work_id=page_a.items[0].work_id,
            cursor_expected_execution_version=(
                page_a.items[0].expected_execution_version
            ),
        )
        assert not next_a.has_more and len(next_a.items) == 1
        assert {item.work_id for item in page_a.items + next_a.items} == {
            item.work_id for item in _read(factory, claim_a.runtime_id)[1]
        }
        with pytest.raises(ValueError, match="not canonical"):
            inspection.list_work(
                runtime_id=claim_b.runtime_id,
                limit=1,
                cursor_work_id=page_a.items[0].work_id,
                cursor_expected_execution_version=(
                    page_a.items[0].expected_execution_version
                ),
            )
        for claim in (claim_a, claim_b):
            assert (
                inspection.get_health(runtime_id=claim.runtime_id).lease_status
                == "unowned"
            )
            assert (
                inspection.reconcile_runtime(runtime_id=claim.runtime_id).status
                == "coherent_terminal"
            )
            inspection.list_audit(runtime_id=claim.runtime_id, limit=1)
            inspection.list_checkpoints(runtime_id=claim.runtime_id, limit=1)
        assert _authority_snapshot(engine) == before_reads
    finally:
        engine.dispose()
