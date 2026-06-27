import importlib.util
from pathlib import Path
from types import ModuleType

from el_psy_quant.data import load_daily_prices_csv

EXAMPLE_PATH = (
    Path(__file__).parents[1] / "examples" / "csv_research_example.py"
)
SAMPLE_CSV = (
    Path(__file__).parents[1]
    / "examples"
    / "data"
    / "sample_daily_prices.csv"
)


def load_example() -> ModuleType:
    spec = importlib.util.spec_from_file_location("csv_research_example", EXAMPLE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_csv_example_module_can_be_imported() -> None:
    example = load_example()

    assert callable(example.main)


def test_main_runs_from_another_working_directory(
    capsys, monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    load_example().main()

    output = capsys.readouterr().out
    assert "summary" in output
    assert "total_return" in output
    assert "max_drawdown" in output


def test_csv_example_does_not_call_yahoo_finance(monkeypatch) -> None:
    def fail_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("example must not access a live data provider")

    monkeypatch.setattr("el_psy_quant.data.providers.yf.download", fail_download)

    load_example().main()


def test_sample_csv_loads_with_usable_close_column() -> None:
    prices = load_daily_prices_csv(SAMPLE_CSV)

    assert "Close" in prices.columns
    assert not prices["Close"].empty
    assert not prices["Close"].isna().any()

