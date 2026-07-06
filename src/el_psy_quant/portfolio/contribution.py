"""Static-weight per-symbol portfolio return contributions."""

from collections.abc import Mapping

import pandas as pd

from el_psy_quant.portfolio.returns import _validate_aligned_returns
from el_psy_quant.portfolio.weights import validate_static_weights


def symbol_contribution_returns(
    aligned_returns: pd.DataFrame,
    weights: Mapping[str, float],
) -> pd.DataFrame:
    """Apply validated static weights to aligned per-symbol returns."""
    _validate_aligned_returns(aligned_returns)
    validated_weights = validate_static_weights(aligned_returns.columns, weights)
    return aligned_returns.mul(validated_weights.to_numpy(), axis="columns")


def summarize_symbol_contributions(
    contribution_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize per-symbol contribution returns in input column order."""
    _validate_aligned_returns(contribution_returns)
    rows = [
        {
            "symbol": str(symbol),
            "total_contribution": float(contribution_returns[symbol].sum()),
            "mean_contribution": float(contribution_returns[symbol].mean()),
            "positive_periods": int((contribution_returns[symbol] > 0).sum()),
            "negative_periods": int((contribution_returns[symbol] < 0).sum()),
            "zero_periods": int((contribution_returns[symbol] == 0).sum()),
        }
        for symbol in contribution_returns.columns
    ]
    return pd.DataFrame(rows)
