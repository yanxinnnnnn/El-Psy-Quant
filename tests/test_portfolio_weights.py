import math

import pandas as pd
import pytest

from el_psy_quant.portfolio import validate_static_weights


def test_valid_weights_follow_configured_symbol_order() -> None:
    result = validate_static_weights(
        ["MSFT", "AAPL"],
        {"AAPL": 0.4, "MSFT": 0.6},
    )

    expected = pd.Series([0.6, 0.4], index=["MSFT", "AAPL"], dtype=float)
    pd.testing.assert_series_equal(result, expected)


def test_normalizes_weight_keys() -> None:
    result = validate_static_weights(
        ["MSFT", "AAPL"],
        {" msft ": 0.6, "aapl": 0.4},
    )

    assert result.to_dict() == {"MSFT": 0.6, "AAPL": 0.4}


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ({"AAPL": 0.5, " aapl ": 0.5}, "duplicate symbol: AAPL"),
        ({"  ": 1.0}, "symbol must not be empty"),
        ({"AAPL": 1.0}, "weights missing symbols: MSFT"),
        (
            {"AAPL": 0.4, "MSFT": 0.4, "TSLA": 0.2},
            "weights contain unknown symbols: TSLA",
        ),
        ({"AAPL": "bad", "MSFT": 0.0}, "AAPL weight must be numeric"),
        ({"AAPL": True, "MSFT": 0.0}, "AAPL weight must be numeric"),
        ({"AAPL": math.nan, "MSFT": 0.0}, "AAPL weight must not be missing"),
        ({"AAPL": -0.1, "MSFT": 1.1}, "AAPL weight must be non-negative"),
        ({"AAPL": 0.4, "MSFT": 0.5}, "weights must sum to 1.0"),
    ],
)
def test_rejects_invalid_weights(
    weights: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_static_weights(["AAPL", "MSFT"], weights)  # type: ignore[arg-type]


def test_does_not_mutate_weight_mapping() -> None:
    weights = {" aapl ": 0.4, "msft": 0.6}
    before = weights.copy()

    validate_static_weights(["AAPL", "MSFT"], weights)

    assert weights == before
