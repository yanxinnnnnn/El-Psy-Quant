import pandas as pd
import pytest

from el_psy_quant.portfolio import strategy_return


def test_strategy_return_uses_previous_day_position() -> None:
    position = pd.Series([0, 1, 1, 0])
    asset_return = pd.Series([float("nan"), 0.10, -0.05, 0.02])

    result = strategy_return(position, asset_return)

    expected = pd.Series([0.0, 0.0, -0.05, 0.02])
    pd.testing.assert_series_equal(result, expected)


def test_first_strategy_return_is_zero_when_asset_return_is_nan() -> None:
    result = strategy_return(
        pd.Series([1, 1]),
        pd.Series([float("nan"), 0.10]),
    )

    assert result.iloc[0] == 0.0


def test_indexes_must_match() -> None:
    position = pd.Series([0, 1], index=["a", "b"])
    asset_return = pd.Series([0.0, 0.1], index=["a", "c"])

    with pytest.raises(ValueError, match="indexes must be equal"):
        strategy_return(position, asset_return)


def test_strategy_return_preserves_index() -> None:
    index = pd.Index(["day-1", "day-2"])
    position = pd.Series([0, 1], index=index)
    asset_return = pd.Series([float("nan"), 0.1], index=index)

    result = strategy_return(position, asset_return)

    assert result.index.equals(index)


def test_position_nan_raises_value_error() -> None:
    with pytest.raises(ValueError, match="position must not contain NaN"):
        strategy_return(
            pd.Series([0.0, float("nan")]),
            pd.Series([float("nan"), 0.1]),
        )


def test_invalid_position_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="position values must be 0 or 1"):
        strategy_return(
            pd.Series([0, 2]),
            pd.Series([float("nan"), 0.1]),
        )


def test_asset_return_nan_after_first_row_raises_value_error() -> None:
    with pytest.raises(ValueError, match="after the first row"):
        strategy_return(
            pd.Series([0, 1, 1]),
            pd.Series([float("nan"), 0.1, float("nan")]),
        )


def test_strategy_return_dtype_is_float() -> None:
    result = strategy_return(
        pd.Series([0, 1]),
        pd.Series([float("nan"), 0.1]),
    )

    assert pd.api.types.is_float_dtype(result.dtype)


def test_zero_position_produces_zero_returns() -> None:
    result = strategy_return(
        pd.Series([0, 0, 0]),
        pd.Series([float("nan"), 0.1, -0.2]),
    )

    expected = pd.Series([0.0, 0.0, -0.0])
    pd.testing.assert_series_equal(result, expected)

