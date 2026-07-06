import json

import pandas as pd
import pytest

from el_psy_quant.portfolio import (
    build_attribution_summary_artifact,
    inspect_portfolio_drawdown,
    portfolio_risk_summary,
    summarize_symbol_contributions,
)


def make_inputs() -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    portfolio_return = pd.Series(
        [0.02, -0.10, 0.05, 0.04],
        index=index,
        name="portfolio_return",
    )
    equity = pd.Series(
        [100.0, 90.0, 94.5, 98.28],
        index=index,
        name="equity",
    )
    contribution_returns = pd.DataFrame(
        {
            "AAPL": [0.012, -0.04, 0.02, 0.016],
            "MSFT": [0.008, -0.06, 0.03, 0.024],
        },
        index=index,
    )
    return portfolio_return, equity, contribution_returns


def build_artifact(
    *,
    weights: dict[str, float] | None = None,
    periods_per_year: int | float | None = None,
) -> dict[str, object]:
    portfolio_return, equity, contribution_returns = make_inputs()
    return build_attribution_summary_artifact(
        portfolio_return,
        equity,
        contribution_returns,
        construction_method="static_weight",
        symbols=["AAPL", "MSFT"],
        weights=weights,
        periods_per_year=periods_per_year,
    )


def test_artifact_contains_expected_top_level_sections() -> None:
    artifact = build_artifact()

    assert set(artifact) == {
        "schema_version",
        "construction",
        "risk",
        "drawdown",
        "contribution",
        "evaluation",
    }
    assert artifact["schema_version"] == 1


def test_records_method_and_normalized_ordered_symbols() -> None:
    portfolio_return, equity, contribution_returns = make_inputs()

    artifact = build_attribution_summary_artifact(
        portfolio_return,
        equity,
        contribution_returns,
        construction_method="static_weight",
        symbols=[" msft ", "aapl"],
    )

    assert artifact["construction"] == {
        "method": "static_weight",
        "symbols": ["MSFT", "AAPL"],
        "weights": None,
    }


def test_normalizes_and_records_weights_in_symbol_order() -> None:
    artifact = build_artifact(weights={" msft ": 0.4, "aapl": 0.6})

    assert artifact["construction"] == {
        "method": "static_weight",
        "symbols": ["AAPL", "MSFT"],
        "weights": {"AAPL": 0.6, "MSFT": 0.4},
    }


def test_weights_are_none_when_not_provided() -> None:
    artifact = build_artifact()

    assert artifact["construction"]["weights"] is None  # type: ignore[index]


def test_sections_match_existing_summary_helpers() -> None:
    portfolio_return, equity, contribution_returns = make_inputs()

    artifact = build_attribution_summary_artifact(
        portfolio_return,
        equity,
        contribution_returns,
        construction_method="static_weight",
        symbols=["AAPL", "MSFT"],
        weights={"AAPL": 0.6, "MSFT": 0.4},
        periods_per_year=252,
    )

    assert artifact["risk"] == portfolio_risk_summary(portfolio_return, 252)
    assert artifact["drawdown"] == inspect_portfolio_drawdown(equity)
    assert artifact["contribution"] == summarize_symbol_contributions(
        contribution_returns
    ).to_dict("records")
    assert artifact["evaluation"] == {"periods_per_year": 252.0}


def test_artifact_is_strictly_json_serializable() -> None:
    artifact = build_artifact(
        weights={"AAPL": 0.6, "MSFT": 0.4},
        periods_per_year=252,
    )

    json.dumps(artifact, allow_nan=False)


@pytest.mark.parametrize("method", ["", "   ", None, 123])
def test_rejects_invalid_construction_method(method: object) -> None:
    portfolio_return, equity, contribution_returns = make_inputs()

    with pytest.raises(ValueError, match="non-empty string"):
        build_attribution_summary_artifact(
            portfolio_return,
            equity,
            contribution_returns,
            construction_method=method,  # type: ignore[arg-type]
            symbols=["AAPL", "MSFT"],
        )


def test_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError, match="weights missing symbols: MSFT"):
        build_artifact(weights={"AAPL": 1.0})


def test_does_not_mutate_inputs() -> None:
    portfolio_return, equity, contribution_returns = make_inputs()
    symbols = [" aapl ", "msft"]
    weights = {" aapl ": 0.6, "msft": 0.4}
    return_before = portfolio_return.copy(deep=True)
    equity_before = equity.copy(deep=True)
    contribution_before = contribution_returns.copy(deep=True)
    symbols_before = symbols.copy()
    weights_before = weights.copy()

    build_attribution_summary_artifact(
        portfolio_return,
        equity,
        contribution_returns,
        construction_method="static_weight",
        symbols=symbols,
        weights=weights,
    )

    pd.testing.assert_series_equal(portfolio_return, return_before)
    pd.testing.assert_series_equal(equity, equity_before)
    pd.testing.assert_frame_equal(contribution_returns, contribution_before)
    assert symbols == symbols_before
    assert weights == weights_before
