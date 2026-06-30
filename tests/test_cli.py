import json
import tomllib
from pathlib import Path

import pandas as pd

from el_psy_quant.cli import main

PRICES_CSV = """Date,Open,High,Low,Close,Volume
2024-01-01,10,11,9,10,100
2024-01-02,20,21,19,20,110
2024-01-03,30,31,29,30,120
2024-01-04,20,21,19,20,130
2024-01-05,10,11,9,10,140
2024-01-06,20,21,19,20,150
2024-01-07,30,31,29,30,160
2024-01-08,40,41,39,40,170
"""


def write_config(tmp_path: Path) -> tuple[Path, str]:
    aapl_path = tmp_path / "aapl.csv"
    msft_path = tmp_path / "msft.csv"
    aapl_path.write_text(PRICES_CSV, encoding="utf-8")
    msft_path.write_text(PRICES_CSV, encoding="utf-8")
    content = f"""experiment:
  name: CLI Local Test
  strategy: moving_average_crossover
data:
  source: csv
  paths:
    AAPL: {aapl_path.as_posix()}
    MSFT: {msft_path.as_posix()}
parameters:
  fast_window: 2
  slow_window: 3
  initial_capital: 1000.0
evaluation:
  periods_per_year: 252
  annual_risk_free_rate: 0.02
"""
    config_path = tmp_path / "experiment.yaml"
    config_path.write_text(content, encoding="utf-8")
    return config_path, content


def test_main_runs_csv_config_and_writes_minimal_artifacts(
    tmp_path: Path, capsys
) -> None:
    config_path, config_text = write_config(tmp_path)
    output_root = tmp_path / "outputs"

    exit_code = main(
        [
            "run",
            str(config_path),
            "--output-root",
            str(output_root),
            "--run-id",
            "20260630T141500Z",
        ]
    )

    run_dir = output_root / "cli-local-test" / "20260630T141500Z"
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(run_dir)
    assert (run_dir / "config.yaml").read_text(encoding="utf-8") == config_text
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata == {
        "experiment_name": "CLI Local Test",
        "strategy": "moving_average_crossover",
        "data_source": "csv",
        "run_id": "20260630T141500Z",
        "summary_path": "results/summary.csv",
    }
    summary = pd.read_csv(run_dir / "results" / "summary.csv")
    assert summary["symbol"].tolist() == ["AAPL", "MSFT"]
    assert set(run_dir.rglob("*")) == {
        run_dir / "results",
        run_dir / "logs",
        run_dir / "config.yaml",
        run_dir / "metadata.json",
        run_dir / "results" / "summary.csv",
    }


def test_invalid_config_returns_nonzero_and_prints_error(
    tmp_path: Path, capsys
) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("", encoding="utf-8")

    exit_code = main(
        ["run", str(config_path), "--output-root", str(tmp_path / "outputs")]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert "must not be empty" in captured.err


def test_console_script_entrypoint_exists() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["el-psy-quant"] == "el_psy_quant.cli:main"


def test_cli_main_is_importable() -> None:
    from el_psy_quant import cli

    assert cli.main is main
