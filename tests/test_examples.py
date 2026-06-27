import importlib.util
from pathlib import Path
from types import ModuleType


def load_example() -> ModuleType:
    path = Path(__file__).parents[1] / "examples" / "minimal_research_example.py"
    spec = importlib.util.spec_from_file_location("minimal_research_example", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_module_can_be_imported() -> None:
    example = load_example()

    assert callable(example.main)


def test_example_main_runs_and_prints_summary(capsys) -> None:
    example = load_example()

    example.main()

    output = capsys.readouterr().out
    assert "summary" in output
    assert "total_return" in output
    assert "max_drawdown" in output


def test_example_does_not_call_yahoo_finance(monkeypatch) -> None:
    def fail_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("example must not access a data provider")

    monkeypatch.setattr("el_psy_quant.data.providers.yf.download", fail_download)

    load_example().main()
