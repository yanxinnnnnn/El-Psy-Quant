"""Tests for bounded configured research artifact inspection."""

import json
import math
import socket
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from el_psy_quant.application.research_artifacts import (
    ResearchArtifactInvalidError,
    ResearchArtifactRootUnavailableError,
    ResearchRunNotFoundError,
    get_research_run_detail,
    list_research_runs,
)
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy


def _manifest(run_id: str, *, periods_per_year=None) -> dict[str, object]:
    return {
        "schema_version": 1,
        "experiment_name": "My Experiment",
        "strategy": "historical_strategy_name",
        "run_id": run_id,
        "data": {"source": "csv", "symbols": ["MSFT", "AAPL"]},
        "parameters": {
            "fast_window": 10,
            "slow_window": 20,
            "initial_capital": 1000.0,
            "transaction_cost_rate": 0.001,
            "slippage_rate": 0.002,
        },
        "evaluation": {
            "periods_per_year": periods_per_year,
            "annual_risk_free_rate": 0.01,
        },
        "artifacts": {
            "config": "config.yaml",
            "metadata": "metadata.json",
            "summary": "results/summary.csv",
            "metrics": "results/metrics.json",
            "logs_dir": "logs",
        },
        "ignored": {"secret": "not exposed"},
    }


def _metrics(run_id: str, *, annualized: bool = False) -> dict[str, object]:
    records = [
        {
            "symbol": "MSFT",
            "initial_equity": 1000.0,
            "final_equity": 1100.0,
            "total_return": 0.1,
            "max_drawdown": -0.05,
            "periods": 20.0,
            "ignored": "not exposed",
        },
        {
            "symbol": "AAPL",
            "initial_equity": 1000.0,
            "final_equity": 1050.0,
            "total_return": 0.05,
            "max_drawdown": -0.03,
            "periods": 20.0,
        },
    ]
    if annualized:
        for record in records:
            record.update(
                {
                    "cagr": 0.12,
                    "annualized_volatility": 0.2,
                    "sharpe_ratio": 0.6,
                }
            )
    return {
        "schema_version": 1,
        "run_id": run_id,
        "source_artifact": "results/summary.csv",
        "metrics": records,
        "ignored": "not exposed",
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_run(
    root: Path,
    experiment_slug: str = "my-experiment",
    run_id: str = "run_1",
    *,
    manifest: dict[str, object] | None = None,
    metrics: dict[str, object] | None = None,
) -> Path:
    run_dir = root / experiment_slug / run_id
    _write_json(run_dir / "manifest.json", manifest or _manifest(run_id))
    _write_json(run_dir / "results" / "metrics.json", metrics or _metrics(run_id))
    return run_dir


def test_root_validation_and_empty_valid_root(tmp_path: Path) -> None:
    assert list_research_runs(artifact_root=tmp_path) == ()
    for root in (tmp_path / "missing", "", object()):
        with pytest.raises(ResearchArtifactRootUnavailableError):
            list_research_runs(artifact_root=root)  # type: ignore[arg-type]


def test_discovery_is_direct_deterministic_and_ignores_non_runs(tmp_path: Path) -> None:
    _write_run(tmp_path, "z-experiment", "run_2")
    _write_run(tmp_path, "a-experiment", "run_3")
    _write_run(tmp_path, "a-experiment", "run_1")
    (tmp_path / "root-file.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / "a-experiment" / "run_without_manifest").mkdir()
    _write_run(tmp_path / "nested", "hidden-experiment", "hidden-run")

    summaries = list_research_runs(artifact_root=tmp_path)

    assert tuple((item.experiment_slug, item.run_id) for item in summaries) == (
        ("a-experiment", "run_1"),
        ("a-experiment", "run_3"),
        ("z-experiment", "run_2"),
    )


def test_discovery_reads_manifests_only(tmp_path: Path, monkeypatch) -> None:
    _write_run(tmp_path)
    original = Path.read_text
    reads: list[str] = []

    def tracked(path: Path, *args, **kwargs):
        reads.append(path.name)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", tracked)
    list_research_runs(artifact_root=tmp_path)
    assert reads == ["manifest.json"]


def test_detail_reads_only_manifest_and_referenced_metrics(
    tmp_path: Path, monkeypatch
) -> None:
    _write_run(tmp_path)
    original = Path.read_text
    reads: list[str] = []

    def tracked(path: Path, *args, **kwargs):
        reads.append(path.name)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", tracked)
    get_research_run_detail(
        artifact_root=tmp_path,
        experiment_slug="my-experiment",
        run_id="run_1",
    )
    assert reads == ["manifest.json", "metrics.json"]


def test_reads_do_not_execute_recompute_write_or_use_network(
    tmp_path: Path, monkeypatch
) -> None:
    _write_run(tmp_path)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(MovingAverageCrossoverStrategy, "run", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    assert list_research_runs(artifact_root=tmp_path)[0].run_id == "run_1"
    assert (
        get_research_run_detail(
            artifact_root=tmp_path,
            experiment_slug="my-experiment",
            run_id="run_1",
        ).run_id
        == "run_1"
    )


def test_detail_read_model_is_exact_ordered_immutable_and_path_free(
    tmp_path: Path,
) -> None:
    _write_run(tmp_path)
    detail = get_research_run_detail(
        artifact_root=tmp_path,
        experiment_slug="my-experiment",
        run_id="run_1",
    )

    assert detail.manifest_schema_version == detail.metrics_schema_version == 1
    assert detail.strategy == "historical_strategy_name"
    assert detail.data.symbols == ("MSFT", "AAPL")
    assert tuple(metric.symbol for metric in detail.metrics) == ("MSFT", "AAPL")
    assert detail.metrics[0].cagr is None
    assert detail.artifacts.metrics == "results/metrics.json"
    assert not any(isinstance(value, Path) for value in detail.__dict__.values())
    assert not hasattr(detail, "ignored")
    assert not hasattr(detail.metrics[0], "ignored")
    with pytest.raises(FrozenInstanceError):
        detail.run_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("experiment_slug", "run_id"),
    (
        ("My-experiment", "run_1"),
        (" my-experiment", "run_1"),
        ("my--experiment", "run_1"),
        ("my.experiment", "run_1"),
        ("..", "run_1"),
        ("my/experiment", "run_1"),
        ("my\\experiment", "run_1"),
        ("my-experiment", "run 1"),
        ("my-experiment", "run.1"),
        ("my-experiment", ".."),
        ("my-experiment", "run/1"),
        ("my-experiment", "C:\\run"),
    ),
)
def test_invalid_identifiers_are_rejected_before_root_access(
    experiment_slug: str, run_id: str
) -> None:
    with pytest.raises(ResearchRunNotFoundError):
        get_research_run_detail(
            artifact_root="root-does-not-need-to-exist",
            experiment_slug=experiment_slug,
            run_id=run_id,
        )


def test_missing_exact_run_is_not_found(tmp_path: Path) -> None:
    with pytest.raises(ResearchRunNotFoundError):
        get_research_run_detail(
            artifact_root=tmp_path,
            experiment_slug="my-experiment",
            run_id="missing",
        )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.update(schema_version=True),
        lambda value: value.update(schema_version=2),
        lambda value: value.update(run_id="other"),
        lambda value: value["data"].update(source="remote"),
        lambda value: value["data"].update(symbols=[]),
        lambda value: value["data"].update(symbols=["AAPL", ""]),
        lambda value: value["parameters"].update(fast_window=True),
        lambda value: value["parameters"].update(initial_capital=math.inf),
        lambda value: value["evaluation"].update(periods_per_year=0),
        lambda value: value["evaluation"].update(annual_risk_free_rate=True),
        lambda value: value["artifacts"].update(metrics=""),
        lambda value: value["artifacts"].update(metrics="../outside.json"),
        lambda value: value["artifacts"].update(metrics="C:\\outside.json"),
    ),
)
def test_invalid_manifest_contract_is_rejected(tmp_path: Path, mutate) -> None:
    manifest = _manifest("run_1")
    mutate(manifest)
    _write_run(tmp_path, manifest=manifest)
    with pytest.raises(ResearchArtifactInvalidError):
        get_research_run_detail(
            artifact_root=tmp_path,
            experiment_slug="my-experiment",
            run_id="run_1",
        )


