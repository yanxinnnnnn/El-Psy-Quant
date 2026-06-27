"""Crossover event signals."""

import pandas as pd


def crossover_signal(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """Return bullish and bearish events when ``fast`` crosses ``slow``."""
    if not fast.index.equals(slow.index):
        raise ValueError("fast and slow indexes must be equal")

    previous_fast = fast.shift(1)
    previous_slow = slow.shift(1)
    valid = (
        fast.notna()
        & slow.notna()
        & previous_fast.notna()
        & previous_slow.notna()
    )

    bullish = valid & (fast > slow) & (previous_fast <= previous_slow)
    bearish = valid & (fast < slow) & (previous_fast >= previous_slow)

    signal = pd.Series(0, index=fast.index, dtype="int64")
    signal.loc[bullish] = 1
    signal.loc[bearish] = -1
    return signal

