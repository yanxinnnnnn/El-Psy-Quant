import json

import pandas as pd
import pytest

from el_psy_quant.performance import annualized_volatility
from el_psy_quant.portfolio import portfolio_risk_summary


def make_portfolio_return() -> pd.Series:
    return pd.Series(
        [0.02, -0.01, 0.0, 0.03, -0.02],
        index=pd.date_range("2024-01-01", periods=5, freq="D"),
        name="portfolio_return",
    )


def test_risk_summary_contains_required_metrics() -> None:
    result = portfolio_risk_summary(make_portfolio_return())

    assert set(result) == {
        "periods",
        "mean_return",
        "volatility",
        "min_return",
        "max_return",
        "positive_periods",
        "negative_periods",
        "zero_periods",
        "loss_rate",
    }


def test_counts_and_loss_rate_are_correct() -> None:
    result = portfolio_risk_summary(make_portfolio_return())

    assert result["periods"] == 5.0
    assert result["positive_periods"] == 2.0
    assert result["negative_periods"] == 2.0
    assert result["zero_periods"] == 1.0
    assert result["loss_rate"] == 0.4


def test_distribution_metrics_use_sample_volatility() -> None:
    portfolio_return = make_portfolio_return()

    result = portfolio_risk_summary(portfolio_return)

    assert result["mean_return"] == pytest.approx(portfolio_return.mean())
    assert result["volatility"] == pytest.approx(
        portfolio_return.std(ddof=1)
    )
    assert result["min_return"] == -0.02
    assert result["max_return"] == 0.03


def test_annualized_volatility_is_optional() -> None:
    portfolio_return = make_portfolio_return()

    without_annualized = portfolio_risk_summary(portfolio_return)
    with_annualized = portfolio_risk_summary(
        portfolio_return,
        periods_per_year=252,
    )

    assert "annualized_volatility" not in without_annualized
    assert with_annualized["annualized_volatility"] == pytest.approx(
        annualized_volatility(portfolio_return, 252)
    )


def test_values_are_plain_json_compatible_numbers() -> None:
    result = portfolio_risk_summary(make_portfolio_return(), periods_per_year=252)

    assert all(type(value) is float for value in result.values())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("portfolio_return", "message"),
    [
        ([], "pandas Series"),
        (pd.Series(dtype=float), "must not be empty"),
        (pd.Series([0.01]), "DatetimeIndex"),
        (
            pd.Series(
                ["bad"],
                index=pd.to_datetime(["2024-01-01"]),
            ),
            "numeric values",
        ),
        (
            pd.Series(
                [float("nan")],
                index=pd.to_datetime(["2024-01-01"]),
            ),
            "missing values",
        ),
    ],
)
def test_rejects_invalid_inputs(portfolio_return: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        portfolio_risk_summary(portfolio_return)  # type: ignore[arg-type]


def test_does_not_mutate_input() -> None:
    portfolio_return = make_portfolio_return()
    before = portfolio_return.copy(deep=True)

    portfolio_risk_summary(portfolio_return)

    pd.testing.assert_series_equal(portfolio_return, before)
