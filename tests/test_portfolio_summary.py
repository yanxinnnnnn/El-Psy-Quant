import json
from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.portfolio import (
    build_portfolio_summary_artifact,
    summarize_portfolio_return,
    write_portfolio_summary_artifact,
)


def make_portfolio_return() -> pd.Series:
    return pd.Series(
        [0.0, 0.1, -0.05, 0.02],
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
        name="portfolio_return",
    )


def test_summary_contains_existing_required_metrics() -> None:
    summary = summarize_portfolio_return(make_portfolio_return())

    assert set(summary) == {
        "initial_equity",
        "final_equity",
        "total_return",
        "max_drawdown",
        "periods",
    }
    assert summary["initial_equity"] == 1.0
    assert summary["periods"] == 4.0
    assert all(type(value) is float for value in summary.values())


def test_annualized_metrics_are_optional() -> None:
    without_annualized = summarize_portfolio_return(make_portfolio_return())
    with_annualized = summarize_portfolio_return(
        make_portfolio_return(),
        periods_per_year=252,
        annual_risk_free_rate=0.02,
    )

    annualized = {"cagr", "annualized_volatility", "sharpe_ratio"}
    assert annualized.isdisjoint(without_annualized)
    assert annualized.issubset(with_annualized)


@pytest.mark.parametrize(
    ("portfolio_return", "initial_capital", "message"),
    [
        ([], 1.0, "pandas Series"),
        (pd.Series(dtype=float), 1.0, "must not be empty"),
        (pd.Series([0.0]), 1.0, "DatetimeIndex"),
        (
            pd.Series(
                ["bad"],
                index=pd.to_datetime(["2024-01-01"]),
            ),
            1.0,
            "numeric values",
        ),
        (
            pd.Series(
                [float("nan")],
                index=pd.to_datetime(["2024-01-01"]),
            ),
            1.0,
            "missing values",
        ),
        (make_portfolio_return(), 0.0, "initial_capital must be positive"),
        (make_portfolio_return(), -1.0, "initial_capital must be positive"),
    ],
)
def test_summary_rejects_invalid_inputs(
    portfolio_return: object,
    initial_capital: float,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        summarize_portfolio_return(  # type: ignore[arg-type]
            portfolio_return,
            initial_capital=initial_capital,
        )


def test_builds_json_serializable_equal_weight_artifact() -> None:
    artifact = build_portfolio_summary_artifact(
        make_portfolio_return(),
        construction_method="equal_weight",
        symbols=[" msft ", "aapl"],
        initial_capital=1_000.0,
        periods_per_year=252,
        annual_risk_free_rate=0.02,
    )

    assert artifact["schema_version"] == 1
    assert artifact["construction"] == {
        "method": "equal_weight",
        "symbols": ["MSFT", "AAPL"],
        "weights": None,
    }
    assert artifact["evaluation"] == {
        "initial_capital": 1_000.0,
        "periods_per_year": 252.0,
        "annual_risk_free_rate": 0.02,
    }
    assert "total_return" in artifact["metrics"]  # type: ignore[operator]
    json.dumps(artifact)


def test_static_weights_are_normalized_validated_and_ordered() -> None:
    artifact = build_portfolio_summary_artifact(
        make_portfolio_return(),
        construction_method="static_weight",
        symbols=["MSFT", "AAPL"],
        weights={" aapl ": 0.4, "msft": 0.6},
    )

    construction = artifact["construction"]
    assert isinstance(construction, dict)
    assert construction["weights"] == {"MSFT": 0.6, "AAPL": 0.4}
    assert list(construction["weights"]) == ["MSFT", "AAPL"]


def test_invalid_static_weight_coverage_raises_value_error() -> None:
    with pytest.raises(ValueError, match="weights missing symbols: MSFT"):
        build_portfolio_summary_artifact(
            make_portfolio_return(),
            construction_method="static_weight",
            symbols=["AAPL", "MSFT"],
            weights={"AAPL": 1.0},
        )


def test_writer_creates_directories_and_round_trips_json(tmp_path: Path) -> None:
    artifact = build_portfolio_summary_artifact(
        make_portfolio_return(),
        construction_method="equal_weight",
        symbols=["AAPL"],
    )
    path = tmp_path / "nested" / "portfolio-summary.json"

    written_path = write_portfolio_summary_artifact(artifact, path)

    assert written_path == path
    assert path.read_bytes().endswith(b"\n")
    assert json.loads(path.read_text(encoding="utf-8")) == artifact
