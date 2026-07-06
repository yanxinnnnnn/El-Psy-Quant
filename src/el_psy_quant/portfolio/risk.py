"""Small risk summaries for portfolio return series."""

import pandas as pd

from el_psy_quant.performance import annualized_volatility


def portfolio_risk_summary(
    portfolio_return: pd.Series,
    periods_per_year: int | float | None = None,
) -> dict[str, float]:
    """Summarize portfolio return distribution and loss frequency."""
    if not isinstance(portfolio_return, pd.Series):
        raise ValueError("portfolio_return must be a pandas Series")
    if portfolio_return.empty:
        raise ValueError("portfolio_return must not be empty")
    if not isinstance(portfolio_return.index, pd.DatetimeIndex):
        raise ValueError("portfolio_return must have a DatetimeIndex")
    if not pd.api.types.is_numeric_dtype(portfolio_return):
        raise ValueError("portfolio_return must contain numeric values")
    if portfolio_return.isna().any():
        raise ValueError("portfolio_return must not contain missing values")

    periods = len(portfolio_return)
    positive_periods = int((portfolio_return > 0).sum())
    negative_periods = int((portfolio_return < 0).sum())
    zero_periods = int((portfolio_return == 0).sum())
    volatility = (
        0.0
        if periods == 1
        else float(portfolio_return.std(ddof=1))
    )
    summary = {
        "periods": float(periods),
        "mean_return": float(portfolio_return.mean()),
        "volatility": volatility,
        "min_return": float(portfolio_return.min()),
        "max_return": float(portfolio_return.max()),
        "positive_periods": float(positive_periods),
        "negative_periods": float(negative_periods),
        "zero_periods": float(zero_periods),
        "loss_rate": float(negative_periods / periods),
    }
    if periods_per_year is not None:
        summary["annualized_volatility"] = (
            0.0
            if periods == 1
            else annualized_volatility(portfolio_return, periods_per_year)
        )
    return summary
