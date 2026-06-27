import pandas as pd
import pytest

from el_psy_quant.performance import max_drawdown, total_return


def test_total_return() -> None:
    result = total_return(pd.Series([1_000.0, 1_100.0, 1_050.0]))

    assert result == pytest.approx(0.05)


def test_flat_equity_has_zero_total_return() -> None:
    assert total_return(pd.Series([100.0, 100.0])) == 0.0


def test_negative_total_return() -> None:
    result = total_return(pd.Series([100.0, 80.0]))

    assert result == pytest.approx(-0.20)


def test_empty_equity_raises_for_total_return() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        total_return(pd.Series([], dtype=float))


def test_nan_equity_raises_for_total_return() -> None:
    with pytest.raises(ValueError, match="must not contain NaN"):
        total_return(pd.Series([100.0, float("nan")]))


@pytest.mark.parametrize("starting_equity", [0.0, -1.0])
def test_non_positive_starting_equity_raises_for_total_return(
    starting_equity: float,
) -> None:
    with pytest.raises(ValueError, match="starting equity must be positive"):
        total_return(pd.Series([starting_equity, 100.0]))


def test_max_drawdown() -> None:
    result = max_drawdown(pd.Series([1_000.0, 1_200.0, 900.0, 1_500.0]))

    assert result == pytest.approx(-0.25)


def test_increasing_equity_has_zero_max_drawdown() -> None:
    assert max_drawdown(pd.Series([100.0, 110.0, 120.0])) == 0.0


def test_empty_equity_raises_for_max_drawdown() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        max_drawdown(pd.Series([], dtype=float))


def test_nan_equity_raises_for_max_drawdown() -> None:
    with pytest.raises(ValueError, match="must not contain NaN"):
        max_drawdown(pd.Series([100.0, float("nan")]))


@pytest.mark.parametrize("invalid_equity", [0.0, -1.0])
def test_non_positive_equity_raises_for_max_drawdown(invalid_equity: float) -> None:
    with pytest.raises(ValueError, match="equity values must be positive"):
        max_drawdown(pd.Series([100.0, invalid_equity]))

