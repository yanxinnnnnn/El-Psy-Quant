import pandas as pd
import pytest

from el_psy_quant.backtesting import moving_average_crossover_pipeline
from el_psy_quant.indicators import daily_return, simple_moving_average
from el_psy_quant.portfolio import (
    equity_curve,
    long_only_position,
    slippage_cost,
    strategy_return,
    transaction_cost,
)
from el_psy_quant.signals import crossover_signal


def test_pipeline_returns_expected_columns_in_order() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]),
        fast_window=1,
        slow_window=2,
    )

    assert list(result.columns) == [
        "close",
        "fast_sma",
        "slow_sma",
        "signal",
        "position",
        "asset_return",
        "strategy_return",
        "transaction_cost",
        "slippage",
        "net_strategy_return",
        "equity",
    ]


def test_pipeline_preserves_close_index() -> None:
    index = pd.Index(["day-1", "day-2", "day-3"])
    close = pd.Series([1.0, 2.0, 3.0], index=index)

    result = moving_average_crossover_pipeline(close, 1, 2)

    assert result.index.equals(index)


def test_pipeline_composes_existing_functions() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 4.0])
    fast_sma = simple_moving_average(close, 2)
    slow_sma = simple_moving_average(close, 3)
    signal = crossover_signal(fast_sma, slow_sma)
    position = long_only_position(signal)
    asset_return = daily_return(close)
    returns = strategy_return(position, asset_return)
    costs = transaction_cost(position, 0.01)
    slippage = slippage_cost(position, 0.005)
    net_returns = returns - costs - slippage
    equity = equity_curve(net_returns, initial_capital=100.0)

    result = moving_average_crossover_pipeline(
        close, 2, 3, 100.0, 0.01, 0.005
    )

    expected = pd.DataFrame(
        {
            "close": close,
            "fast_sma": fast_sma,
            "slow_sma": slow_sma,
            "signal": signal,
            "position": position,
            "asset_return": asset_return,
            "strategy_return": returns,
            "transaction_cost": costs,
            "slippage": slippage,
            "net_strategy_return": net_returns,
            "equity": equity,
        }
    )
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize("fast_window, slow_window", [(2, 2), (3, 2)])
def test_fast_window_must_be_less_than_slow_window(
    fast_window: int, slow_window: int
) -> None:
    with pytest.raises(ValueError, match="must be less than"):
        moving_average_crossover_pipeline(
            pd.Series([1.0, 2.0, 3.0]),
            fast_window,
            slow_window,
        )


def test_nan_close_price_raises_value_error() -> None:
    with pytest.raises(ValueError, match="close must not contain NaN"):
        moving_average_crossover_pipeline(
            pd.Series([1.0, float("nan"), 3.0]),
            1,
            2,
        )


def test_custom_initial_capital_is_reflected_in_equity() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]),
        1,
        2,
        initial_capital=1_000.0,
    )

    assert result["equity"].iloc[0] == 1_000.0


def test_first_strategy_return_is_zero() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]),
        1,
        2,
    )

    assert result["strategy_return"].iloc[0] == 0.0


def test_default_transaction_cost_is_zero() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]), 1, 2
    )

    assert (result["transaction_cost"] == 0.0).all()


def test_negative_transaction_cost_rate_raises_value_error() -> None:
    with pytest.raises(ValueError, match="cost_rate must not be negative"):
        moving_average_crossover_pipeline(
            pd.Series([1.0, 2.0, 3.0]), 1, 2, transaction_cost_rate=-0.01
        )


def test_default_slippage_is_zero() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]), 1, 2
    )

    assert (result["slippage"] == 0.0).all()


def test_negative_slippage_rate_raises_value_error() -> None:
    with pytest.raises(ValueError, match="slippage_rate must not be negative"):
        moving_average_crossover_pipeline(
            pd.Series([1.0, 2.0, 3.0]), 1, 2, slippage_rate=-0.01
        )


def test_pipeline_does_not_call_yahoo_finance(monkeypatch) -> None:
    def fail_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("pipeline must not access a data provider")

    monkeypatch.setattr("el_psy_quant.data.providers.yf.download", fail_download)

    moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0]),
        1,
        2,
    )

