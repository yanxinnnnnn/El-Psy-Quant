"""Position state generation."""

import pandas as pd


def long_only_position(signal: pd.Series) -> pd.Series:
    """Convert buy and sell events into a daily long-only position state."""
    if signal.isna().any():
        raise ValueError("signal must not contain NaN values")
    if not signal.isin([-1, 0, 1]).all():
        raise ValueError("signal values must be -1, 0, or 1")

    current_position = 0
    positions: list[int] = []

    for event in signal:
        if event == 1:
            current_position = 1
        elif event == -1:
            current_position = 0
        positions.append(current_position)

    return pd.Series(positions, index=signal.index, dtype="int64")

