import re
from pathlib import Path

import pytest

from el_psy_quant.outputs import (
    ExperimentOutputLayout,
    create_experiment_output_layout,
)


def test_creates_expected_directory_tree_and_paths(tmp_path: Path) -> None:
    layout = create_experiment_output_layout(
        tmp_path,
        "MA Crossover Local",
        run_id="20260630T141500Z",
    )

    experiment_dir = tmp_path / "ma-crossover-local"
    run_dir = experiment_dir / "20260630T141500Z"
    assert layout == ExperimentOutputLayout(
        root_dir=tmp_path,
        experiment_dir=experiment_dir,
        run_dir=run_dir,
        config_path=run_dir / "config.yaml",
        metadata_path=run_dir / "metadata.json",
        results_dir=run_dir / "results",
        logs_dir=run_dir / "logs",
    )
    assert experiment_dir.is_dir()
    assert run_dir.is_dir()
    assert layout.results_dir.is_dir()
    assert layout.logs_dir.is_dir()


def test_does_not_write_reserved_files(tmp_path: Path) -> None:
    layout = create_experiment_output_layout(tmp_path, "test", run_id="run_1")

    assert not layout.config_path.exists()
    assert not layout.metadata_path.exists()
    assert list(layout.results_dir.iterdir()) == []
    assert list(layout.logs_dir.iterdir()) == []


@pytest.mark.parametrize(
    ("name", "expected_slug"),
    [
        ("MA Crossover Local", "ma-crossover-local"),
        ("  AAPL/MSFT Test  ", "aapl-msft-test"),
        ("alpha___beta", "alpha-beta"),
    ],
)
def test_slugifies_experiment_name(
    tmp_path: Path, name: str, expected_slug: str
) -> None:
    layout = create_experiment_output_layout(tmp_path, name, run_id="run-1")

    assert layout.experiment_dir.name == expected_slug


@pytest.mark.parametrize("name", ["", "   ", "///", 123])
def test_rejects_invalid_experiment_names(tmp_path: Path, name: object) -> None:
    with pytest.raises(ValueError, match="experiment_name"):
        create_experiment_output_layout(tmp_path, name, run_id="run-1")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "run_id",
    ["", "   ", "run id", "../run", "..", ".", "run/id", r"run\id"],
)
def test_rejects_invalid_run_ids(tmp_path: Path, run_id: str) -> None:
    with pytest.raises(ValueError, match="run_id"):
        create_experiment_output_layout(tmp_path, "test", run_id=run_id)


def test_generates_utc_timestamp_run_id(tmp_path: Path) -> None:
    layout = create_experiment_output_layout(tmp_path, "test")

    assert re.fullmatch(r"\d{8}T\d{6}Z", layout.run_dir.name)
    assert layout.run_dir.is_dir()


def test_output_api_is_importable() -> None:
    from el_psy_quant import outputs

    assert outputs.ExperimentOutputLayout is ExperimentOutputLayout
    assert outputs.create_experiment_output_layout is create_experiment_output_layout
