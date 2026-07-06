"""Daily strategy return calculation."""

import pandas as pd


def equal_weight_portfolio_return(aligned_returns: pd.DataFrame) -> pd.Series:
    """Compute the row-wise mean of validated aligned symbol returns."""
    if not isinstance(aligned_returns, pd.DataFrame):
        raise ValueError("aligned_returns must be a pandas DataFrame")
    if len(aligned_returns.index) == 0:
        raise ValueError("aligned_returns must not be empty")
    if not isinstance(aligned_returns.index, pd.DatetimeIndex):
        raise ValueError("aligned_returns must have a DatetimeIndex")
    if len(aligned_returns.columns) == 0:
        raise ValueError("aligned_returns must contain at least one symbol column")

    non_numeric = [
        str(column)
        for column in aligned_returns.columns
        if not pd.api.types.is_numeric_dtype(aligned_returns[column])
    ]
    if non_numeric:
        raise ValueError(
            f"aligned_returns columns must be numeric: {', '.join(non_numeric)}"
        )
    if aligned_returns.isna().any().any():
        raise ValueError("aligned_returns must not contain missing values")

    return aligned_returns.mean(axis=1).rename("portfolio_return")


def strategy_return(position: pd.Series, asset_return: pd.Series) -> pd.Series:
    """Apply the previous day's long-only position to each asset return."""
    if not position.index.equals(asset_return.index):
        raise ValueError("position and asset_return indexes must be equal")
    if position.isna().any():
        raise ValueError("position must not contain NaN values")
    if not position.isin([0, 1]).all():
        raise ValueError("position values must be 0 or 1")
    if asset_return.iloc[1:].isna().any():
        raise ValueError("asset_return must not contain NaN values after the first row")

    previous_position = position.shift(1, fill_value=0).astype(float)
    result = previous_position * asset_return.astype(float)

    if not result.empty:
        result.iloc[0] = 0.0

    return result

