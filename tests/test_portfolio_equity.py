import pandas as pd
import pytest

from el_psy_quant.portfolio import equity_curve


def test_equity_curve_compounds_returns() -> None:
    strategy_return = pd.Series([0.0, 0.10, -0.05])

    result = equity_curve(strategy_return)

    expected = pd.Series([1.0, 1.1, 1.045])
    pd.testing.assert_series_equal(result, expected)


def test_equity_curve_uses_custom_initial_capital() -> None:
    strategy_return = pd.Series([0.0, 0.10, -0.05])

    result = equity_curve(strategy_return, initial_capital=1_000.0)

    expected = pd.Series([1_000.0, 1_100.0, 1_045.0])
    pd.testing.assert_series_equal(result, expected)


def test_flat_returns_keep_equity_unchanged() -> None:
    result = equity_curve(pd.Series([0.0, 0.0, 0.0]), initial_capital=100.0)

    expected = pd.Series([100.0, 100.0, 100.0])
    pd.testing.assert_series_equal(result, expected)


def test_negative_return_reduces_equity() -> None:
    result = equity_curve(pd.Series([0.0, -0.25]), initial_capital=100.0)

    expected = pd.Series([100.0, 75.0])
    pd.testing.assert_series_equal(result, expected)


def test_equity_curve_preserves_index() -> None:
    index = pd.Index(["day-1", "day-2"])
    strategy_return = pd.Series([0.0, 0.1], index=index)

    result = equity_curve(strategy_return)

    assert result.index.equals(index)


def test_equity_curve_dtype_is_float() -> None:
    result = equity_curve(pd.Series([0, 1]))

    assert pd.api.types.is_float_dtype(result.dtype)


def test_nan_strategy_return_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not contain NaN"):
        equity_curve(pd.Series([0.0, float("nan")]))


def test_zero_initial_capital_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        equity_curve(pd.Series([0.0]), initial_capital=0.0)


def test_negative_initial_capital_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        equity_curve(pd.Series([0.0]), initial_capital=-1.0)


def test_empty_input_returns_empty_float_series_with_same_index() -> None:
    index = pd.Index([], name="date")
    strategy_return = pd.Series([], index=index, dtype=float)

    result = equity_curve(strategy_return)

    expected = pd.Series([], index=index, dtype=float)
    pd.testing.assert_series_equal(result, expected)

