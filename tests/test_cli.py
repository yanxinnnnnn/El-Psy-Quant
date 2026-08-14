import json
import tomllib
from pathlib import Path

import pandas as pd

from el_psy_quant import cli
from el_psy_quant.cli import main
from el_psy_quant.strategies import Strategy

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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
    tmp_path: Path, capsys, monkeypatch
) -> None:
    config_path, config_text = write_config(tmp_path)
    output_root = tmp_path / "outputs"
    resolved_names: list[str] = []
    strategy_calls: list[tuple[pd.DataFrame, dict[str, object]]] = []
    original_resolve_strategy = cli.resolve_strategy

    class RecordingStrategy:
        name = "moving_average_crossover"

        def __init__(self, delegate: Strategy) -> None:
            self.delegate = delegate

        def run(
            self,
            prices: pd.DataFrame,
            parameters: dict[str, object],
        ) -> pd.DataFrame:
            strategy_calls.append((prices, dict(parameters)))
            return self.delegate.run(prices, parameters)

    def recording_resolver(name: str) -> Strategy:
        resolved_names.append(name)
        return RecordingStrategy(original_resolve_strategy(name))

    monkeypatch.setattr(cli, "resolve_strategy", recording_resolver)

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
    assert resolved_names == ["moving_average_crossover"]
    assert len(strategy_calls) == 2
    assert all("Close" in prices for prices, _ in strategy_calls)
    assert [parameters for _, parameters in strategy_calls] == [
        {
            "fast_window": 2,
            "slow_window": 3,
            "initial_capital": 1_000.0,
            "transaction_cost_rate": 0.0,
            "slippage_rate": 0.0,
        }
    ] * 2
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
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "schema_version": 1,
        "experiment_name": "CLI Local Test",
        "strategy": "moving_average_crossover",
        "run_id": "20260630T141500Z",
        "data": {
            "source": "csv",
            "symbols": ["AAPL", "MSFT"],
        },
        "parameters": {
            "fast_window": 2,
            "slow_window": 3,
            "initial_capital": 1_000.0,
            "transaction_cost_rate": 0.0,
            "slippage_rate": 0.0,
        },
        "evaluation": {
            "periods_per_year": 252.0,
            "annual_risk_free_rate": 0.02,
        },
        "artifacts": {
            "config": "config.yaml",
            "metadata": "metadata.json",
            "summary": "results/summary.csv",
            "metrics": "results/metrics.json",
            "logs_dir": "logs",
        },
    }
    assert all(
        not Path(path).is_absolute() and ".." not in Path(path).parts
        for path in manifest["artifacts"].values()
    )
    summary = pd.read_csv(run_dir / "results" / "summary.csv")
    assert summary["symbol"].tolist() == ["AAPL", "MSFT"]
    metrics = json.loads(
        (run_dir / "results" / "metrics.json").read_text(encoding="utf-8")
    )
    assert {key: value for key, value in metrics.items() if key != "metrics"} == {
        "schema_version": 1,
        "run_id": "20260630T141500Z",
        "source_artifact": "results/summary.csv",
    }
    pd.testing.assert_frame_equal(pd.DataFrame(metrics["metrics"]), summary)
    assert not Path(metrics["source_artifact"]).is_absolute()
    assert ".." not in Path(metrics["source_artifact"]).parts
    assert set(run_dir.rglob("*")) == {
        run_dir / "results",
        run_dir / "logs",
        run_dir / "config.yaml",
        run_dir / "metadata.json",
        run_dir / "manifest.json",
        run_dir / "results" / "summary.csv",
        run_dir / "results" / "metrics.json",
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


def test_unsupported_strategy_name_returns_nonzero(tmp_path: Path, capsys) -> None:
    config_path, _ = write_config(tmp_path)
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "moving_average_crossover",
            "Moving_Average_Crossover",
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["run", str(config_path), "--output-root", str(tmp_path / "outputs")]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "experiment.strategy" in captured.err


def test_invalid_prices_fail_before_strategy_resolution(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    config_path, _ = write_config(tmp_path)
    aapl_path = tmp_path / "aapl.csv"
    aapl_path.write_text(
        PRICES_CSV.replace("2024-01-01,10,11,9,10,100", "2024-01-01,10,11,9,bad,100"),
        encoding="utf-8",
    )

    def unexpected_resolver(name: str) -> Strategy:
        raise AssertionError(f"resolver must not be called for {name}")

    monkeypatch.setattr(cli, "resolve_strategy", unexpected_resolver)

    exit_code = main(
        ["run", str(config_path), "--output-root", str(tmp_path / "outputs")]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "AAPL price data invalid" in captured.err
    assert "Close must contain numeric values" in captured.err


def test_console_script_entrypoint_exists() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["el-psy-quant"] == "el_psy_quant.cli:main"


def test_demo_installer_cli_requires_demo_mode_and_replays_deterministically(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    target = tmp_path / "demo"
    arguments = [
        "install-demo-workspace",
        "--source-root",
        str(PROJECT_ROOT / "examples" / "demo_workspace"),
        "--workspace-root",
        str(target),
        "--alembic-config",
        str(PROJECT_ROOT / "alembic.ini"),
    ]

    monkeypatch.setenv("EL_PSY_QUANT_WORKSPACE_MODE", "standard")
    assert main(arguments) == 1
    assert not target.exists()
    assert "demo mode is required" in capsys.readouterr().err

    monkeypatch.setenv("EL_PSY_QUANT_WORKSPACE_MODE", "demo")
    assert main(arguments) == 0
    assert "founder-demo-workspace v5 installed" in capsys.readouterr().out
    assert main(arguments) == 0
    assert "founder-demo-workspace v5 already installed" in capsys.readouterr().out


def test_cli_main_is_importable() -> None:
    from el_psy_quant import cli

    assert cli.main is main


def test_startup_resource_failure_prints_only_safe_bounded_identity(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    def fail_startup(**_kwargs) -> None:
        try:
            raise FileNotFoundError("C:/private/runtime/site-packages/migrations/env.py")
        except FileNotFoundError as error:
            raise cli.LocalWorkspaceError(
                "product migration resources are unavailable"
            ) from error

    monkeypatch.setattr(cli, "start_local_backend", fail_startup)

    exit_code = main(
        [
            "start-local-backend",
            "--mode",
            "standard",
            "--workspace-root",
            str(tmp_path / "standard"),
            "--alembic-config",
            str(tmp_path / "alembic.ini"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: product migration resources are unavailable\n"
    assert "private" not in captured.err
