import pandas as pd
import pytest

from el_psy_quant.signals import crossover_signal


def test_bullish_crossover_emits_one() -> None:
    fast = pd.Series([1.0, 2.0, 3.0])
    slow = pd.Series([2.0, 2.0, 2.0])

    result = crossover_signal(fast, slow)

    expected = pd.Series([0, 0, 1], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_bearish_crossover_emits_minus_one() -> None:
    fast = pd.Series([3.0, 2.0, 1.0])
    slow = pd.Series([2.0, 2.0, 2.0])

    result = crossover_signal(fast, slow)

    expected = pd.Series([0, 0, -1], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_signal_is_not_repeated_while_fast_remains_above_slow() -> None:
    fast = pd.Series([1.0, 3.0, 4.0, 5.0])
    slow = pd.Series([2.0, 2.0, 2.0, 2.0])

    result = crossover_signal(fast, slow)

    expected = pd.Series([0, 1, 0, 0], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_different_indexes_raise_value_error() -> None:
    fast = pd.Series([1.0, 2.0], index=["a", "b"])
    slow = pd.Series([1.0, 2.0], index=["a", "c"])

    with pytest.raises(ValueError, match="indexes must be equal"):
        crossover_signal(fast, slow)


def test_signal_preserves_index() -> None:
    index = pd.Index(["day-1", "day-2", "day-3"])
    fast = pd.Series([1.0, 2.0, 3.0], index=index)
    slow = pd.Series([2.0, 2.0, 2.0], index=index)

    result = crossover_signal(fast, slow)

    assert result.index.equals(index)


def test_nan_values_do_not_emit_false_signals() -> None:
    fast = pd.Series([1.0, float("nan"), 3.0, 4.0])
    slow = pd.Series([2.0, 2.0, 2.0, 2.0])

    result = crossover_signal(fast, slow)

    expected = pd.Series([0, 0, 0, 0], dtype="int64")
    pd.testing.assert_series_equal(result, expected)


def test_signal_dtype_is_integer() -> None:
    result = crossover_signal(
        pd.Series([1.0, 3.0]),
        pd.Series([2.0, 2.0]),
    )

    assert pd.api.types.is_integer_dtype(result.dtype)

