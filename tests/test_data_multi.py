from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.data import (
    load_daily_prices_csvs,
    read_daily_prices_caches,
    write_daily_prices_cache,
)


def make_prices(offset: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [10.0 + offset, 11.0 + offset],
            "High": [11.0 + offset, 12.0 + offset],
            "Low": [9.0 + offset, 10.0 + offset],
            "Close": [10.5 + offset, 11.5 + offset],
            "Volume": [100, 110],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )


def write_csv(path: Path, prices: pd.DataFrame) -> None:
    prices.to_csv(path, index=True, index_label="Date")


def test_loads_csvs_with_normalized_symbols_in_input_order(tmp_path: Path) -> None:
    aapl_path = tmp_path / "aapl.csv"
    msft_path = tmp_path / "msft.csv"
    write_csv(aapl_path, make_prices())
    write_csv(msft_path, make_prices(10.0))

    result = load_daily_prices_csvs(
        {" aapl ": aapl_path, "msft": msft_path}
    )

    assert list(result) == ["AAPL", "MSFT"]
    pd.testing.assert_frame_equal(result["AAPL"], make_prices().rename_axis("Date"))
    pd.testing.assert_frame_equal(
        result["MSFT"], make_prices(10.0).rename_axis("Date")
    )


def test_load_csvs_rejects_empty_mapping() -> None:
    with pytest.raises(ValueError, match="paths_by_symbol must not be empty"):
        load_daily_prices_csvs({})


@pytest.mark.parametrize(
    ("paths", "message"),
    [
        ({"  ": "unused.csv"}, "symbol must not be empty"),
        (
            {"AAPL": "first.csv", " aapl ": "second.csv"},
            "duplicate symbol: AAPL",
        ),
    ],
)
def test_load_csvs_rejects_invalid_symbols(
    paths: dict[str, str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_daily_prices_csvs(paths)


def test_load_csvs_propagates_csv_validation_errors(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "Close": [10.0]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing required columns"):
        load_daily_prices_csvs({"AAPL": path})


def test_reads_caches_with_normalized_symbols_in_input_order(tmp_path: Path) -> None:
    write_daily_prices_cache(make_prices(), tmp_path, "AAPL")
    write_daily_prices_cache(make_prices(10.0), tmp_path, "MSFT")

    result = read_daily_prices_caches(tmp_path, [" msft ", "aapl"])

    assert list(result) == ["MSFT", "AAPL"]
    pd.testing.assert_frame_equal(
        result["MSFT"], make_prices(10.0).rename_axis("Date")
    )


@pytest.mark.parametrize(
    ("symbols", "message"),
    [
        ([], "symbols must not be empty"),
        (["  "], "symbol must not be empty"),
        (["MSFT", " msft "], "duplicate symbol: MSFT"),
    ],
)
def test_read_caches_rejects_invalid_symbols(
    tmp_path: Path, symbols: list[str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        read_daily_prices_caches(tmp_path, symbols)


def test_read_caches_propagates_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_daily_prices_caches(tmp_path, ["AAPL"])


def test_multi_symbol_helpers_are_exported() -> None:
    from el_psy_quant import data

    assert data.load_daily_prices_csvs is load_daily_prices_csvs
    assert data.read_daily_prices_caches is read_daily_prices_caches
