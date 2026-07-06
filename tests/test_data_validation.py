import pandas as pd
import pytest

from el_psy_quant.data import REQUIRED_PRICE_COLUMNS, validate_daily_prices


def make_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 105.0],
            "High": [110.0, 112.0],
            "Low": [99.0, 104.0],
            "Close": [105.0, 110.0],
            "Volume": [1000, 1200],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )


def test_valid_daily_prices_pass_validation() -> None:
    validate_daily_prices(make_prices())


def test_required_price_columns_are_explicit() -> None:
    assert REQUIRED_PRICE_COLUMNS == ("Open", "High", "Low", "Close", "Volume")


def test_non_dataframe_raises_value_error() -> None:
    with pytest.raises(ValueError, match="pandas DataFrame"):
        validate_daily_prices([])  # type: ignore[arg-type]


def test_empty_dataframe_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_daily_prices(make_prices().iloc[0:0])


def test_missing_required_columns_include_names() -> None:
    prices = make_prices().drop(columns=["High", "Volume"])

    with pytest.raises(ValueError, match="High, Volume"):
        validate_daily_prices(prices)


def test_non_datetime_index_raises_value_error() -> None:
    prices = make_prices().reset_index(drop=True)

    with pytest.raises(ValueError, match="DatetimeIndex"):
        validate_daily_prices(prices)


def test_missing_index_value_raises_value_error() -> None:
    prices = make_prices()
    prices.index = pd.DatetimeIndex([pd.Timestamp("2024-01-01"), pd.NaT])

    with pytest.raises(ValueError, match="missing dates"):
        validate_daily_prices(prices)


def test_duplicate_dates_raise_value_error() -> None:
    prices = make_prices()
    prices.index = pd.to_datetime(["2024-01-01", "2024-01-01"])

    with pytest.raises(ValueError, match="duplicate dates"):
        validate_daily_prices(prices)


def test_missing_close_value_raises_value_error() -> None:
    prices = make_prices()
    prices.loc[prices.index[0], "Close"] = float("nan")

    with pytest.raises(ValueError, match="Close must not contain NaN"):
        validate_daily_prices(prices)


def test_non_numeric_close_raises_value_error() -> None:
    prices = make_prices()
    prices["Close"] = ["105", "110"]

    with pytest.raises(ValueError, match="Close must contain numeric values"):
        validate_daily_prices(prices)


def test_validation_does_not_mutate_input() -> None:
    prices = make_prices().iloc[::-1]
    before = prices.copy(deep=True)

    validate_daily_prices(prices)

    pd.testing.assert_frame_equal(prices, before)
