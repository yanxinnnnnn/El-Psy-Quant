from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.data import (
    cache_path,
    read_daily_prices_cache,
    write_daily_prices_cache,
)


def make_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [105, 100],
            "High": [112, 110],
            "Low": [104, 99],
            "Close": [110, 105],
            "Volume": [1200, 1000],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-01"]),
    )


def test_cache_path_uses_symbol_filename(tmp_path: Path) -> None:
    assert cache_path(tmp_path, "AAPL") == tmp_path / "AAPL.csv"


def test_cache_path_normalizes_lowercase_symbol(tmp_path: Path) -> None:
    assert cache_path(tmp_path, "msft") == tmp_path / "MSFT.csv"


def test_cache_path_replaces_unsafe_characters(tmp_path: Path) -> None:
    assert cache_path(tmp_path, "brk/b:c d\\e") == tmp_path / "BRK_B_C_D_E.csv"


def test_cache_path_rejects_empty_symbol(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="symbol must not be empty"):
        cache_path(tmp_path, "   ")


def test_write_cache_creates_file_and_returns_path(tmp_path: Path) -> None:
    path = write_daily_prices_cache(make_prices(), tmp_path, "AAPL")

    assert path == tmp_path / "AAPL.csv"
    assert path.is_file()


def test_write_cache_creates_cache_directory(tmp_path: Path) -> None:
    cache_dir = tmp_path / "nested" / "cache"

    write_daily_prices_cache(make_prices(), cache_dir, "AAPL")

    assert cache_dir.is_dir()


def test_written_cache_can_be_read_back(tmp_path: Path) -> None:
    prices = make_prices()
    write_daily_prices_cache(prices, tmp_path, "AAPL")

    result = read_daily_prices_cache(tmp_path, "AAPL")

    expected = prices.sort_index().rename_axis("Date")
    pd.testing.assert_frame_equal(result, expected)


def test_written_rows_are_sorted_ascending(tmp_path: Path) -> None:
    write_daily_prices_cache(make_prices(), tmp_path, "AAPL")

    result = read_daily_prices_cache(tmp_path, "AAPL")

    assert result.index.is_monotonic_increasing


def test_missing_required_column_raises_value_error(tmp_path: Path) -> None:
    prices = make_prices().drop(columns="Volume")

    with pytest.raises(ValueError, match="missing required columns: Volume"):
        write_daily_prices_cache(prices, tmp_path, "AAPL")


def test_empty_prices_raise_value_error(tmp_path: Path) -> None:
    prices = make_prices().iloc[0:0]

    with pytest.raises(ValueError, match="prices must not be empty"):
        write_daily_prices_cache(prices, tmp_path, "AAPL")


def test_non_datetime_index_raises_value_error(tmp_path: Path) -> None:
    prices = make_prices().reset_index(drop=True)

    with pytest.raises(ValueError, match="must have a DatetimeIndex"):
        write_daily_prices_cache(prices, tmp_path, "AAPL")


def test_duplicate_dates_raise_value_error(tmp_path: Path) -> None:
    prices = make_prices()
    prices.index = pd.to_datetime(["2024-01-01", "2024-01-01"])

    with pytest.raises(ValueError, match="must not contain duplicate dates"):
        write_daily_prices_cache(prices, tmp_path, "AAPL")


def test_nan_close_raises_value_error(tmp_path: Path) -> None:
    prices = make_prices()
    prices.iloc[0, prices.columns.get_loc("Close")] = float("nan")

    with pytest.raises(ValueError, match="Close must not contain NaN"):
        write_daily_prices_cache(prices, tmp_path, "AAPL")


def test_read_missing_cache_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_daily_prices_cache(tmp_path, "AAPL")


def test_cache_functions_are_exported_from_data_package() -> None:
    from el_psy_quant import data

    assert data.cache_path is cache_path
    assert data.read_daily_prices_cache is read_daily_prices_cache
    assert data.write_daily_prices_cache is write_daily_prices_cache

