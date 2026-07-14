"""Integration tests for product-root execution and authoritative result reads."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

import el_psy_quant.application.paper_jobs as service
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperJobExecutionError,
    PaperJobResultInvalidError,
    PaperJobResultUnavailableError,
    PaperJobStateConflictError,
    PaperRunCommand,
    get_paper_job,
    get_paper_job_result_reference,
    list_paper_job_attempts,
    read_paper_job_result,
    recover_product_paper_job,
    run_paper_job_once,
    run_product_paper_job_once,
    submit_paper_job,
)
from el_psy_quant.persistence import (
    SqlAlchemyPaperJobResultReferenceRepository,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOB_ID = "12345678-1234-4abc-8def-1234567890ab"


@pytest.fixture
def session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    alembic_command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
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
        created_timestamp="2026-07-14T12:00:00Z",
        starting_account_state=_account(
            "2026-07-14T11:00:00Z", 10_000, {"AAPL": 1}
        ),
        ending_account_state=_account(
            "2026-07-14T11:30:00Z", 9_900, {"AAPL": 2}
        ),
        orders=(),
        fills=(),
    )


def _submit(session_factory, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service, "_new_job_id", lambda: JOB_ID)
    return submit_paper_job(session_factory=session_factory, command=_command())


def test_product_execution_atomically_completes_job_attempt_and_reference(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()

    result = run_product_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
    )

    reference = get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    )
    assert reference is not None
    assert reference.artifact_relative_path == (
        f"jobs/{JOB_ID}/paper/paper_run_artifact.json"
    )
    assert reference.result_summary_relative_path == (
        f"jobs/{JOB_ID}/paper/paper_run_result_summary.json"
    )
    assert result.job.status == result.attempt.status == "succeeded"
    assert (
        result.job.updated_timestamp
        == result.attempt.completed_timestamp
        == reference.created_timestamp
    )
    assert (root / reference.artifact_relative_path).is_file()
    assert (root / reference.result_summary_relative_path).is_file()


def test_reference_failure_rolls_back_terminal_state_but_preserves_files(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    monkeypatch.setattr(
        SqlAlchemyPaperJobResultReferenceRepository,
        "add",
        lambda self, *, reference: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="boom"):
        run_product_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=root,
        )

    persisted = get_paper_job(session_factory=session_factory, job_id=job.job_id)
    attempt = list_paper_job_attempts(
        session_factory=session_factory,
        job_id=job.job_id,
    )[0]
    assert persisted.status == attempt.status == "running"
    assert attempt.completed_timestamp is None
    assert get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    ) is None
    assert (root / "jobs" / JOB_ID / "paper" / "paper_run_artifact.json").is_file()
    assert (
        root / "jobs" / JOB_ID / "paper" / "paper_run_result_summary.json"
    ).is_file()


def test_expected_execution_failure_creates_no_reference(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    monkeypatch.setattr(
        service,
        "run_paper_workflow_request",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("invalid workflow")),
    )

    with pytest.raises(PaperJobExecutionError):
        run_product_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=root,
        )

    assert get_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
    ).status == "failed"
    assert get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    ) is None


def test_successful_recovery_atomically_registers_existing_valid_outputs(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    original_add = SqlAlchemyPaperJobResultReferenceRepository.add
    monkeypatch.setattr(
        SqlAlchemyPaperJobResultReferenceRepository,
        "add",
        lambda self, *, reference: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(RuntimeError):
        run_product_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=root,
        )
    monkeypatch.setattr(
        SqlAlchemyPaperJobResultReferenceRepository,
        "add",
        original_add,
    )

    recovered = recover_product_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
        stale_before=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    reference = get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    )
    assert recovered.outcome == "succeeded"
    assert reference is not None
    assert (
        recovered.job.updated_timestamp
        == recovered.attempt.completed_timestamp
        == reference.created_timestamp
    )


def test_no_output_recovery_creates_no_result_reference(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    monkeypatch.setattr(
        service,
        "run_paper_workflow_request",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("interrupted")),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        run_product_paper_job_once(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=root,
        )

    recovered = recover_product_paper_job(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
        stale_before=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    assert recovered.outcome == "requeued"
    assert recovered.job.status == "queued"
    assert recovered.attempt.status == "interrupted"
    assert get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    ) is None


def test_result_read_returns_explicit_path_free_views_and_detects_mutation(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    run_product_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
    )

    view = read_paper_job_result(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
    )

    assert view.job_id == JOB_ID
    assert view.run_id == "run-1"
    assert view.artifact.session_summary.order_count == 0
    assert not hasattr(view.result_reference, "artifact_relative_path")
    assert not hasattr(view.result_summary, "artifact_path")
    summary_path = (
        root / "jobs" / JOB_ID / "paper" / "paper_run_result_summary.json"
    )
    original = summary_path.read_bytes()
    summary_path.write_text("{}", encoding="utf-8")
    with pytest.raises(PaperJobResultInvalidError):
        read_paper_job_result(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=root,
        )
    assert summary_path.read_text(encoding="utf-8") == "{}"
    assert original != b"{}"


def test_result_files_are_read_only_after_database_session_closes(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    run_product_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
    )
    active_sessions = 0

    class TrackingSession(Session):
        def __init__(self, *args, **kwargs) -> None:
            nonlocal active_sessions
            super().__init__(*args, **kwargs)
            active_sessions += 1

        def close(self) -> None:
            nonlocal active_sessions
            if self.is_active:
                active_sessions -= 1
            super().close()

    tracking_factory = sessionmaker(
        bind=session_factory.kw["bind"],
        class_=TrackingSession,
    )
    original_reader = service.read_paper_trading_artifact_file

    def tracked_reader(path):
        assert active_sessions == 0
        return original_reader(path)

    monkeypatch.setattr(service, "read_paper_trading_artifact_file", tracked_reader)

    view = read_paper_job_result(
        session_factory=tracking_factory,
        job_id=job.job_id,
        paper_artifact_root=root,
    )

    assert view.job_id == job.job_id
    assert active_sessions == 0


def test_manual_success_remains_backward_compatible_without_reference(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    run_dir = tmp_path / "operator-run"
    run_dir.mkdir()

    result = run_paper_job_once(
        session_factory=session_factory,
        job_id=job.job_id,
        run_dir=run_dir,
    )

    assert result.job.status == "succeeded"
    assert get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    ) is None
    with pytest.raises(PaperJobResultUnavailableError):
        read_paper_job_result(
            session_factory=session_factory,
            job_id=job.job_id,
            paper_artifact_root=tmp_path,
        )


def test_concurrent_product_runs_create_one_attempt_and_one_reference(
    session_factory,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _submit(session_factory, monkeypatch)
    root = tmp_path / "paper-root"
    root.mkdir()
    barrier = Barrier(2)
    original_preflight = service._preflight_run_dir

    def synchronized_preflight(run_dir):
        validated = original_preflight(run_dir)
        barrier.wait(timeout=5)
        return validated

    monkeypatch.setattr(service, "_preflight_run_dir", synchronized_preflight)

    def run_once():
        try:
            return run_product_paper_job_once(
                session_factory=session_factory,
                job_id=job.job_id,
                paper_artifact_root=root,
            )
        except PaperJobStateConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: run_once(), range(2)))

    assert sum(not isinstance(item, Exception) for item in outcomes) == 1
    assert sum(isinstance(item, PaperJobStateConflictError) for item in outcomes) == 1
    assert len(
        list_paper_job_attempts(
            session_factory=session_factory,
            job_id=job.job_id,
        )
    ) == 1
    assert get_paper_job_result_reference(
        session_factory=session_factory,
        job_id=job.job_id,
    ) is not None
