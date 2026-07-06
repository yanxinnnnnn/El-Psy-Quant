import pandas as pd
import pytest

from el_psy_quant.portfolio import align_strategy_returns


def make_result(
    dates: list[str],
    returns: list[object],
    return_column: str = "strategy_return",
) -> pd.DataFrame:
    return pd.DataFrame(
        {return_column: returns, "equity": [1.0] * len(dates)},
        index=pd.to_datetime(dates),
    )


def test_aligns_shared_dates_with_normalized_ordered_columns() -> None:
    msft = make_result(
        ["2024-01-01", "2024-01-02", "2024-01-03"],
        [0.0, 0.1, 0.2],
    )
    aapl = make_result(
        ["2024-01-02", "2024-01-03", "2024-01-04"],
        [-0.1, 0.3, 0.4],
    )

    aligned = align_strategy_returns({" msft ": msft, "aapl": aapl})

    expected = pd.DataFrame(
        {"MSFT": [0.1, 0.2], "AAPL": [-0.1, 0.3]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    pd.testing.assert_frame_equal(aligned, expected)
    assert isinstance(aligned.index, pd.DatetimeIndex)


@pytest.mark.parametrize(
    ("results", "message"),
    [
        ({}, "results_by_symbol must not be empty"),
        ({"  ": make_result(["2024-01-01"], [0.0])}, "symbol must not be empty"),
        (
            {
                "AAPL": make_result(["2024-01-01"], [0.0]),
                " aapl ": make_result(["2024-01-01"], [0.0]),
            },
            "duplicate symbol: AAPL",
        ),
    ],
)
def test_rejects_invalid_symbol_mappings(
    results: dict[str, pd.DataFrame],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        align_strategy_returns(results)


def test_rejects_non_dataframe_result() -> None:
    with pytest.raises(ValueError, match="AAPL result must be a pandas DataFrame"):
        align_strategy_returns({"AAPL": []})  # type: ignore[dict-item]


def test_rejects_non_datetime_index() -> None:
    result = make_result(["2024-01-01"], [0.0]).reset_index(drop=True)

    with pytest.raises(ValueError, match="AAPL result must have a DatetimeIndex"):
        align_strategy_returns({"AAPL": result})


def test_rejects_missing_requested_return_column_with_symbol_context() -> None:
    result = make_result(["2024-01-01"], [0.0])

    with pytest.raises(ValueError, match="AAPL result must contain 'net_return'"):
        align_strategy_returns({"AAPL": result}, return_column="net_return")


def test_rejects_non_numeric_returns_with_symbol_context() -> None:
    result = make_result(["2024-01-01"], ["bad"])

    with pytest.raises(
        ValueError,
        match="AAPL strategy_return must contain numeric values",
    ):
        align_strategy_returns({"AAPL": result})


def test_rejects_missing_returns_on_shared_dates_with_symbol_context() -> None:
    aapl = make_result(["2024-01-01", "2024-01-02"], [0.0, float("nan")])
    msft = make_result(["2024-01-02", "2024-01-03"], [0.1, 0.2])

    with pytest.raises(
        ValueError,
        match="AAPL strategy_return must not contain missing values",
    ):
        align_strategy_returns({"AAPL": aapl, "MSFT": msft})


def test_ignores_missing_returns_outside_shared_dates() -> None:
    aapl = make_result(["2024-01-01", "2024-01-02"], [float("nan"), 0.1])
    msft = make_result(["2024-01-02", "2024-01-03"], [0.2, 0.3])

    aligned = align_strategy_returns({"AAPL": aapl, "MSFT": msft})

    assert aligned.loc[pd.Timestamp("2024-01-02")].to_dict() == {
        "AAPL": 0.1,
        "MSFT": 0.2,
    }


def test_rejects_empty_shared_date_intersection() -> None:
    aapl = make_result(["2024-01-01"], [0.0])
    msft = make_result(["2024-01-02"], [0.1])

    with pytest.raises(ValueError, match="no shared dates"):
        align_strategy_returns({"AAPL": aapl, "MSFT": msft})


def test_does_not_mutate_input_frames() -> None:
    aapl = make_result(["2024-01-02", "2024-01-01"], [0.1, 0.0])
    msft = make_result(["2024-01-01", "2024-01-02"], [0.0, 0.2])
    aapl_before = aapl.copy(deep=True)
    msft_before = msft.copy(deep=True)

    align_strategy_returns({"AAPL": aapl, "MSFT": msft})

    pd.testing.assert_frame_equal(aapl, aapl_before)
    pd.testing.assert_frame_equal(msft, msft_before)
