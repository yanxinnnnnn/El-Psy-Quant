import pandas as pd
import pytest

from el_psy_quant.portfolio import weighted_portfolio_return


def make_returns(columns: dict[str, list[object]]) -> pd.DataFrame:
    return pd.DataFrame(
        columns,
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )


def test_computes_two_symbol_weighted_returns() -> None:
    aligned = make_returns({"AAPL": [0.01, 0.02], "MSFT": [0.03, -0.01]})

    result = weighted_portfolio_return(aligned, {"AAPL": 0.25, "MSFT": 0.75})

    expected = pd.Series(
        [0.025, -0.0025],
        index=aligned.index,
        name="portfolio_return",
    )
    pd.testing.assert_series_equal(result, expected)


def test_computes_three_symbol_weighted_returns() -> None:
    aligned = make_returns(
        {"AAPL": [0.03, 0.06], "MSFT": [0.0, -0.03], "SPY": [-0.03, 0.0]}
    )

    result = weighted_portfolio_return(
        aligned,
        {"AAPL": 0.5, "MSFT": 0.25, "SPY": 0.25},
    )

    expected = pd.Series(
        [0.0075, 0.0225],
        index=aligned.index,
        name="portfolio_return",
    )
    pd.testing.assert_series_equal(result, expected)


def test_one_symbol_weight_returns_same_values() -> None:
    aligned = make_returns({"AAPL": [0.01, -0.02]})

    result = weighted_portfolio_return(aligned, {"AAPL": 1.0})

    pd.testing.assert_series_equal(
        result,
        aligned["AAPL"].rename("portfolio_return"),
    )


def test_preserves_index_and_does_not_mutate_inputs() -> None:
    aligned = make_returns({"MSFT": [0.03, -0.01], "AAPL": [0.01, 0.02]})
    weights = {"AAPL": 0.4, "MSFT": 0.6}
    aligned_before = aligned.copy(deep=True)
    weights_before = weights.copy()

    result = weighted_portfolio_return(aligned, weights)

    assert result.name == "portfolio_return"
    assert result.index.equals(aligned.index)
    pd.testing.assert_frame_equal(aligned, aligned_before)
    assert weights == weights_before


@pytest.mark.parametrize(
    ("aligned", "message"),
    [
        ([], "pandas DataFrame"),
        (pd.DataFrame(), "must not be empty"),
        (pd.DataFrame({"AAPL": [0.1]}), "DatetimeIndex"),
        (make_returns({"AAPL": ["bad", "values"]}), "columns must be numeric"),
        (make_returns({"AAPL": [0.1, float("nan")]}), "missing values"),
    ],
)
def test_reuses_aligned_return_validation(aligned: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        weighted_portfolio_return(aligned, {"AAPL": 1.0})  # type: ignore[arg-type]


def test_weight_validation_errors_propagate() -> None:
    aligned = make_returns({"AAPL": [0.01, 0.02], "MSFT": [0.03, -0.01]})

    with pytest.raises(ValueError, match="weights missing symbols: MSFT"):
        weighted_portfolio_return(aligned, {"AAPL": 1.0})
