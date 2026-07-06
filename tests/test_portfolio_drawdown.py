import json

import pandas as pd
import pytest

from el_psy_quant.portfolio import inspect_portfolio_drawdown


def make_equity(values: list[float]) -> pd.Series:
    return pd.Series(
        values,
        index=pd.date_range("2024-01-01", periods=len(values), freq="D"),
        name="equity",
    )


def test_inspects_recovered_drawdown() -> None:
    result = inspect_portfolio_drawdown(
        make_equity([100.0, 120.0, 90.0, 110.0, 120.0, 130.0])
    )

    assert result == {
        "max_drawdown": -0.25,
        "peak_date": "2024-01-02T00:00:00",
        "trough_date": "2024-01-03T00:00:00",
        "recovery_date": "2024-01-05T00:00:00",
        "recovered": True,
        "duration_periods": 3.0,
        "time_to_trough_periods": 1.0,
        "time_to_recovery_periods": 2.0,
    }


def test_inspects_unrecovered_drawdown() -> None:
    result = inspect_portfolio_drawdown(
        make_equity([100.0, 120.0, 90.0, 100.0, 110.0])
    )

    assert result["max_drawdown"] == -0.25
    assert result["peak_date"] == "2024-01-02T00:00:00"
    assert result["trough_date"] == "2024-01-03T00:00:00"
    assert result["recovery_date"] is None
    assert result["recovered"] is False
    assert result["duration_periods"] == 3.0
    assert result["time_to_trough_periods"] == 1.0
    assert result["time_to_recovery_periods"] is None


@pytest.mark.parametrize(
    "equity",
    [
        make_equity([100.0, 110.0, 120.0]),
        make_equity([100.0, 100.0, 100.0]),
        make_equity([100.0]),
    ],
)
def test_no_drawdown_uses_first_observation(equity: pd.Series) -> None:
    result = inspect_portfolio_drawdown(equity)
    first_date = equity.index[0].isoformat()

    assert result == {
        "max_drawdown": 0.0,
        "peak_date": first_date,
        "trough_date": first_date,
        "recovery_date": first_date,
        "recovered": True,
        "duration_periods": 0.0,
        "time_to_trough_periods": 0.0,
        "time_to_recovery_periods": 0.0,
    }


def test_worst_drawdown_uses_latest_running_peak() -> None:
    result = inspect_portfolio_drawdown(
        make_equity([100.0, 80.0, 110.0, 105.0, 70.0, 90.0])
    )

    assert result["max_drawdown"] == pytest.approx(70.0 / 110.0 - 1.0)
    assert result["peak_date"] == "2024-01-03T00:00:00"
    assert result["trough_date"] == "2024-01-05T00:00:00"


def test_recovery_is_first_observation_at_or_above_peak() -> None:
    result = inspect_portfolio_drawdown(
        make_equity([100.0, 120.0, 90.0, 119.0, 120.0, 125.0])
    )

    assert result["recovery_date"] == "2024-01-05T00:00:00"
    assert result["duration_periods"] == 3.0
    assert result["time_to_recovery_periods"] == 2.0


def test_result_is_json_compatible_and_dates_are_strings() -> None:
    result = inspect_portfolio_drawdown(
        make_equity([100.0, 80.0, 100.0])
    )

    assert isinstance(result["peak_date"], str)
    assert isinstance(result["trough_date"], str)
    assert isinstance(result["recovery_date"], str)
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("equity", "message"),
    [
        ([100.0], "pandas Series"),
        (pd.Series(dtype=float), "must not be empty"),
        (pd.Series([100.0]), "DatetimeIndex"),
        (
            pd.Series(["bad"], index=pd.to_datetime(["2024-01-01"])),
            "numeric values",
        ),
        (
            pd.Series([float("nan")], index=pd.to_datetime(["2024-01-01"])),
            "missing values",
        ),
        (
            pd.Series([100.0, 0.0], index=pd.date_range("2024-01-01", periods=2)),
            "must be positive",
        ),
        (
            pd.Series([-1.0], index=pd.to_datetime(["2024-01-01"])),
            "must be positive",
        ),
    ],
)
def test_rejects_invalid_inputs(equity: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        inspect_portfolio_drawdown(equity)  # type: ignore[arg-type]


def test_does_not_mutate_equity() -> None:
    equity = make_equity([100.0, 80.0, 90.0])
    before = equity.copy(deep=True)

    inspect_portfolio_drawdown(equity)

    pd.testing.assert_series_equal(equity, before)