def test_malformed_discovered_manifest_fails_deterministically(tmp_path: Path) -> None:
    path = tmp_path / "my-experiment" / "run_1" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("not-json", encoding="utf-8")
    with pytest.raises(ResearchArtifactInvalidError, match="research artifact"):
        list_research_runs(artifact_root=tmp_path)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.update(schema_version=True),
        lambda value: value.update(schema_version=2),
        lambda value: value.update(run_id="other"),
        lambda value: value.update(source_artifact="other.csv"),
        lambda value: value.update(source_artifact="../summary.csv"),
        lambda value: value.update(metrics=[]),
        lambda value: value.update(metrics=["not-an-object"]),
        lambda value: value["metrics"][0].update(symbol=""),
        lambda value: value["metrics"][0].update(initial_equity=True),
        lambda value: value["metrics"][0].update(final_equity=math.nan),
        lambda value: value["metrics"][0].update(periods=0),
        lambda value: value["metrics"][0].update(cagr=None),
    ),
)
def test_invalid_metrics_contract_is_rejected(tmp_path: Path, mutate) -> None:
    metrics = _metrics("run_1")
    mutate(metrics)
    _write_run(tmp_path, metrics=metrics)
    with pytest.raises(ResearchArtifactInvalidError):
        get_research_run_detail(
            artifact_root=tmp_path,
            experiment_slug="my-experiment",
            run_id="run_1",
        )


