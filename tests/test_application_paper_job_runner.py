"""Tests for the explicit one-job runner and queued-only manual control."""

from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config

import el_psy_quant.application.paper_jobs as service
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperJobExecutionError,
    PaperJobNotFoundError,
    PaperJobOutputConflictError,
    PaperJobRunResult,
    PaperJobStateConflictError,
    PaperRunCommand,
    cancel_paper_job,
    get_paper_job,
    list_paper_jobs,
    run_paper_job_once,
    submit_paper_job,
)
from el_psy_quant.configured_paper import PaperWorkflowRunResult
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.persistence import (
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "12345678-1234-4abc-8def-1234567890ab"
OTHER_JOB_ID = "00000000-0000-4000-8000-000000000002"


@pytest.fixture
def session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    alembic_command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _account(timestamp: str, cash: float, positions: dict[str, float]):
    return PaperAccountStateCommandInput(
        timestamp=timestamp,
        starting_cash=10_000,
        current_cash=cash,
        positions=positions,
    )


def _command(run_id: str = "run-1") -> PaperRunCommand:
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp="2026-07-13T12:00:00Z",
        starting_account_state=_account(
            "2026-07-13T11:00:00Z", 10_000, {"AAPL": 1}
        ),
        ending_account_state=_account(
            "2026-07-13T11:30:00Z", 9_900, {"AAPL": 2}
        ),
        orders=(),
        fills=(),
    )


def _submit(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
    *,
    job_id: str = JOB_ID,
    run_id: str = "run-1",
):
    monkeypatch.setattr(service, "_new_job_id", lambda: job_id)
    return submit_paper_job(
        session_factory=session_factory,
        command=_command(run_id),
    )


