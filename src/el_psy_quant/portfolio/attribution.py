"""Standalone portfolio attribution summary artifacts."""

from collections.abc import Iterable, Mapping

import pandas as pd

from el_psy_quant.data.universe import build_symbol_universe
from el_psy_quant.portfolio.contribution import summarize_symbol_contributions
from el_psy_quant.portfolio.drawdown import inspect_portfolio_drawdown
from el_psy_quant.portfolio.risk import portfolio_risk_summary
from el_psy_quant.portfolio.weights import validate_static_weights


def build_attribution_summary_artifact(
    portfolio_return: pd.Series,
    equity: pd.Series,
    contribution_returns: pd.DataFrame,
    construction_method: str,
    symbols: Iterable[str],
    weights: Mapping[str, float] | None = None,
    periods_per_year: int | float | None = None,
) -> dict[str, object]:
    """Combine existing portfolio attribution summaries into one artifact."""
    if not isinstance(construction_method, str) or not construction_method.strip():
        raise ValueError("construction_method must be a non-empty string")

    normalized_symbols = build_symbol_universe(symbols)
    contribution_summary = summarize_symbol_contributions(contribution_returns)
    normalized_contribution_symbols = build_symbol_universe(
        contribution_returns.columns
    )
    if normalized_contribution_symbols != normalized_symbols:
        raise ValueError("contribution_returns columns must match symbols")

    serialized_weights: dict[str, float] | None = None
    if weights is not None:
        validated_weights = validate_static_weights(normalized_symbols, weights)
        serialized_weights = {
            symbol: float(value) for symbol, value in validated_weights.items()
        }

    return {
        "schema_version": 1,
        "construction": {
            "method": construction_method,
            "symbols": list(normalized_symbols),
            "weights": serialized_weights,
        },
        "risk": portfolio_risk_summary(portfolio_return, periods_per_year),
        "drawdown": inspect_portfolio_drawdown(equity),
        "contribution": contribution_summary.to_dict("records"),
        "evaluation": {
            "periods_per_year": (
                None if periods_per_year is None else float(periods_per_year)
            ),
        },
    }
