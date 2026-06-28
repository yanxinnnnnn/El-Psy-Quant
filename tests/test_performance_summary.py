import pandas as pd
import pytest

from el_psy_quant.performance import backtest_summary


def make_result() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "equity": [1_000.0, 1_100.0, 1_045.0],
            "strategy_return": [0.0, 0.10, -0.05],
        }
    )


def test_backtest_summary() -> None:
    result = backtest_summary(make_result())

    assert result == pytest.approx(
        {
            "initial_equity": 1_000.0,
            "final_equity": 1_045.0,
            "total_return": 0.045,
            "max_drawdown": -0.05,
            "periods": 3.0,
        }
    )


def test_summary_uses_existing_metric_functions(monkeypatch) -> None:
    monkeypatch.setattr(
        "el_psy_quant.performance.summary.total_return", lambda equity: 0.12
    )
    monkeypatch.setattr(
        "el_psy_quant.performance.summary.max_drawdown", lambda equity: -0.34
    )

    result = backtest_summary(make_result())

    assert result["total_return"] == 0.12
    assert result["max_drawdown"] == -0.34


def test_missing_equity_column_raises_value_error() -> None:
    result = pd.DataFrame({"strategy_return": [0.0]})

    with pytest.raises(ValueError, match="'equity' column"):
        backtest_summary(result)


def test_missing_strategy_return_column_raises_value_error() -> None:
    result = pd.DataFrame({"equity": [1.0]})

    with pytest.raises(ValueError, match="'strategy_return' column"):
        backtest_summary(result)


def test_empty_result_raises_value_error() -> None:
    result = pd.DataFrame(columns=["equity", "strategy_return"])

    with pytest.raises(ValueError, match="must not be empty"):
        backtest_summary(result)


def test_nan_equity_raises_value_error() -> None:
    result = make_result()
    result.loc[1, "equity"] = float("nan")

    with pytest.raises(ValueError, match="equity must not contain NaN"):
        backtest_summary(result)


def test_nan_strategy_return_raises_value_error() -> None:
    result = make_result()
    result.loc[1, "strategy_return"] = float("nan")

    with pytest.raises(ValueError, match="strategy_return must not contain NaN"):
        backtest_summary(result)


def test_summary_has_exactly_expected_keys() -> None:
    result = backtest_summary(make_result())

    assert set(result) == {
        "initial_equity",
        "final_equity",
        "total_return",
        "max_drawdown",
        "periods",
    }


def test_periods_equals_number_of_rows() -> None:
    result_frame = make_result()

    result = backtest_summary(result_frame)

    assert result["periods"] == len(result_frame)


def test_summary_adds_annualized_metrics_when_frequency_is_provided() -> None:
    result_frame = make_result()
    result_frame["net_strategy_return"] = [0.0, 0.08, -0.04]

    result = backtest_summary(result_frame, periods_per_year=2)

    assert result["cagr"] == pytest.approx(0.045)
    assert result["annualized_volatility"] == pytest.approx(
        result_frame["net_strategy_return"].std(ddof=1) * 2**0.5
    )
    assert "sharpe_ratio" in result


def test_summary_annualized_volatility_falls_back_to_gross_returns() -> None:
    result_frame = make_result()

    result = backtest_summary(result_frame, periods_per_year=2)

    assert result["annualized_volatility"] == pytest.approx(
        result_frame["strategy_return"].std(ddof=1) * 2**0.5
    )


def test_summary_rejects_invalid_period_frequency() -> None:
    with pytest.raises(ValueError, match="periods_per_year must be positive"):
        backtest_summary(make_result(), periods_per_year=0)


def test_summary_risk_free_rate_affects_sharpe() -> None:
    zero_rate = backtest_summary(make_result(), periods_per_year=2)
    positive_rate = backtest_summary(
        make_result(), periods_per_year=2, annual_risk_free_rate=0.02
    )

    assert positive_rate["sharpe_ratio"] < zero_rate["sharpe_ratio"]


def test_zero_volatility_only_raises_when_annualized_metrics_requested() -> None:
    result = pd.DataFrame(
        {"equity": [1.0, 1.0], "strategy_return": [0.0, 0.0]}
    )

    assert "sharpe_ratio" not in backtest_summary(result)
    with pytest.raises(ValueError, match="annualized volatility must not be zero"):
        backtest_summary(result, periods_per_year=252)

