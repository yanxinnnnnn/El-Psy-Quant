"""Tests for explicit artifact-index refresh and database-only reads."""

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

import el_psy_quant.application.artifact_index as service
from el_psy_quant.application import (
    ArtifactIndexRefreshResult,
    ArtifactIndexNotFoundError,
    get_indexed_artifact,
    list_indexed_artifacts,
    refresh_artifact_index,
)
from el_psy_quant.application.evidence_manifests import EvidenceManifestSummary
from el_psy_quant.application.research_artifacts import ResearchRunSummary
from el_psy_quant.persistence import (
    create_artifact_index_entry,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.decision_governance import (
    create_strategy_decision_manifest,
    create_strategy_decision_reference,
)
from el_psy_quant.report_artifacts import (
    create_report_artifact_manifest,
    create_report_artifact_reference,
)
from el_psy_quant.strategy_review import (
    create_strategy_review_workflow_manifest,
    create_strategy_review_workflow_reference,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(database_path))
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=database_path)
    )
    factory = create_product_session_factory(engine=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _research_summary(run_id: str = "run_1") -> ResearchRunSummary:
    return ResearchRunSummary(
        experiment_slug="daily-research",
        run_id=run_id,
        experiment_name="Daily Research",
        strategy="moving_average_crossover",
        data_source="csv",
        symbols=("AAPL",),
    )


def _evidence_summaries() -> tuple[EvidenceManifestSummary, ...]:
    return (
        EvidenceManifestSummary(
            manifest_type="strategy_decision_manifest",
            artifact_key="decision_file",
            manifest_id="normalized decision id",
            reference_count=1,
            created_by="founder",
            created_timestamp=None,
            label=None,
            description=None,
        ),
        EvidenceManifestSummary(
            manifest_type="report_artifact_manifest",
            artifact_key="report_file",
            manifest_id="normalized report id",
            reference_count=1,
            created_by="founder",
            created_timestamp=None,
            label="Report",
            description=None,
        ),
        EvidenceManifestSummary(
            manifest_type="strategy_review_workflow_manifest",
            artifact_key="review_file",
            manifest_id="normalized review id",
            reference_count=1,
            created_by="founder",
            created_timestamp=None,
            label=None,
            description=None,
        ),
    )


def _stub_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        service,
        "list_research_runs",
        lambda *, artifact_root: (_research_summary(),),
    )
    monkeypatch.setattr(
        service,
        "list_evidence_manifests",
        lambda *, artifact_root: _evidence_summaries(),
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_authoritative_artifacts(research_root: Path, evidence_root: Path) -> None:
    _write_json(
        research_root / "daily-research" / "run_1" / "manifest.json",
        {
            "schema_version": 1,
            "experiment_name": "Daily Research",
            "strategy": "moving_average_crossover",
            "run_id": "run_1",
            "data": {"source": "csv", "symbols": ["AAPL"]},
            "parameters": {
                "fast_window": 10,
                "slow_window": 20,
                "initial_capital": 1000.0,
                "transaction_cost_rate": 0.001,
                "slippage_rate": 0.002,
            },
            "evaluation": {
                "periods_per_year": None,
                "annual_risk_free_rate": 0.01,
            },
            "artifacts": {
                "config": "config.yaml",
                "metadata": "metadata.json",
                "summary": "results/summary.csv",
                "metrics": "results/metrics.json",
                "logs_dir": "logs",
            },
        },
    )
    decision_reference = create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id="summary-1",
    )
    decision = create_strategy_decision_manifest(
        manifest_id=" decision id ",
        summary_references=[decision_reference],
    )
    _write_json(
        evidence_root / "strategy-decisions" / "decision_file.json",
        decision.to_dict(),
    )
    report_reference = create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id="report-1",
    )
    report = create_report_artifact_manifest(
        manifest_id=" report id ", references=[report_reference]
    )
    _write_json(
        evidence_root / "report-artifacts" / "report_file.json",
        report.to_dict(),
    )
    review_reference = create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_state_snapshot",
        reference_id="snapshot-1",
    )
    review = create_strategy_review_workflow_manifest(
        manifest_id=" review id ", state_snapshot_references=[review_reference]
    )
    _write_json(
        evidence_root / "strategy-review" / "review_file.json",
        review.to_dict(),
    )


def test_refresh_uses_real_authoritative_readers_without_modifying_artifacts(
    session_factory,
    tmp_path: Path,
) -> None:
    research_root = tmp_path / "research"
    evidence_root = tmp_path / "evidence"
    _write_authoritative_artifacts(research_root, evidence_root)
    paths = tuple(research_root.rglob("*.json")) + tuple(evidence_root.rglob("*.json"))
    before = {path: path.read_bytes() for path in paths}

    refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root=research_root,
        evidence_artifact_root=evidence_root,
    )

    assert {path: path.read_bytes() for path in paths} == before
    entries = list_indexed_artifacts(session_factory=session_factory)
    assert len(entries) == 4
    assert {entry.source_id for entry in entries} == {
        "run_1",
        "decision id",
        "report id",
        "review id",
    }


