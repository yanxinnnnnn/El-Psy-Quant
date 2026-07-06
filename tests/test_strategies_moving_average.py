import pandas as pd
import pytest

from el_psy_quant.backtesting import moving_average_crossover_pipeline
from el_psy_quant.strategies import (
    MovingAverageCrossoverStrategy,
    Strategy,
    validate_strategy_result,
)


def make_prices() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=8, freq="D")
    return pd.DataFrame(
        {"Close": [10.0, 11.0, 12.0, 11.0, 10.0, 11.0, 12.0, 13.0]},
        index=index,
    )


def test_strategy_is_importable_and_satisfies_contract() -> None:
    strategy = MovingAverageCrossoverStrategy()

    assert isinstance(strategy, Strategy)
    assert strategy.name == "moving_average_crossover"


def test_run_matches_existing_pipeline_exactly() -> None:
    prices = make_prices()
    parameters = {
        "fast_window": 2,
        "slow_window": 3,
        "initial_capital": 1_000.0,
        "transaction_cost_rate": 0.01,
        "slippage_rate": 0.005,
    }

    actual = MovingAverageCrossoverStrategy().run(prices, parameters)
    expected = moving_average_crossover_pipeline(
        prices["Close"],
        fast_window=2,
        slow_window=3,
        initial_capital=1_000.0,
        transaction_cost_rate=0.01,
        slippage_rate=0.005,
    )

    pd.testing.assert_frame_equal(actual, expected)
    assert actual.columns.equals(expected.columns)
    assert actual.index.equals(expected.index)
    validate_strategy_result(actual)


def test_run_preserves_pipeline_defaults() -> None:
    prices = make_prices()

    actual = MovingAverageCrossoverStrategy().run(
        prices,
        {"fast_window": 2, "slow_window": 3},
    )
    expected = moving_average_crossover_pipeline(
        prices["Close"],
        fast_window=2,
        slow_window=3,
    )

    pd.testing.assert_frame_equal(actual, expected)


def test_run_rejects_prices_without_close_column() -> None:
    prices = make_prices().rename(columns={"Close": "Open"})

    with pytest.raises(ValueError, match="Close"):
        MovingAverageCrossoverStrategy().run(
            prices,
            {"fast_window": 2, "slow_window": 3},
        )
