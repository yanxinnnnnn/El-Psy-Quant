from pathlib import Path

import pytest

from el_psy_quant.config import (
    ExperimentConfig,
    ExperimentDataConfig,
    ExperimentEvaluationConfig,
    MovingAverageCrossoverParameters,
    load_experiment_config,
)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "experiment.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_csv_source_config_and_normalizes_symbols(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
experiment:
  name: ma-crossover-local
  strategy: moving_average_crossover
data:
  source: csv
  paths:
    " msft ": data/cache/MSFT.csv
    aapl: data/cache/AAPL.csv
parameters:
  fast_window: 20
  slow_window: 50
  initial_capital: 1000.0
  transaction_cost_rate: 0.001
  slippage_rate: 0.0005
evaluation:
  periods_per_year: 252
  annual_risk_free_rate: 0.02
""",
    )

    config = load_experiment_config(path)

    assert config.name == "ma-crossover-local"
    assert config.strategy == "moving_average_crossover"
    assert config.data == ExperimentDataConfig(
        source="csv",
        paths={
            "MSFT": "data/cache/MSFT.csv",
            "AAPL": "data/cache/AAPL.csv",
        },
    )
    assert config.parameters == MovingAverageCrossoverParameters(
        fast_window=20,
        slow_window=50,
        initial_capital=1_000.0,
        transaction_cost_rate=0.001,
        slippage_rate=0.0005,
    )
    assert config.evaluation == ExperimentEvaluationConfig(252.0, 0.02)


def test_loads_cache_source_config_with_defaults(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
experiment:
  name: ma-crossover-cache
  strategy: moving_average_crossover
data:
  source: cache
  cache_dir: data/cache
  symbols: [" aapl ", msft]
parameters:
  fast_window: 20
  slow_window: 50
""",
    )

    config = load_experiment_config(path)

    assert config.data == ExperimentDataConfig(
        source="cache",
        cache_dir="data/cache",
        symbols=("AAPL", "MSFT"),
    )
    assert config.parameters == MovingAverageCrossoverParameters(20, 50)
    assert config.evaluation == ExperimentEvaluationConfig()


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "must not be empty"),
        ("- one\n- two\n", "top-level mapping"),
        ("experiment: [invalid", "valid YAML"),
        ("data: {}\nparameters: {}\n", "experiment must be a mapping"),
        (
            "experiment: {name: test, strategy: unsupported}\ndata: {}\nparameters: {}\n",
            "experiment.strategy",
        ),
        (
            "experiment: {name: test, strategy: moving_average_crossover}\nparameters: {}\n",
            "data section is required",
        ),
        (
            "experiment: {name: test, strategy: moving_average_crossover}\ndata: {}\n",
            "parameters section is required",
        ),
    ],
)
def test_rejects_invalid_documents(
    tmp_path: Path, content: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_experiment_config(write_config(tmp_path, content))


def valid_config(data: str, parameters: str | None = None) -> str:
    parameters = parameters or "fast_window: 20\n  slow_window: 50"
    return f"""experiment:
  name: test
  strategy: moving_average_crossover
data:
  {data}
parameters:
  {parameters}
"""


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ("source: remote", "data.source"),
        ("source: csv\n  paths: {}", "data.paths must not be empty"),
        ("source: csv\n  paths: {'  ': prices.csv}", "symbol"),
        (
            "source: csv\n  paths: {AAPL: first.csv, ' aapl ': second.csv}",
            "duplicate symbol: AAPL",
        ),
        ("source: cache\n  cache_dir: data/cache\n  symbols: []", "data.symbols"),
        (
            "source: cache\n  cache_dir: data/cache\n  symbols: [MSFT, ' msft ']",
            "duplicate symbol: MSFT",
        ),
    ],
)
def test_rejects_invalid_data(tmp_path: Path, data: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_experiment_config(write_config(tmp_path, valid_config(data)))


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ("fast_window: 0\n  slow_window: 50", "fast_window"),
        ("fast_window: 20\n  slow_window: 20", "must be less than"),
        (
            "fast_window: 20\n  slow_window: 50\n  initial_capital: 0",
            "initial_capital",
        ),
        (
            "fast_window: 20\n  slow_window: 50\n  transaction_cost_rate: -0.1",
            "transaction_cost_rate",
        ),
        (
            "fast_window: 20\n  slow_window: 50\n  slippage_rate: -0.1",
            "slippage_rate",
        ),
    ],
)
def test_rejects_invalid_parameters(
    tmp_path: Path, parameters: str, message: str
) -> None:
    content = valid_config(
        "source: cache\n  cache_dir: data/cache\n  symbols: [AAPL]",
        parameters,
    )
    with pytest.raises(ValueError, match=message):
        load_experiment_config(write_config(tmp_path, content))


def test_rejects_invalid_evaluation_frequency(tmp_path: Path) -> None:
    content = valid_config(
        "source: cache\n  cache_dir: data/cache\n  symbols: [AAPL]"
    )
    content += "evaluation:\n  periods_per_year: 0\n"

    with pytest.raises(ValueError, match="periods_per_year"):
        load_experiment_config(write_config(tmp_path, content))


def test_public_config_api_is_exported() -> None:
    from el_psy_quant import config

    assert config.ExperimentConfig is ExperimentConfig
    assert config.load_experiment_config is load_experiment_config
