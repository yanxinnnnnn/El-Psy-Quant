"""Focused Sprint 223 dedicated Paper Runtime process composition tests."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone

from el_psy_quant import cli
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeOwnershipService,
    PaperRuntimeRecoveryService,
)
from test_paper_runtime_runner import _read, _runner_fixture
from test_paper_runtime_recovery import _leave_work_without_attempt


def test_cli_recovery_continues_with_exact_fence_and_iteration_budget(
    tmp_path: Path, monkeypatch
) -> None:
    engine, _factory, _order, _lifecycle, _ownership, _runner, _clock, claim = (
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
    pending = _read(factory, claim.runtime_id)[1][0]
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
