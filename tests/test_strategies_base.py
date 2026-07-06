from collections.abc import Mapping

import pandas as pd
import pytest

from el_psy_quant.strategies import Strategy, validate_strategy_result


class FakeStrategy:
    name = "fake"

    def run(
        self,
        prices: pd.DataFrame,
        parameters: Mapping[str, object],
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "equity": [1.0, 1.1],
                "strategy_return": [0.0, 0.1],
            },
            index=prices.index[:2],
        )


def test_strategy_contract_is_importable_and_structural() -> None:
    strategy = FakeStrategy()

    assert isinstance(strategy, Strategy)
    assert strategy.name == "fake"


@pytest.mark.parametrize(
    "result",
    [
        pd.DataFrame(
            {"equity": [1.0], "strategy_return": [0.0]},
        ),
        pd.DataFrame(
            {
                "equity": [1.0],
                "strategy_return": [0.0],
                "net_strategy_return": [0.0],
            }
        ),
    ],
)
def test_valid_strategy_results_pass_validation(result: pd.DataFrame) -> None:
    validate_strategy_result(result)


@pytest.mark.parametrize("missing_column", ["equity", "strategy_return"])
def test_missing_required_result_columns_raise_value_error(
    missing_column: str,
) -> None:
    columns = {
        "equity": [1.0],
        "strategy_return": [0.0],
    }
    del columns[missing_column]

    with pytest.raises(ValueError, match=missing_column):
        validate_strategy_result(pd.DataFrame(columns))


def test_empty_strategy_result_raises_value_error() -> None:
    result = pd.DataFrame(columns=["equity", "strategy_return"])

    with pytest.raises(ValueError, match="must not be empty"):
        validate_strategy_result(result)


def test_non_dataframe_strategy_result_raises_value_error() -> None:
    with pytest.raises(ValueError, match="pandas DataFrame"):
        validate_strategy_result([])  # type: ignore[arg-type]
