from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.data import load_daily_prices_csv

VALID_CSV = """Date,Open,High,Low,Close,Volume
2024-01-02,105,112,104,110,1200
2024-01-01,100,110,99,105,1000
"""


def write_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "prices.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_csv(tmp_path: Path) -> None:
    prices = load_daily_prices_csv(write_csv(tmp_path, VALID_CSV))

    assert len(prices) == 2
    assert prices.loc["2024-01-01", "Close"] == 105


def test_returns_datetime_index(tmp_path: Path) -> None:
    prices = load_daily_prices_csv(write_csv(tmp_path, VALID_CSV))

    assert isinstance(prices.index, pd.DatetimeIndex)
    assert prices.index.name == "Date"


def test_sorts_rows_by_date_ascending(tmp_path: Path) -> None:
    prices = load_daily_prices_csv(write_csv(tmp_path, VALID_CSV))

    assert prices.index.is_monotonic_increasing


def test_preserves_required_price_columns(tmp_path: Path) -> None:
    prices = load_daily_prices_csv(write_csv(tmp_path, VALID_CSV))

    assert list(prices.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_preserves_optional_adjusted_close_column(tmp_path: Path) -> None:
    content = """Date,Open,High,Low,Close,Adj Close,Volume
2024-01-01,100,110,99,105,104,1000
"""

    prices = load_daily_prices_csv(write_csv(tmp_path, content))

    assert "Adj Close" in prices.columns
    assert prices.iloc[0]["Adj Close"] == 104


def test_missing_required_column_raises_value_error(tmp_path: Path) -> None:
    content = """Date,Open,High,Low,Close
2024-01-01,100,110,99,105
"""

    with pytest.raises(ValueError, match="missing required columns: Volume"):
        load_daily_prices_csv(write_csv(tmp_path, content))


def test_invalid_date_raises_value_error(tmp_path: Path) -> None:
    content = """Date,Open,High,Low,Close,Volume
not-a-date,100,110,99,105,1000
"""

    with pytest.raises(ValueError, match="Date contains invalid values"):
        load_daily_prices_csv(write_csv(tmp_path, content))


def test_duplicate_dates_raise_value_error(tmp_path: Path) -> None:
    content = """Date,Open,High,Low,Close,Volume
2024-01-01,100,110,99,105,1000
2024-01-01,105,112,104,110,1200
"""

    with pytest.raises(ValueError, match="Date contains duplicate values"):
        load_daily_prices_csv(write_csv(tmp_path, content))


def test_nan_close_raises_value_error(tmp_path: Path) -> None:
    content = """Date,Open,High,Low,Close,Volume
2024-01-01,100,110,99,,1000
"""

    with pytest.raises(ValueError, match="Close must not contain NaN"):
        load_daily_prices_csv(write_csv(tmp_path, content))


def test_accepts_path_object(tmp_path: Path) -> None:
    path = write_csv(tmp_path, VALID_CSV)

    prices = load_daily_prices_csv(path)

    assert len(prices) == 2


def test_loader_is_exported_from_data_package() -> None:
    from el_psy_quant import data

    assert data.load_daily_prices_csv is load_daily_prices_csv

