import pandas as pd
import pytest

from el_psy_quant.portfolio import equal_weight_portfolio_return


def make_aligned_returns(columns: dict[str, list[object]]) -> pd.DataFrame:
    return pd.DataFrame(
        columns,
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )


def test_computes_two_symbol_equal_weight_returns() -> None:
    aligned = make_aligned_returns(
        {"AAPL": [0.01, 0.02], "MSFT": [0.03, -0.01]}
    )

    result = equal_weight_portfolio_return(aligned)

    expected = pd.Series(
        [0.02, 0.005],
        index=aligned.index,
        name="portfolio_return",
    )
    pd.testing.assert_series_equal(result, expected)


def test_computes_three_symbol_equal_weight_returns() -> None:
    aligned = make_aligned_returns(
        {
            "AAPL": [0.03, 0.06],
            "MSFT": [0.0, -0.03],
            "SPY": [-0.03, 0.0],
        }
    )

    result = equal_weight_portfolio_return(aligned)

    expected = pd.Series(
        [0.0, 0.01],
        index=aligned.index,
        name="portfolio_return",
    )
    pd.testing.assert_series_equal(result, expected)


def test_one_symbol_returns_same_values_with_portfolio_name() -> None:
    aligned = make_aligned_returns({"AAPL": [0.01, -0.02]})

    result = equal_weight_portfolio_return(aligned)

    expected = aligned["AAPL"].rename("portfolio_return")
    pd.testing.assert_series_equal(result, expected)


def test_preserves_index_and_does_not_mutate_input() -> None:
    aligned = make_aligned_returns(
        {"MSFT": [0.03, -0.01], "AAPL": [0.01, 0.02]}
    )
    before = aligned.copy(deep=True)

    result = equal_weight_portfolio_return(aligned)

    assert result.index.equals(aligned.index)
    pd.testing.assert_frame_equal(aligned, before)


def test_rejects_non_dataframe_input() -> None:
    with pytest.raises(ValueError, match="pandas DataFrame"):
        equal_weight_portfolio_return([])  # type: ignore[arg-type]


def test_rejects_empty_dataframe() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        equal_weight_portfolio_return(pd.DataFrame())


def test_rejects_non_datetime_index() -> None:
    aligned = pd.DataFrame({"AAPL": [0.01]})

    with pytest.raises(ValueError, match="DatetimeIndex"):
        equal_weight_portfolio_return(aligned)


def test_rejects_dataframe_without_symbol_columns() -> None:
    aligned = pd.DataFrame(index=pd.to_datetime(["2024-01-01"]))

    with pytest.raises(ValueError, match="at least one symbol column"):
        equal_weight_portfolio_return(aligned)


def test_rejects_non_numeric_column() -> None:
    aligned = make_aligned_returns(
        {"AAPL": [0.01, 0.02], "MSFT": ["bad", "values"]}
    )

    with pytest.raises(ValueError, match="numeric: MSFT"):
        equal_weight_portfolio_return(aligned)


def test_rejects_missing_values() -> None:
    aligned = make_aligned_returns(
        {"AAPL": [0.01, float("nan")], "MSFT": [0.03, -0.01]}
    )

    with pytest.raises(ValueError, match="must not contain missing values"):
        equal_weight_portfolio_return(aligned)
