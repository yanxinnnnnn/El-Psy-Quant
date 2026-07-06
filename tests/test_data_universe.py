import pytest

from el_psy_quant.data import build_symbol_universe, normalize_symbol


def test_normalize_symbol_strips_and_uppercases() -> None:
    assert normalize_symbol(" aapl ") == "AAPL"


@pytest.mark.parametrize("symbol", ["", "   "])
def test_normalize_symbol_rejects_blank_values(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol must not be empty"):
        normalize_symbol(symbol)


def test_build_symbol_universe_normalizes_and_preserves_order() -> None:
    universe = build_symbol_universe(["msft", " AAPL "])

    assert universe == ("MSFT", "AAPL")
    assert isinstance(universe, tuple)


def test_build_symbol_universe_accepts_one_pass_iterable() -> None:
    symbols = (symbol for symbol in ["nvda", "aapl"])

    assert build_symbol_universe(symbols) == ("NVDA", "AAPL")


def test_build_symbol_universe_rejects_single_string_input() -> None:
    with pytest.raises(ValueError, match="not a single symbol"):
        build_symbol_universe("MSFT")


def test_build_symbol_universe_rejects_normalized_duplicates() -> None:
    with pytest.raises(ValueError, match="duplicate symbol: AAPL"):
        build_symbol_universe(["AAPL", " aapl "])


def test_build_symbol_universe_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="symbols must not be empty"):
        build_symbol_universe([])


def test_universe_helpers_are_exported() -> None:
    from el_psy_quant import data

    assert data.normalize_symbol is normalize_symbol
    assert data.build_symbol_universe is build_symbol_universe