def test_annualized_fields_are_required_when_evaluation_is_annualized(
    tmp_path: Path,
) -> None:
    _write_run(
        tmp_path,
        manifest=_manifest("run_1", periods_per_year=252),
        metrics=_metrics("run_1"),
    )
    with pytest.raises(ResearchArtifactInvalidError):
        get_research_run_detail(
            artifact_root=tmp_path,
            experiment_slug="my-experiment",
            run_id="run_1",
        )

    _write_json(
        tmp_path / "my-experiment" / "run_1" / "results" / "metrics.json",
        _metrics("run_1", annualized=True),
    )
    detail = get_research_run_detail(
        artifact_root=tmp_path,
        experiment_slug="my-experiment",
        run_id="run_1",
    )
    assert detail.metrics[0].cagr == 0.12


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")


def test_symlinked_experiment_and_run_directories_are_ignored(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _write_run(outside, "real-experiment", "real-run")
    root = tmp_path / "root"
    root.mkdir()
    _symlink_or_skip(
        root / "linked-experiment", outside / "real-experiment", directory=True
    )
    assert list_research_runs(artifact_root=root) == ()

    experiment = root / "my-experiment"
    experiment.mkdir()
    _symlink_or_skip(
        experiment / "linked-run",
        outside / "real-experiment" / "real-run",
        directory=True,
    )
    assert list_research_runs(artifact_root=root) == ()


def test_symlinked_manifest_and_metrics_are_rejected(tmp_path: Path) -> None:
    outside_manifest = tmp_path / "outside-manifest.json"
    _write_json(outside_manifest, _manifest("run_1"))
    run_dir = tmp_path / "root" / "my-experiment" / "run_1"
    run_dir.mkdir(parents=True)
    _symlink_or_skip(run_dir / "manifest.json", outside_manifest)
    with pytest.raises(ResearchArtifactInvalidError):
        list_research_runs(artifact_root=tmp_path / "root")

    (run_dir / "manifest.json").unlink()
    _write_json(run_dir / "manifest.json", _manifest("run_1"))
    outside_metrics = tmp_path / "outside-metrics.json"
    _write_json(outside_metrics, _metrics("run_1"))
    (run_dir / "results").mkdir()
    _symlink_or_skip(run_dir / "results" / "metrics.json", outside_metrics)
    with pytest.raises(ResearchArtifactInvalidError):
        get_research_run_detail(
            artifact_root=tmp_path / "root",
            experiment_slug="my-experiment",
            run_id="run_1",
        )