def test_refresh_maps_only_authoritative_reader_summaries(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    def research_reader(*, artifact_root):
        calls.append(("research", artifact_root))
        return (_research_summary(),)

    def evidence_reader(*, artifact_root):
        calls.append(("evidence", artifact_root))
        return _evidence_summaries()

    monkeypatch.setattr(service, "list_research_runs", research_reader)
    monkeypatch.setattr(service, "list_evidence_manifests", evidence_reader)

    result = refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root="research-root",
        evidence_artifact_root="evidence-root",
    )

    assert isinstance(result, ArtifactIndexRefreshResult)
    assert calls == [
        ("research", "research-root"),
        ("evidence", "evidence-root"),
    ]
    assert result.research_entries is not None
    assert result.research_entries[0].relative_path == (
        "daily-research/run_1/manifest.json"
    )
    assert result.research_entries[0].source_id == "run_1"
    assert result.evidence_entries is not None
    assert tuple(entry.relative_path for entry in result.evidence_entries) == (
        "report-artifacts/report_file.json",
        "strategy-decisions/decision_file.json",
        "strategy-review/review_file.json",
    )
    decision = get_indexed_artifact(
        session_factory=session_factory,
        artifact_type="strategy_decision_manifest",
        artifact_key="decision_file",
    )
    assert decision.source_id == "normalized decision id"
    assert decision.artifact_key != decision.source_id


def test_omitted_root_is_preserved_and_supplied_empty_root_is_cleared(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_discovery(monkeypatch)
    refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root="research-root",
        evidence_artifact_root="evidence-root",
    )
    monkeypatch.setattr(service, "list_research_runs", lambda *, artifact_root: ())

    result = refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root="empty-research-root",
    )

    assert result.research_entries == ()
    assert result.evidence_entries is None
    assert (
        list_indexed_artifacts(session_factory=session_factory, root_type="research")
        == ()
    )
    assert (
        len(
            list_indexed_artifacts(
                session_factory=session_factory, root_type="evidence"
            )
        )
        == 3
    )


def test_all_discovery_precedes_mutation_and_failure_preserves_existing_rows(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_discovery(monkeypatch)
    refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root="research-root",
        evidence_artifact_root="evidence-root",
    )
    before = list_indexed_artifacts(session_factory=session_factory)
    monkeypatch.setattr(
        service,
        "list_research_runs",
        lambda *, artifact_root: (_research_summary("replacement"),),
    )

    def failed_discovery(*, artifact_root):
        raise RuntimeError("discovery failed")

    monkeypatch.setattr(service, "list_evidence_manifests", failed_discovery)

    with pytest.raises(RuntimeError, match="discovery failed"):
        refresh_artifact_index(
            session_factory=session_factory,
            research_artifact_root="research-root",
            evidence_artifact_root="evidence-root",
        )
    assert list_indexed_artifacts(session_factory=session_factory) == before


def test_multi_root_database_failure_rolls_back_both_replacements(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_discovery(monkeypatch)
    original = service.SqlAlchemyArtifactIndexRepository.replace_root_entries

    def fail_evidence(self, *, root_type, entries):
        if root_type == "evidence":
            raise RuntimeError("second replacement failed")
        return original(self, root_type=root_type, entries=entries)

    monkeypatch.setattr(
        service.SqlAlchemyArtifactIndexRepository,
        "replace_root_entries",
        fail_evidence,
    )

    with pytest.raises(RuntimeError, match="second replacement failed"):
        refresh_artifact_index(
            session_factory=session_factory,
            research_artifact_root="research-root",
            evidence_artifact_root="evidence-root",
        )
    assert list_indexed_artifacts(session_factory=session_factory) == ()


def test_reads_use_only_database_rows_and_missing_is_explicit(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_discovery(monkeypatch)
    refresh_artifact_index(
        session_factory=session_factory,
        research_artifact_root="research-root",
    )

    def forbidden_read(*args, **kwargs):
        raise AssertionError("artifact files must not be read")

    monkeypatch.setattr(Path, "read_text", forbidden_read)
    assert len(list_indexed_artifacts(session_factory=session_factory)) == 1
    assert (
        get_indexed_artifact(
            session_factory=session_factory,
            artifact_type="research_run_manifest",
            artifact_key="daily-research/run_1",
        ).source_id
        == "run_1"
    )
    with pytest.raises(
        ArtifactIndexNotFoundError, match="indexed artifact not found"
    ):
        get_indexed_artifact(
            session_factory=session_factory,
            artifact_type="research_run_manifest",
            artifact_key="daily-research/missing",
        )


def test_repeated_refresh_is_idempotent_and_no_root_is_rejected(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_discovery(monkeypatch)
    first = refresh_artifact_index(
        session_factory=session_factory,
        evidence_artifact_root="evidence-root",
    )
    second = refresh_artifact_index(
        session_factory=session_factory,
        evidence_artifact_root="evidence-root",
    )

    assert second == first
    assert len(list_indexed_artifacts(session_factory=session_factory)) == 3
    with pytest.raises(ValueError, match="at least one artifact root"):
        refresh_artifact_index(session_factory=session_factory)


def test_application_services_export_no_job_or_lifecycle_state_mutation() -> None:
    from el_psy_quant import application

    forbidden = {
        "ArtifactIndexJob",
        "ArtifactIndexStatus",
        "refresh_artifact_index_async",
        "set_current_lifecycle_state",
        "resolve_indexed_artifact_payload",
    }
    assert all(not hasattr(application, name) for name in forbidden)
    entry = create_artifact_index_entry(
        artifact_type="report_artifact_manifest",
        artifact_key="report",
        source_id="report id",
    )
    assert not hasattr(entry, "payload")
