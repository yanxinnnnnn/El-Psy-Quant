import pandas as pd
import pytest

from el_psy_quant.portfolio import (
    summarize_symbol_contributions,
    symbol_contribution_returns,
    weighted_portfolio_return,
)


def make_returns(columns: dict[str, list[object]]) -> pd.DataFrame:
    return pd.DataFrame(
        columns,
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )


def test_computes_static_weight_symbol_contributions() -> None:
    aligned = make_returns(
        {"AAPL": [0.02, -0.01, 0.0], "MSFT": [0.01, 0.03, -0.02]}
    )

    result = symbol_contribution_returns(
        aligned,
        {"AAPL": 0.25, "MSFT": 0.75},
    )

    expected = pd.DataFrame(
        {
            "AAPL": [0.005, -0.0025, 0.0],
            "MSFT": [0.0075, 0.0225, -0.015],
        },
        index=aligned.index,
    )
    pd.testing.assert_frame_equal(result, expected)


def test_preserves_index_and_symbol_order() -> None:
    aligned = make_returns(
        {"MSFT": [0.01, 0.03, -0.02], "AAPL": [0.02, -0.01, 0.0]}
    )

    result = symbol_contribution_returns(
        aligned,
        {"AAPL": 0.4, "MSFT": 0.6},
    )

    assert result.index.equals(aligned.index)
    assert result.columns.tolist() == ["MSFT", "AAPL"]


def test_contribution_sums_equal_weighted_portfolio_return() -> None:
    aligned = make_returns(
        {"AAPL": [0.02, -0.01, 0.0], "MSFT": [0.01, 0.03, -0.02]}
    )
    weights = {"AAPL": 0.25, "MSFT": 0.75}

    contributions = symbol_contribution_returns(aligned, weights)

    pd.testing.assert_series_equal(
        contributions.sum(axis=1).rename("portfolio_return"),
        weighted_portfolio_return(aligned, weights),
    )


def test_normalizes_weight_keys() -> None:
    aligned = make_returns(
        {"AAPL": [0.02, -0.01, 0.0], "MSFT": [0.01, 0.03, -0.02]}
    )

    result = symbol_contribution_returns(
        aligned,
        {" aapl ": 0.25, "msft": 0.75},
    )

    expected = aligned.mul([0.25, 0.75], axis="columns")
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ({"AAPL": 1.0}, "weights missing symbols: MSFT"),
        (
            {"AAPL": 0.4, "MSFT": 0.4, "TSLA": 0.2},
            "weights contain unknown symbols: TSLA",
        ),
        ({"AAPL": "bad", "MSFT": 0.0}, "AAPL weight must be numeric"),
    ],
)
def test_rejects_invalid_weights(
    weights: dict[str, object],
    message: str,
) -> None:
    aligned = make_returns(
        {"AAPL": [0.02, -0.01, 0.0], "MSFT": [0.01, 0.03, -0.02]}
    )

    with pytest.raises(ValueError, match=message):
        symbol_contribution_returns(aligned, weights)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("aligned", "message"),
    [
        ([], "pandas DataFrame"),
        (pd.DataFrame(), "must not be empty"),
        (pd.DataFrame(index=pd.to_datetime(["2024-01-01"])), "symbol column"),
        (pd.DataFrame({"AAPL": [0.01]}), "DatetimeIndex"),
        (make_returns({"AAPL": [0.01, "bad", 0.02]}), "must be numeric"),
        (make_returns({"AAPL": [0.01, float("nan"), 0.02]}), "missing values"),
    ],
)
def test_rejects_invalid_aligned_returns(
    aligned: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        symbol_contribution_returns(  # type: ignore[arg-type]
            aligned,
            {"AAPL": 1.0},
        )


def test_does_not_mutate_inputs() -> None:
    aligned = make_returns(
        {"AAPL": [0.02, -0.01, 0.0], "MSFT": [0.01, 0.03, -0.02]}
    )
    weights = {"AAPL": 0.25, "MSFT": 0.75}
    aligned_before = aligned.copy(deep=True)
    weights_before = weights.copy()

    symbol_contribution_returns(aligned, weights)

    pd.testing.assert_frame_equal(aligned, aligned_before)
    assert weights == weights_before


def test_summarizes_each_symbol_in_input_order() -> None:
    contributions = make_returns(
        {"MSFT": [0.01, 0.0, -0.02], "AAPL": [-0.01, 0.02, 0.03]}
    )

    result = summarize_symbol_contributions(contributions)

    expected = pd.DataFrame(
        [
            {
                "symbol": "MSFT",
                "total_contribution": -0.01,
                "mean_contribution": -0.01 / 3,
                "positive_periods": 1,
                "negative_periods": 1,
                "zero_periods": 1,
            },
            {
                "symbol": "AAPL",
                "total_contribution": 0.04,
                "mean_contribution": 0.04 / 3,
                "positive_periods": 2,
                "negative_periods": 1,
                "zero_periods": 0,
            },
        ]
    )
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    ("contributions", "message"),
    [
        (pd.DataFrame(), "must not be empty"),
        (pd.DataFrame({"AAPL": [0.01]}), "DatetimeIndex"),
        (make_returns({"AAPL": [0.01, "bad", 0.02]}), "must be numeric"),
        (make_returns({"AAPL": [0.01, float("nan"), 0.02]}), "missing values"),
    ],
)
def test_summary_rejects_invalid_contribution_returns(
    contributions: pd.DataFrame,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        summarize_symbol_contributions(contributions)
