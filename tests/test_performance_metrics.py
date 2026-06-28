import pandas as pd
import pytest

from el_psy_quant.performance import (
    annualized_volatility,
    cagr,
    max_drawdown,
    total_return,
)


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


def test_cagr_uses_elapsed_periods() -> None:
    result = cagr(pd.Series([100.0, 110.0, 121.0]), periods_per_year=1)

    assert result == pytest.approx(0.10)


@pytest.mark.parametrize(
    ("equity", "periods_per_year", "message"),
    [
        ([], 1, "equity must not be empty"),
        ([100.0, float("nan")], 1, "equity must not contain NaN"),
        ([100.0, 0.0], 1, "equity values must be positive"),
        ([100.0, 110.0], 0, "periods_per_year must be positive"),
        ([100.0], 1, "equity must contain at least two points"),
    ],
)
def test_cagr_rejects_invalid_inputs(
    equity: list[float], periods_per_year: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        cagr(pd.Series(equity, dtype=float), periods_per_year)


def test_annualized_volatility_uses_sample_standard_deviation() -> None:
    returns = pd.Series([0.01, -0.01, 0.02])

    result = annualized_volatility(returns, periods_per_year=252)

    assert result == pytest.approx(returns.std(ddof=1) * 252**0.5)


@pytest.mark.parametrize(
    ("returns", "periods_per_year", "message"),
    [
        ([], 1, "returns must not be empty"),
        ([0.0, float("nan")], 1, "returns must not contain NaN"),
        ([0.0, 0.1], 0, "periods_per_year must be positive"),
        ([0.0], 1, "returns must contain at least two observations"),
    ],
)
def test_annualized_volatility_rejects_invalid_inputs(
    returns: list[float], periods_per_year: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        annualized_volatility(pd.Series(returns, dtype=float), periods_per_year)


def test_annualized_metrics_are_exported() -> None:
    from el_psy_quant import performance

    assert performance.cagr is cagr
    assert performance.annualized_volatility is annualized_volatility