def test_selected_job_runs_once_to_succeeded_and_leaves_other_job_queued(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _submit(session_factory, monkeypatch)
    other = _submit(
        session_factory,
        monkeypatch,
        job_id=OTHER_JOB_ID,
        run_id="other-run",
    )
    run_dir = tmp_path / "run-output"
    run_dir.mkdir()
    captured_requests = []
    original = service.run_paper_workflow_request

    def tracked(*, request, run_dir):
        captured_requests.append(request)
        return original(request=request, run_dir=run_dir)

    monkeypatch.setattr(service, "run_paper_workflow_request", tracked)

    result = run_paper_job_once(
        session_factory=session_factory,
        job_id=selected.job_id,
        run_dir=run_dir,
    )

    assert isinstance(result, PaperJobRunResult)
    assert isinstance(result.workflow, PaperWorkflowRunResult)
    assert result.job.status == "succeeded"
    assert result.workflow.request.to_dict() == selected.request.to_dict()
    assert [request.to_dict() for request in captured_requests] == [
        selected.request.to_dict()
    ]
    assert get_paper_job(
        session_factory=session_factory, job_id=selected.job_id
    ) == result.job
    assert get_paper_job(
        session_factory=session_factory, job_id=other.job_id
    ) == other
    assert list_paper_jobs(session_factory=session_factory, status="running") == ()
    assert sorted(path.name for path in (run_dir / "paper").iterdir()) == [
        "paper_run_artifact.json",
        "paper_run_result_summary.json",
    ]

    with pytest.raises(PaperJobStateConflictError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=selected.job_id,
            run_dir=tmp_path,
        )
    with pytest.raises(PaperJobStateConflictError):
        cancel_paper_job(session_factory=session_factory, job_id=selected.job_id)
    assert len(captured_requests) == 1


def test_execution_occurs_after_claim_commit_with_no_open_service_transaction(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run-output"
    run_dir.mkdir()
    active_transactions = 0
    transaction_count = 0
    original_workflow = service.run_paper_workflow_request

    class TrackingFactory:
        @contextmanager
        def begin(self):
            nonlocal active_transactions, transaction_count
            with session_factory.begin() as session:
                active_transactions += 1
                transaction_count += 1
                try:
                    yield session
                finally:
                    active_transactions -= 1

    def tracked_workflow(*, request, run_dir):
        assert active_transactions == 0
        with session_factory() as independent_session:
            assert not independent_session.in_transaction()
        return original_workflow(request=request, run_dir=run_dir)

    monkeypatch.setattr(
        service,
        "run_paper_workflow_request",
        tracked_workflow,
    )

    result = run_paper_job_once(
        session_factory=TrackingFactory(),  # type: ignore[arg-type]
        job_id=job.job_id,
        run_dir=run_dir,
    )

    assert result.job.status == "succeeded"
    assert transaction_count == 2
    assert active_transactions == 0


@pytest.mark.parametrize("reserved_name", (None, "artifact", "summary"))
def test_preflight_failure_leaves_job_queued_and_never_overwrites(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reserved_name: str | None,
) -> None:
    job = _submit(session_factory, monkeypatch)
    if reserved_name is None:
        run_dir = tmp_path / "missing"
        expected_error = ValueError
    else:
        run_dir = tmp_path / "run-output"
        run_dir.mkdir()
        paths = create_configured_paper_run_output_paths(run_dir=run_dir)
        reserved_path = (
            paths.paper_run_artifact_path
            if reserved_name == "artifact"
            else paths.paper_run_result_summary_path
        )
        reserved_path.parent.mkdir()
        reserved_path.write_text("do-not-overwrite", encoding="utf-8")
        expected_error = PaperJobOutputConflictError

    with pytest.raises(expected_error):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    assert get_paper_job(session_factory=session_factory, job_id=job.job_id) == job
    if reserved_name is None:
        assert not (run_dir / "paper").exists()
    else:
        assert reserved_path.read_text(encoding="utf-8") == "do-not-overwrite"


def test_non_directory_preflight_leaves_job_queued(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_file = tmp_path / "run-file"
    run_file.write_text("not-a-directory", encoding="utf-8")

    with pytest.raises(ValueError, match="run_dir must be a directory"):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_file,
        )

    assert get_paper_job(session_factory=session_factory, job_id=job.job_id) == job


@pytest.mark.parametrize("failure", (ValueError("private domain"), OSError("private fs")))
def test_expected_execution_failure_is_sanitized_and_marks_failed(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run-output"
    run_dir.mkdir()
    calls = 0

    def fail(*, request, run_dir):
        nonlocal calls
        del request, run_dir
        calls += 1
        raise failure

    monkeypatch.setattr(service, "run_paper_workflow_request", fail)

    with pytest.raises(PaperJobExecutionError) as raised:
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    assert str(raised.value) == "paper job execution failed"
    assert raised.value.__cause__ is failure
    failed = get_paper_job(session_factory=session_factory, job_id=job.job_id)
    assert failed.status == "failed"
    assert calls == 1
    assert all(
        not hasattr(failed, field)
        for field in ("error", "error_code", "traceback", "attempt", "retry")
    )
    with pytest.raises(PaperJobStateConflictError):
        cancel_paper_job(session_factory=session_factory, job_id=job.job_id)


def test_partial_output_is_preserved_when_expected_persistence_failure_occurs(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run-output"
    run_dir.mkdir()
    partial_path = run_dir / "paper" / "paper_run_artifact.json"

    def partial_failure(*, request, run_dir):
        del request
        paper_dir = run_dir / "paper"
        paper_dir.mkdir()
        partial_path.write_text("partial", encoding="utf-8")
        raise OSError("private result-summary failure")

    monkeypatch.setattr(service, "run_paper_workflow_request", partial_failure)

    with pytest.raises(PaperJobExecutionError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    assert partial_path.read_text(encoding="utf-8") == "partial"
    assert get_paper_job(
        session_factory=session_factory, job_id=job.job_id
    ).status == "failed"


def test_programming_error_is_not_swallowed_and_job_remains_running(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "run-output"
    run_dir.mkdir()

    def programming_failure(*, request, run_dir):
        del request, run_dir
        raise RuntimeError("programming failure")

    monkeypatch.setattr(service, "run_paper_workflow_request", programming_failure)

    with pytest.raises(RuntimeError, match="programming failure"):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=run_dir,
        )

    assert get_paper_job(
        session_factory=session_factory, job_id=job.job_id
    ).status == "running"
    with pytest.raises(PaperJobStateConflictError):
        cancel_paper_job(session_factory=session_factory, job_id=job.job_id)


def test_manual_cancellation_is_queued_only_and_writes_nothing(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)

    canceled = cancel_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    )

    assert canceled.status == "canceled"
    assert list(tmp_path.rglob("paper_run_artifact.json")) == []
    with pytest.raises(PaperJobStateConflictError):
        cancel_paper_job(session_factory=session_factory, job_id=job.job_id)
    with pytest.raises(PaperJobStateConflictError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            run_dir=tmp_path,
        )


def test_missing_job_is_explicit_for_run_and_cancel(
    session_factory,
    tmp_path: Path,
) -> None:
    with pytest.raises(PaperJobNotFoundError):
        run_paper_job_once(
            session_factory=session_factory,
            job_id=JOB_ID,
            run_dir=tmp_path,
        )
    with pytest.raises(PaperJobNotFoundError):
        cancel_paper_job(session_factory=session_factory, job_id=JOB_ID)
    assert not (tmp_path / "paper").exists()
