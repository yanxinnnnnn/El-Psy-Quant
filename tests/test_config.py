from pathlib import Path
from textwrap import dedent, indent

import pytest

from el_psy_quant.config import (
    ExperimentConfig,
    ExperimentDataConfig,
    ExperimentEvaluationConfig,
    MovingAverageCrossoverParameters,
    PaperRunConfig,
    create_paper_run_request_from_config,
    load_experiment_config,
)
from el_psy_quant.paper import (
    PaperAccountState,
    PaperFill,
    PaperOrderRecord,
    PaperRunRequest,
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
    assert config.paper_run is None


def test_loads_config_with_valid_paper_run_section(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
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
      aapl: 0.0
  ending_account_state:
    timestamp: "2026-07-08T00:01:00Z"
    starting_cash: 10000.0
    current_cash: 9900.0
    positions:
      AAPL: 1.0
  orders:
    - order_id: order-001
      timestamp: "2026-07-08T00:00:30Z"
      symbol: aapl
      side: buy
      quantity: 1.0
      status: filled
  fills:
    - timestamp: "2026-07-08T00:00:45Z"
      symbol: aapl
      side: buy
      quantity: 1.0
      price: 100.0
      order_id: order-001
""",
    )

    config = load_experiment_config(path)

    assert isinstance(config.paper_run, PaperRunConfig)
    assert config.paper_run.run_id == "paper-run-001"
    assert config.paper_run.created_timestamp == "2026-07-08T00:00:00Z"
    assert isinstance(config.paper_run.starting_account_state, PaperAccountState)
    assert isinstance(config.paper_run.ending_account_state, PaperAccountState)
    assert config.paper_run.starting_account_state.positions == (("AAPL", 0.0),)
    assert config.paper_run.ending_account_state.positions == (("AAPL", 1.0),)
    assert config.paper_run.orders[0].symbol == "AAPL"
    assert config.paper_run.orders[0].side == "buy"
    assert config.paper_run.orders[0].status == "filled"
    assert isinstance(config.paper_run.orders[0], PaperOrderRecord)
    assert config.paper_run.fills[0].symbol == "AAPL"
    assert config.paper_run.fills[0].order_id == "order-001"
    assert isinstance(config.paper_run.fills[0], PaperFill)


def test_converts_paper_run_config_to_paper_run_request(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
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
  run_id: " paper-run-001 "
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
""",
    )
    config = load_experiment_config(path)
    assert config.paper_run is not None

    request = create_paper_run_request_from_config(config.paper_run)

    assert isinstance(request, PaperRunRequest)
    assert request.run_id == "paper-run-001"
    assert request.created_timestamp.isoformat() == "2026-07-08T00:00:00+00:00"
    assert request.starting_account_state is config.paper_run.starting_account_state
    assert request.ending_account_state is config.paper_run.ending_account_state
    assert request.orders == config.paper_run.orders
    assert request.fills == config.paper_run.fills


def test_rejects_invalid_paper_run_request_conversion_input() -> None:
    with pytest.raises(ValueError, match="PaperRunConfig"):
        create_paper_run_request_from_config(object())  # type: ignore[arg-type]


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


def valid_config_with_paper_run(paper_run: str) -> str:
    paper_run = indent(dedent(paper_run).strip(), "  ")
    return f"""experiment:
  name: test
  strategy: moving_average_crossover
data:
  source: cache
  cache_dir: data/cache
  symbols: [AAPL]
parameters:
  fast_window: 20
  slow_window: 50
paper_run:
{paper_run}
"""


@pytest.mark.parametrize(
    ("paper_run", "message"),
    [
        ("created_timestamp: '2026-07-08T00:00:00Z'", "paper_run.run_id"),
        (
            "run_id: ''\ncreated_timestamp: '2026-07-08T00:00:00Z'",
            "paper_run.run_id",
        ),
        ("run_id: paper-run-001", "paper_run.created_timestamp"),
        (
            "run_id: paper-run-001\ncreated_timestamp: not-a-date",
            "paper_run.created_timestamp",
        ),
        (
            "run_id: paper-run-001\ncreated_timestamp: '2026-07-08T00:00:00Z'",
            "paper_run.starting_account_state",
        ),
    ],
)
def test_rejects_invalid_paper_run_required_fields(
    tmp_path: Path,
    paper_run: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        load_experiment_config(
            write_config(tmp_path, valid_config_with_paper_run(paper_run))
        )


@pytest.mark.parametrize(
    ("account_state", "message"),
    [
        (
            "timestamp: not-a-date\nstarting_cash: 10000\ncurrent_cash: 10000\npositions: {AAPL: 0}",
            "timestamp",
        ),
        (
            "timestamp: '2026-07-08T00:00:00Z'\ncurrent_cash: 10000\npositions: {AAPL: 0}",
            "starting_cash",
        ),
        (
            "timestamp: '2026-07-08T00:00:00Z'\nstarting_cash: -1\ncurrent_cash: 10000\npositions: {AAPL: 0}",
            "starting_cash",
        ),
        (
            "timestamp: '2026-07-08T00:00:00Z'\nstarting_cash: 10000\ncurrent_cash: 10000\npositions: []",
            "positions",
        ),
        (
            "timestamp: '2026-07-08T00:00:00Z'\nstarting_cash: 10000\ncurrent_cash: 10000\npositions: {' ': 0}",
            "symbol",
        ),
    ],
)
def test_rejects_invalid_paper_account_state_fields(
    tmp_path: Path,
    account_state: str,
    message: str,
) -> None:
    account_state = indent(dedent(account_state).strip(), "  ")
    paper_run = f"""run_id: paper-run-001
created_timestamp: '2026-07-08T00:00:00Z'
starting_account_state:
{account_state}
ending_account_state:
  timestamp: '2026-07-08T00:01:00Z'
  starting_cash: 10000
  current_cash: 9900
  positions: {{AAPL: 1}}
orders: []
fills: []"""

    with pytest.raises(ValueError, match=message):
        load_experiment_config(
            write_config(tmp_path, valid_config_with_paper_run(paper_run))
        )


@pytest.mark.parametrize(
    ("orders", "message"),
    [
        ("not-a-list", "paper_run.orders must be a list"),
        (
            "- timestamp: '2026-07-08T00:00:30Z'\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  status: filled",
            "order_id",
        ),
        (
            "- order_id: order-001\n  timestamp: bad\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  status: filled",
            "timestamp",
        ),
        (
            "- order_id: order-001\n  timestamp: '2026-07-08T00:00:30Z'\n  symbol: ''\n  side: buy\n  quantity: 1\n  status: filled",
            "symbol",
        ),
        (
            "- order_id: order-001\n  timestamp: '2026-07-08T00:00:30Z'\n  symbol: AAPL\n  side: hold\n  quantity: 1\n  status: filled",
            "side",
        ),
        (
            "- order_id: order-001\n  timestamp: '2026-07-08T00:00:30Z'\n  symbol: AAPL\n  side: buy\n  quantity: 0\n  status: filled",
            "quantity",
        ),
        (
            "- order_id: order-001\n  timestamp: '2026-07-08T00:00:30Z'\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  status: pending",
            "status",
        ),
        (
            "- order_id: order-001\n  timestamp: '2026-07-08T00:00:30Z'\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  status: filled\n- order_id: order-001\n  timestamp: '2026-07-08T00:00:31Z'\n  symbol: MSFT\n  side: buy\n  quantity: 1\n  status: filled",
            "duplicate order_id: order-001",
        ),
    ],
)
def test_rejects_invalid_paper_orders(
    tmp_path: Path,
    orders: str,
    message: str,
) -> None:
    orders = indent(dedent(orders).strip(), "  ")
    paper_run = f"""run_id: paper-run-001
created_timestamp: '2026-07-08T00:00:00Z'
starting_account_state:
  timestamp: '2026-07-08T00:00:00Z'
  starting_cash: 10000
  current_cash: 10000
  positions: {{AAPL: 0}}
ending_account_state:
  timestamp: '2026-07-08T00:01:00Z'
  starting_cash: 10000
  current_cash: 9900
  positions: {{AAPL: 1}}
orders:
{orders}
fills: []"""

    with pytest.raises(ValueError, match=message):
        load_experiment_config(
            write_config(tmp_path, valid_config_with_paper_run(paper_run))
        )


@pytest.mark.parametrize(
    ("fills", "message"),
    [
        ("not-a-list", "paper_run.fills must be a list"),
        (
            "- symbol: AAPL\n  side: buy\n  quantity: 1\n  price: 100",
            "timestamp",
        ),
        (
            "- timestamp: bad\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  price: 100",
            "timestamp",
        ),
        (
            "- timestamp: '2026-07-08T00:00:45Z'\n  symbol: ''\n  side: buy\n  quantity: 1\n  price: 100",
            "symbol",
        ),
        (
            "- timestamp: '2026-07-08T00:00:45Z'\n  symbol: AAPL\n  side: hold\n  quantity: 1\n  price: 100",
            "side",
        ),
        (
            "- timestamp: '2026-07-08T00:00:45Z'\n  symbol: AAPL\n  side: buy\n  quantity: 0\n  price: 100",
            "quantity",
        ),
        (
            "- timestamp: '2026-07-08T00:00:45Z'\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  price: -1",
            "price",
        ),
        (
            "- timestamp: '2026-07-08T00:00:45Z'\n  symbol: AAPL\n  side: buy\n  quantity: 1\n  price: 100\n  order_id: ''",
            "order_id",
        ),
    ],
)
def test_rejects_invalid_paper_fills(
    tmp_path: Path,
    fills: str,
    message: str,
) -> None:
    fills = indent(dedent(fills).strip(), "  ")
    paper_run = f"""run_id: paper-run-001
created_timestamp: '2026-07-08T00:00:00Z'
starting_account_state:
  timestamp: '2026-07-08T00:00:00Z'
  starting_cash: 10000
  current_cash: 10000
  positions: {{AAPL: 0}}
ending_account_state:
  timestamp: '2026-07-08T00:01:00Z'
  starting_cash: 10000
  current_cash: 9900
  positions: {{AAPL: 1}}
orders: []
fills:
{fills}"""

    with pytest.raises(ValueError, match=message):
        load_experiment_config(
            write_config(tmp_path, valid_config_with_paper_run(paper_run))
        )


def test_public_config_api_is_exported() -> None:
    from el_psy_quant import config

    assert config.ExperimentConfig is ExperimentConfig
    assert config.PaperRunConfig is PaperRunConfig
    assert (
        config.create_paper_run_request_from_config
        is create_paper_run_request_from_config
    )
    assert config.load_experiment_config is load_experiment_config
