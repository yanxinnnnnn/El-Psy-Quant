import pandas as pd
import pytest

from el_psy_quant.indicators import (
    daily_return,
    exponential_moving_average,
    simple_moving_average,
)


def test_simple_moving_average() -> None:
    series = pd.Series([1.0, 2.0, 3.0, 4.0])

    result = simple_moving_average(series, window=3)

    expected = pd.Series([float("nan"), float("nan"), 2.0, 3.0])
    pd.testing.assert_series_equal(result, expected)


def test_simple_moving_average_preserves_index() -> None:
    index = pd.Index(["a", "b", "c"])
    series = pd.Series([1.0, 2.0, 3.0], index=index)

    result = simple_moving_average(series, window=2)

    assert result.index.equals(index)


@pytest.mark.parametrize("window", [0, -1])
def test_simple_moving_average_rejects_non_positive_window(window: int) -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        simple_moving_average(pd.Series([1.0]), window=window)


def test_exponential_moving_average() -> None:
    series = pd.Series([1.0, 2.0, 3.0])

    result = exponential_moving_average(series, span=2)

    expected = pd.Series([1.0, 5.0 / 3.0, 23.0 / 9.0])
    pd.testing.assert_series_equal(result, expected)


def test_exponential_moving_average_preserves_index() -> None:
    index = pd.Index(["a", "b", "c"])
    series = pd.Series([1.0, 2.0, 3.0], index=index)

    result = exponential_moving_average(series, span=2)

    assert result.index.equals(index)


@pytest.mark.parametrize("span", [0, -1])
def test_exponential_moving_average_rejects_non_positive_span(span: int) -> None:
    with pytest.raises(ValueError, match="span must be positive"):
        exponential_moving_average(pd.Series([1.0]), span=span)


def test_daily_return() -> None:
    series = pd.Series([100.0, 110.0, 99.0])

    result = daily_return(series)

    expected = pd.Series([float("nan"), 0.1, -0.1])
    pd.testing.assert_series_equal(result, expected)


def test_daily_return_preserves_first_nan() -> None:
    result = daily_return(pd.Series([100.0, 110.0]))

    assert pd.isna(result.iloc[0])

