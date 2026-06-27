import pandas as pd
import pytest

from el_psy_quant.portfolio import long_only_position


def test_basic_signal_to_position_conversion() -> None:
    signal = pd.Series([0, 1, 0, 0, -1, 0, 1])

    result = long_only_position(signal)

    expected = pd.Series([0, 1, 1, 1, 0, 0, 1], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_first_hold_signal_starts_flat() -> None:
    result = long_only_position(pd.Series([0, 0]))

    expected = pd.Series([0, 0], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_first_buy_signal_enters_long() -> None:
    result = long_only_position(pd.Series([1, 0]))

    expected = pd.Series([1, 1], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_first_sell_signal_remains_flat() -> None:
    result = long_only_position(pd.Series([-1, 0]))

    expected = pd.Series([0, 0], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_repeated_buy_signals_remain_long() -> None:
    result = long_only_position(pd.Series([1, 1, 1]))

    expected = pd.Series([1, 1, 1], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_repeated_sell_signals_remain_flat() -> None:
    result = long_only_position(pd.Series([-1, -1, -1]))

    expected = pd.Series([0, 0, 0], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_position_preserves_index() -> None:
    index = pd.Index(["day-1", "day-2", "day-3"])
    signal = pd.Series([0, 1, 0], index=index)

    result = long_only_position(signal)

    assert result.index.equals(index)


def test_position_dtype_is_integer() -> None:
    result = long_only_position(pd.Series([0, 1]))

    assert pd.api.types.is_integer_dtype(result.dtype)


def test_invalid_signal_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must be -1, 0, or 1"):
        long_only_position(pd.Series([0, 2]))


def test_nan_signal_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not contain NaN"):
        long_only_position(pd.Series([0.0, float("nan")]))

