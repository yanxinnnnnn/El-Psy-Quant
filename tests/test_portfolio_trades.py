import pandas as pd
import pytest

from el_psy_quant.portfolio import long_only_trade_records

TRADE_COLUMNS = ["action", "position_before", "position_after", "close"]


def test_returns_buy_and_sell_records_at_position_changes() -> None:
    index = pd.Index(["first", "second", "third", "fourth"])

    result = long_only_trade_records(
        pd.Series([0, 1, 1, 0], index=index),
        pd.Series([10.0, 11.0, 12.0, 13.0], index=index),
    )

    expected = pd.DataFrame(
        {
            "action": ["BUY", "SELL"],
            "position_before": [0, 1],
            "position_after": [1, 0],
            "close": [11.0, 13.0],
        },
        index=pd.Index(["second", "fourth"]),
    )
    pd.testing.assert_frame_equal(result, expected)


def test_first_long_position_is_a_buy() -> None:
    result = long_only_trade_records(
        pd.Series([1, 1]), pd.Series([10.0, 11.0])
    )

    assert result.iloc[0].to_dict() == {
        "action": "BUY",
        "position_before": 0,
        "position_after": 1,
        "close": 10.0,
    }


def test_unchanged_positions_return_empty_stable_frame() -> None:
    result = long_only_trade_records(
        pd.Series([0, 0]), pd.Series([10.0, 11.0])
    )

    assert result.empty
    assert list(result.columns) == TRADE_COLUMNS


def test_unequal_indexes_raise_value_error() -> None:
    with pytest.raises(ValueError, match="indexes must be equal"):
        long_only_trade_records(
            pd.Series([0, 1], index=[0, 1]),
            pd.Series([10.0, 11.0], index=[0, 2]),
        )


@pytest.mark.parametrize(
    ("position", "close", "message"),
    [
        ([0.0, float("nan")], [10.0, 11.0], "position must not contain NaN"),
        ([0, 2], [10.0, 11.0], "position values must be 0 or 1"),
        ([0, 1], [10.0, float("nan")], "close must not contain NaN"),
    ],
)
def test_invalid_values_raise_value_error(
    position: list[float], close: list[float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        long_only_trade_records(pd.Series(position), pd.Series(close))


def test_trade_helper_is_exported_from_portfolio() -> None:
    from el_psy_quant import portfolio

    assert portfolio.long_only_trade_records is long_only_trade_records
