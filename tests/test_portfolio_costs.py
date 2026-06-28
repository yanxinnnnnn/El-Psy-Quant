import pandas as pd
import pytest

from el_psy_quant.portfolio import transaction_cost


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        ([0, 0, 0], [0.0, 0.0, 0.0]),
        ([0, 1, 1], [0.0, 0.01, 0.0]),
        ([1, 1, 0], [0.01, 0.0, 0.01]),
    ],
)
def test_transaction_cost_charges_position_turnover(
    position: list[int], expected: list[float]
) -> None:
    result = transaction_cost(pd.Series(position), 0.01)

    pd.testing.assert_series_equal(result, pd.Series(expected))


def test_transaction_cost_preserves_index_and_returns_float() -> None:
    index = pd.Index(["day-1", "day-2"])

    result = transaction_cost(pd.Series([0, 1], index=index), 0.01)

    assert result.index.equals(index)
    assert pd.api.types.is_float_dtype(result)


def test_zero_cost_rate_returns_zeros() -> None:
    result = transaction_cost(pd.Series([1, 0, 1]), 0.0)

    pd.testing.assert_series_equal(result, pd.Series([0.0, 0.0, 0.0]))


def test_negative_cost_rate_raises_value_error() -> None:
    with pytest.raises(ValueError, match="cost_rate must not be negative"):
        transaction_cost(pd.Series([0, 1]), -0.01)


def test_nan_position_raises_value_error() -> None:
    with pytest.raises(ValueError, match="position must not contain NaN"):
        transaction_cost(pd.Series([0.0, float("nan")]), 0.01)


def test_invalid_position_raises_value_error() -> None:
    with pytest.raises(ValueError, match="position values must be 0 or 1"):
        transaction_cost(pd.Series([0, 2]), 0.01)


def test_transaction_cost_is_exported_from_portfolio_package() -> None:
    from el_psy_quant import portfolio

    assert portfolio.transaction_cost is transaction_cost
