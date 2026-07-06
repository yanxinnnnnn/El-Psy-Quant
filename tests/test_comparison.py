import json
from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.comparison import compare_experiment_runs


def write_run(
    root: Path,
    run_id: str,
    metrics: list[dict[str, object]],
    *,
    metrics_artifact: str = "results/metrics.json",
    manifest_schema_version: int = 1,
    metrics_schema_version: int = 1,
) -> Path:
    run_dir = root / run_id
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True)
    manifest = {
        "schema_version": manifest_schema_version,
        "run_id": run_id,
        "experiment_name": f"Experiment {run_id}",
        "strategy": "moving_average_crossover",
        "artifacts": {"metrics": metrics_artifact},
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    if not Path(metrics_artifact).is_absolute() and ".." not in Path(
        metrics_artifact
    ).parts:
        metrics_path = run_dir / metrics_artifact
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(
            json.dumps(
                {
                    "schema_version": metrics_schema_version,
                    "run_id": run_id,
                    "source_artifact": "results/summary.csv",
                    "metrics": metrics,
                }
            ),
            encoding="utf-8",
        )
    return run_dir


def test_combines_runs_and_preserves_run_and_symbol_order(tmp_path: Path) -> None:
    first = write_run(
        tmp_path,
        "run-1",
        [
            {"symbol": "MSFT", "total_return": 0.1, "periods": 8.0},
            {"symbol": "AAPL", "total_return": 0.2, "periods": 9.0},
        ],
    )
    second = write_run(
        tmp_path,
        "run-2",
        [{"symbol": "NVDA", "total_return": -0.05, "periods": 7.0}],
    )

    comparison = compare_experiment_runs([second, first])

    assert comparison[["run_id", "symbol"]].to_dict(orient="records") == [
        {"run_id": "run-2", "symbol": "NVDA"},
        {"run_id": "run-1", "symbol": "MSFT"},
        {"run_id": "run-1", "symbol": "AAPL"},
    ]
    assert comparison["experiment_name"].tolist() == [
        "Experiment run-2",
        "Experiment run-1",
        "Experiment run-1",
    ]
    assert comparison["strategy"].tolist() == [
        "moving_average_crossover",
        "moving_average_crossover",
        "moving_average_crossover",
    ]
    assert comparison["total_return"].tolist() == [-0.05, 0.1, 0.2]
    assert comparison["periods"].tolist() == [7.0, 8.0, 9.0]


def test_preserves_annualized_metric_columns(tmp_path: Path) -> None:
    records = [
        {
            "symbol": "AAPL",
            "cagr": 0.12,
            "annualized_volatility": 0.2,
            "sharpe_ratio": 0.5,
        }
    ]
    first = write_run(tmp_path, "run-1", records)
    second = write_run(tmp_path, "run-2", records)

    comparison = compare_experiment_runs([first, second])

    pd.testing.assert_frame_equal(
        comparison[["symbol", "cagr", "annualized_volatility", "sharpe_ratio"]],
        pd.DataFrame(records * 2),
    )


def test_rejects_fewer_than_two_run_directories(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least two"):
        compare_experiment_runs([tmp_path])


def test_rejects_missing_manifest(tmp_path: Path) -> None:
    valid = write_run(tmp_path, "valid", [{"symbol": "AAPL"}])
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="manifest.json is missing"):
        compare_experiment_runs([valid, missing])


@pytest.mark.parametrize("metrics_artifact", [None, ""])
def test_rejects_missing_metrics_artifact(
    tmp_path: Path, metrics_artifact: object
) -> None:
    first = write_run(tmp_path, "run-1", [{"symbol": "AAPL"}])
    second = write_run(tmp_path, "run-2", [{"symbol": "MSFT"}])
    manifest_path = second / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["metrics"] = metrics_artifact
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=r"artifacts\.metrics is missing"):
        compare_experiment_runs([first, second])


@pytest.mark.parametrize(
    ("metrics_artifact", "message"),
    [
        (str(Path.cwd().anchor + "metrics.json"), "relative path"),
        ("../metrics.json", "must not contain"),
    ],
)
def test_rejects_unsafe_metrics_artifact_paths(
    tmp_path: Path, metrics_artifact: str, message: str
) -> None:
    first = write_run(tmp_path, "run-1", [{"symbol": "AAPL"}])
    second = write_run(
        tmp_path,
        "run-2",
        [{"symbol": "MSFT"}],
        metrics_artifact=metrics_artifact,
    )

    with pytest.raises(ValueError, match=message):
        compare_experiment_runs([first, second])


def test_rejects_missing_metrics_file(tmp_path: Path) -> None:
    first = write_run(tmp_path, "run-1", [{"symbol": "AAPL"}])
    second = write_run(tmp_path, "run-2", [{"symbol": "MSFT"}])
    (second / "results" / "metrics.json").unlink()

    with pytest.raises(ValueError, match="metrics artifact is missing"):
        compare_experiment_runs([first, second])


@pytest.mark.parametrize(
    ("manifest_version", "metrics_version", "message"),
    [(2, 1, "manifest schema_version"), (1, 2, "metrics schema_version")],
)
def test_rejects_unsupported_schema_versions(
    tmp_path: Path,
    manifest_version: int,
    metrics_version: int,
    message: str,
) -> None:
    first = write_run(tmp_path, "run-1", [{"symbol": "AAPL"}])
    second = write_run(
        tmp_path,
        "run-2",
        [{"symbol": "MSFT"}],
        manifest_schema_version=manifest_version,
        metrics_schema_version=metrics_version,
    )

    with pytest.raises(ValueError, match=message):
        compare_experiment_runs([first, second])


def test_rejects_empty_metrics_records(tmp_path: Path) -> None:
    first = write_run(tmp_path, "run-1", [{"symbol": "AAPL"}])
    second = write_run(tmp_path, "run-2", [])

    with pytest.raises(ValueError, match="must not be empty"):
        compare_experiment_runs([first, second])
