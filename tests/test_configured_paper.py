"""Tests for configured local paper workflow runner."""

import json
from pathlib import Path

import pytest

from el_psy_quant.config import load_experiment_config
from el_psy_quant.configured_paper import (
    ConfiguredPaperWorkflowRunResult,
    run_configured_paper_workflow,
)
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.paper import (
    PaperRunRequest,
    PaperRunResultSummary,
    PaperTradingArtifact,
    create_paper_trading_artifact_file_payload,
)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "experiment.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def valid_config_with_paper_run() -> str:
    return """
experiment:
  name: ma-crossover-with-paper
  strategy: moving_average_crossover
data:
  source: cache
  cache_dir: data/cache
  symbols: [AAPL]
parameters:
  fast_window: 20
  slow_window: 50
paper_run:
  run_id: paper-run-001
  created_timestamp: "2026-07-08T00:00:00Z"
  starting_account_state:
    timestamp: "2026-07-08T00:00:00Z"
    starting_cash: 10000.0
    current_cash: 10000.0
    positions:
      AAPL: 0.0
  ending_account_state:
    timestamp: "2026-07-08T00:01:00Z"
    starting_cash: 10000.0
    current_cash: 9900.0
    positions:
      AAPL: 1.0
  orders:
    - order_id: order-001
      timestamp: "2026-07-08T00:00:30Z"
      symbol: AAPL
      side: buy
      quantity: 1.0
      status: filled
  fills:
    - timestamp: "2026-07-08T00:00:45Z"
      symbol: AAPL
      side: buy
      quantity: 1.0
      price: 100.0
      order_id: order-001
"""


def research_only_config() -> str:
    return """
experiment:
  name: ma-crossover-research-only
  strategy: moving_average_crossover
data:
  source: cache
  cache_dir: data/cache
  symbols: [AAPL]
parameters:
  fast_window: 20
  slow_window: 50
"""


def test_configured_paper_workflow_writes_expected_files(tmp_path: Path) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    expected_paths = create_configured_paper_run_output_paths(run_dir=run_dir)

    result = run_configured_paper_workflow(config=config, run_dir=run_dir)

    assert result.paper_run_artifact_path == expected_paths.paper_run_artifact_path
    assert (
        result.paper_run_result_summary_path
        == expected_paths.paper_run_result_summary_path
    )
    assert result.paper_run_artifact_path.is_file()
    assert result.paper_run_result_summary_path.is_file()
    assert sorted(path.name for path in (run_dir / "paper").iterdir()) == [
        "paper_run_artifact.json",
        "paper_run_result_summary.json",
    ]


def test_configured_paper_workflow_returned_objects_are_consistent(
    tmp_path: Path,
) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    result = run_configured_paper_workflow(config=config, run_dir=run_dir)

    assert isinstance(result, ConfiguredPaperWorkflowRunResult)
    assert isinstance(result.request, PaperRunRequest)
    assert isinstance(result.artifact, PaperTradingArtifact)
    assert isinstance(result.result_summary, PaperRunResultSummary)
    assert result.request.run_id == "paper-run-001"
    assert result.result_summary.request is result.request
    assert result.result_summary.artifact is result.artifact
    assert result.result_summary.to_dict()["artifact"]["path"] == str(
        result.paper_run_artifact_path
    )


def test_configured_paper_workflow_writes_deterministic_json(
    tmp_path: Path,
) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    result = run_configured_paper_workflow(config=config, run_dir=run_dir)

    artifact_payload = json.loads(
        result.paper_run_artifact_path.read_text(encoding="utf-8")
    )
    summary_payload = json.loads(
        result.paper_run_result_summary_path.read_text(encoding="utf-8")
    )
    assert artifact_payload == create_paper_trading_artifact_file_payload(
        result.artifact
    )
    assert summary_payload == result.result_summary.to_dict()
    assert result.paper_run_artifact_path.read_text(encoding="utf-8").endswith("\n")
    assert result.paper_run_result_summary_path.read_text(
        encoding="utf-8"
    ).endswith("\n")
    json.dumps(artifact_payload, allow_nan=False)
    json.dumps(summary_payload, allow_nan=False)


def test_configured_paper_workflow_creates_only_paper_output_directory(
    tmp_path: Path,
) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    run_configured_paper_workflow(config=config, run_dir=run_dir)

    assert sorted(path.name for path in run_dir.iterdir()) == ["paper"]
    assert not (run_dir / "manifest.json").exists()
    assert not (run_dir / "metadata.json").exists()
    assert not (run_dir / "config.yaml").exists()


def test_configured_paper_workflow_requires_paper_run_config(
    tmp_path: Path,
) -> None:
    config = load_experiment_config(write_config(tmp_path, research_only_config()))
    assert config.paper_run is None
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="config.paper_run"):
        run_configured_paper_workflow(config=config, run_dir=run_dir)


def test_configured_paper_workflow_rejects_non_experiment_config(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="ExperimentConfig"):
        run_configured_paper_workflow(config=object(), run_dir=run_dir)  # type: ignore[arg-type]


def test_configured_paper_workflow_rejects_missing_run_dir(tmp_path: Path) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )

    with pytest.raises(ValueError, match="run_dir"):
        run_configured_paper_workflow(config=config, run_dir=tmp_path / "missing")


def test_configured_paper_workflow_rejects_non_directory_run_dir(
    tmp_path: Path,
) -> None:
    config = load_experiment_config(
        write_config(tmp_path, valid_config_with_paper_run())
    )
    run_dir = tmp_path / "run-file"
    run_dir.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="run_dir"):
        run_configured_paper_workflow(config=config, run_dir=run_dir)


def test_configured_paper_api_is_importable() -> None:
    from el_psy_quant import configured_paper

    assert (
        configured_paper.ConfiguredPaperWorkflowRunResult
        is ConfiguredPaperWorkflowRunResult
    )
    assert configured_paper.run_configured_paper_workflow is run_configured_paper_workflow
