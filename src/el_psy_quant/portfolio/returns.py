"""Daily strategy return calculation."""

import pandas as pd


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

