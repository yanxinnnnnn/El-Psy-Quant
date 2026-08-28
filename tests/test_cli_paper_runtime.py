"""Focused Sprint 223 dedicated Paper Runtime process composition tests."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from el_psy_quant import cli
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeClaimMismatchError,
    PaperRuntimeLeaseExpiredError,
    PaperRuntimeOwnershipService,
    PaperRuntimeRecoveryService,
)
from el_psy_quant.persistence import (
    PaperExecutionConcurrencyConflictError,
    PaperExecutionReconciliationRequiredError,
    PaperExecutionStorageBusyError,
    PaperExecutionStorageFailureError,
    PaperRuntimeConcurrencyConflictError,
    PaperRuntimePersistenceCorruptionError,
)
from test_paper_runtime_runner import _read, _runner_fixture
from test_paper_runtime_recovery import (
    _canonical_side_effects,
    _leave_work_without_attempt,
    _recovery,
)


def test_cli_recovery_continues_with_exact_fence_and_iteration_budget(
    tmp_path: Path, monkeypatch
) -> None:
    engine, factory, order, _lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(tmp_path / "runtime-cli.sqlite3", monkeypatch)
    )
    engine.dispose()
    fences: list[int] = []
    original = cli.PaperRuntimeRunnerService.run_claimed_runtime

    def recording(self, **kwargs):
        fences.append(kwargs["fencing_token"])
        return original(self, **kwargs)

    monkeypatch.setattr(cli.PaperRuntimeRunnerService, "run_claimed_runtime", recording)
    result = cli.run_paper_runtime_process(
        database_path=tmp_path / "runtime-cli.sqlite3",
        runtime_id=claim.runtime_id,
        owner_id="runtime-cli-worker",
        lease_seconds=30,
        iteration_budget=1,
    )
    assert result.recovery_outcome == "runnable"
    assert result.runner_outcome == "iteration_budget_exhausted"
    assert result.iterations == 1
    assert fences == [result.fencing_token]
    runtime, work, checkpoints, _events, history = _read(factory, claim.runtime_id)
    assert runtime.owner_id is None
    assert runtime.claimed_at is runtime.heartbeat_at is runtime.lease_expires_at is None
    assert runtime.desired_state == runtime.observed_state == "running"
    assert runtime.fencing_token == result.fencing_token
    assert len(work) == len(checkpoints) == len(history.attempts) == 1
    first_effects = _canonical_side_effects(
        factory, claim.runtime_id, order.market_handoff_reference.replay_id
    )

    second = cli.run_paper_runtime_process(
        database_path=tmp_path / "runtime-cli.sqlite3",
        runtime_id=claim.runtime_id,
        owner_id="runtime-cli-second-worker",
        lease_seconds=30,
        iteration_budget=1,
    )
    assert second.recovery_outcome == "runnable"
    assert second.runner_outcome == "completed"
    assert second.fencing_token == result.fencing_token + 1
    later_runtime, later_work, later_checkpoints, _later_events, later_history = _read(
        factory, claim.runtime_id
    )
    assert later_runtime.owner_id is None
    assert len(later_work) == len(later_checkpoints) == len(later_history.attempts) == 2
    assert len(later_history.fills) == len(later_history.settlement_links) == 1
    second_effects = _canonical_side_effects(
        factory, claim.runtime_id, order.market_handoff_reference.replay_id
    )
    assert second_effects[0] == first_effects[0] + 1
    assert second_effects[1] == first_effects[1] + 1
    assert second_effects[2] == first_effects[2] + 1
    assert second_effects[3] == first_effects[3] + 1
    assert second_effects[4] == first_effects[4] + 1


def test_cli_stopped_runtime_does_not_call_runner(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "runtime-cli-stopped.sqlite3"
    engine, factory, _order, lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    current = _read(factory, claim.runtime_id)[0]
    lifecycle.stop_runtime(
        runtime_id=current.runtime_id,
        runtime_binding_digest=current.runtime_binding_digest,
        expected_runtime_version=current.row_version,
        command_idempotency_key="runtime-cli-stop",
        command_actor="founder",
    )
    engine.dispose()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("stopped recovery must not run S221")

    monkeypatch.setattr(cli.PaperRuntimeRunnerService, "run_claimed_runtime", forbidden)
    result = cli.run_paper_runtime_process(
        database_path=path,
        runtime_id=claim.runtime_id,
        owner_id="runtime-cli-stop-worker",
    )
    assert result.recovery_outcome == "stopped"
    assert result.runner_outcome is None
    assert result.iterations == 0


def test_cli_process_output_is_sanitized_and_engine_is_disposed(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    disposed: list[bool] = []

    class Engine:
        def dispose(self):
            disposed.append(True)

    monkeypatch.setattr(cli, "verify_product_schema", lambda _path: None)
    monkeypatch.setattr(cli, "create_product_database_engine", lambda **_kwargs: Engine())
    monkeypatch.setattr(cli, "create_product_session_factory", lambda **_kwargs: object())
    monkeypatch.setattr(
        cli.PaperExecutionApplicationService,
        "__init__",
        lambda self, **_kwargs: (_ for _ in ()).throw(RuntimeError("C:/secret/db.sql")),
    )
    assert (
        cli.main(
            [
                "run-paper-runtime",
                "--database-path",
                str(tmp_path / "secret.sqlite3"),
                "--runtime-id",
                "prt_" + "0" * 64,
                "--owner-id",
                "worker",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: paper runtime process input is invalid\n"
    assert "secret" not in captured.err.lower()
    assert disposed == [True]


def test_http_and_cli_sources_preserve_execution_boundary() -> None:
    route_source = Path("src/el_psy_quant/api/routes/paper_runtimes.py").read_text(
        encoding="utf-8"
    )
    cli_source = Path("src/el_psy_quant/cli.py").read_text(encoding="utf-8")
    assert "run_claimed_runtime" not in route_source
    assert "PaperRuntimeRecoveryService" not in route_source
    assert ".step_order(" not in cli_source
    assert "recover_runtime(" in cli_source
    assert "run_claimed_runtime(" in cli_source


def test_cli_recovery_service_is_the_existing_s222_type() -> None:
    assert cli.PaperRuntimeRecoveryService is PaperRuntimeRecoveryService


def test_cli_active_foreign_claim_refuses_before_runner(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "runtime-cli-owned.sqlite3"
    engine, factory, _order, _lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    now = datetime.now(timezone.utc)
    foreign = PaperRuntimeOwnershipService(
        session_factory=factory,
        lease_duration=timedelta(days=1),
        clock=lambda: now,
    ).claim_runtime(runtime_id=claim.runtime_id, owner_id="active-foreign").runtime
    assert foreign.owner_id == "active-foreign"
    engine.dispose()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("active foreign claim must refuse before S221")

    monkeypatch.setattr(cli.PaperRuntimeRunnerService, "run_claimed_runtime", forbidden)
    assert (
        cli.main(
            [
                "run-paper-runtime",
                "--database-path",
                str(path),
                "--runtime-id",
                claim.runtime_id,
                "--owner-id",
                "competing-worker",
            ]
        )
        == 1
    )


def test_cli_recovery_reuses_pending_work_identity(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "runtime-cli-pending.sqlite3"
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    _leave_work_without_attempt(runner, claim, monkeypatch)
    before_runtime, before_work, *_ = _read(factory, claim.runtime_id)
    pending = before_work[0]
    assert before_runtime.lease_expires_at is not None
    assert before_runtime.lease_expires_at < datetime.now(timezone.utc)
    engine.dispose()
    result = cli.run_paper_runtime_process(
        database_path=path,
        runtime_id=claim.runtime_id,
        owner_id="pending-recovery-worker",
        iteration_budget=1,
    )
    assert result.recovery_outcome == "runnable"
    later_work = _read(factory, claim.runtime_id)[1]
    assert later_work[0] == pending
    assert later_work[0].m34_step_idempotency_key == pending.m34_step_idempotency_key
    assert later_work[0].m34_step_actor == pending.m34_step_actor
    assert later_work[0].expected_execution_version == pending.expected_execution_version
    assert result.fencing_token == before_runtime.fencing_token + 1


def test_cli_terminal_recovery_never_enters_runner_or_creates_following_work(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "runtime-cli-terminal.sqlite3"
    engine, factory, _order, _lifecycle, _ownership, runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    completed = runner.run_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
        iteration_budget=3,
    )
    assert completed.outcome == "completed"
    before = _read(factory, claim.runtime_id)
    engine.dispose()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("terminal recovery must not run S221")

    monkeypatch.setattr(cli.PaperRuntimeRunnerService, "run_claimed_runtime", forbidden)
    result = cli.run_paper_runtime_process(
        database_path=path,
        runtime_id=claim.runtime_id,
        owner_id="terminal-recovery-worker",
    )
    assert result.recovery_outcome == "completed"
    assert result.runner_outcome is None
    after = _read(factory, claim.runtime_id)
    assert after[1] == before[1]
    assert after[2] == before[2]
    assert after[4] == before[4]


def test_cli_blocked_recovery_never_enters_runner_or_creates_following_work(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "runtime-cli-blocked.sqlite3"
    engine, factory, _order, _lifecycle, ownership, runner, clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    recovery = _recovery(factory, ownership, runner, clock)

    def corrupt(**_kwargs):
        raise PaperRuntimePersistenceCorruptionError()

    monkeypatch.setattr(recovery, "_phase_r1_reconcile", corrupt)
    blocked = recovery.reconcile_claimed_runtime(
        runtime_id=claim.runtime_id,
        owner_id=claim.owner_id,
        fencing_token=claim.fencing_token,
    )
    assert blocked.outcome == "blocked"
    before = _read(factory, claim.runtime_id)
    engine.dispose()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("blocked recovery must not run S221")

    monkeypatch.setattr(cli.PaperRuntimeRunnerService, "run_claimed_runtime", forbidden)
    result = cli.run_paper_runtime_process(
        database_path=path,
        runtime_id=claim.runtime_id,
        owner_id="blocked-recovery-worker",
    )
    assert result.recovery_outcome == "blocked"
    assert result.runner_outcome is None
    after = _read(factory, claim.runtime_id)
    assert after[1] == before[1] == ()
    assert after[2] == before[2] == ()
    assert after[4] == before[4]


_SECRET_ERROR = "C:/private/runtime.sqlite3 SELECT secret FROM payload"


def _assert_sanitized_failure(capsys, *, expected_stderr: str) -> None:
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == expected_stderr + "\n"
    assert _SECRET_ERROR not in captured.err
    assert "traceback" not in captured.err.lower()
    assert "sqlite3" not in captured.err.lower()
    assert "select" not in captured.err.lower()
    assert "payload" not in captured.err.lower()


@pytest.mark.parametrize(
    "error_type",
    (PaperRuntimeClaimMismatchError, PaperRuntimeLeaseExpiredError),
)
def test_cli_budget_release_fencing_failures_are_fixed_and_sanitized(
    tmp_path: Path, monkeypatch, capsys, error_type: type[Exception]
) -> None:
    path = tmp_path / f"runtime-cli-{error_type.__name__}.sqlite3"
    engine, _factory, _order, _lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    engine.dispose()
    capsys.readouterr()

    def fail_release(*_args, **_kwargs):
        raise error_type(_SECRET_ERROR)

    monkeypatch.setattr(
        cli.PaperRuntimeOwnershipService, "release_runtime_claim", fail_release
    )
    assert (
        cli.main(
            [
                "run-paper-runtime",
                "--database-path",
                str(path),
                "--runtime-id",
                claim.runtime_id,
                "--owner-id",
                "fencing-failure-worker",
                "--iteration-budget",
                "1",
            ]
        )
        == 1
    )
    _assert_sanitized_failure(
        capsys, expected_stderr="error: paper runtime claim is no longer current"
    )


@pytest.mark.parametrize(
    ("error_type", "expected_stderr"),
    (
        (
            PaperExecutionReconciliationRequiredError,
            "error: paper runtime live continuation is stale",
        ),
        (
            PaperRuntimeConcurrencyConflictError,
            "error: paper runtime operation conflicts with current authority",
        ),
        (
            PaperExecutionConcurrencyConflictError,
            "error: paper runtime operation conflicts with current authority",
        ),
        (
            PaperExecutionStorageBusyError,
            "error: paper runtime storage is temporarily unavailable",
        ),
        (
            PaperExecutionStorageFailureError,
            "error: paper runtime authority is unavailable",
        ),
    ),
)
def test_cli_runner_operational_failures_are_fixed_and_sanitized(
    tmp_path: Path,
    monkeypatch,
    capsys,
    error_type: type[Exception],
    expected_stderr: str,
) -> None:
    path = tmp_path / f"runtime-cli-{error_type.__name__}.sqlite3"
    engine, _factory, _order, _lifecycle, _ownership, _runner, _clock, claim = (
        _runner_fixture(path, monkeypatch)
    )
    engine.dispose()
    capsys.readouterr()

    def fail_runner(*_args, **_kwargs):
        raise error_type(_SECRET_ERROR)

    monkeypatch.setattr(
        cli.PaperRuntimeRunnerService, "run_claimed_runtime", fail_runner
    )
    assert (
        cli.main(
            [
                "run-paper-runtime",
                "--database-path",
                str(path),
                "--runtime-id",
                claim.runtime_id,
                "--owner-id",
                "runner-failure-worker",
            ]
        )
        == 1
    )
    _assert_sanitized_failure(capsys, expected_stderr=expected_stderr)


def test_cli_process_boundary_does_not_hide_programmer_errors(
    tmp_path: Path, monkeypatch
) -> None:
    def fail_programmer_error(**_kwargs):
        raise AssertionError("programmer error remains visible to tests")

    monkeypatch.setattr(cli, "run_paper_runtime_process", fail_programmer_error)
    with pytest.raises(AssertionError, match="programmer error remains visible"):
        cli.main(
            [
                "run-paper-runtime",
                "--database-path",
                str(tmp_path / "unused.sqlite3"),
                "--runtime-id",
                "prt_" + "0" * 64,
                "--owner-id",
                "programmer-error-worker",
            ]
        )
