"""Basic long-only trade record extraction."""

import pandas as pd

TRADE_COLUMNS = ["action", "position_before", "position_after", "close"]


def long_only_trade_records(
    position: pd.Series, close: pd.Series
) -> pd.DataFrame:
    """Return one trade record for each long-only position change."""
    if not position.index.equals(close.index):
        raise ValueError("position and close indexes must be equal")
    if position.isna().any():
        raise ValueError("position must not contain NaN values")
    if not position.isin([0, 1]).all():
        raise ValueError("position values must be 0 or 1")
    if close.isna().any():
        raise ValueError("close must not contain NaN values")

    current = position.astype(int)
    previous = current.shift(1, fill_value=0)
    change = current - previous
    trade_mask = change.ne(0)
    trades = pd.DataFrame(
        {
            "action": change.map({1: "BUY", -1: "SELL"}),
            "position_before": previous,
            "position_after": current,
            "close": close,
        },
        index=position.index,
    )
    return trades.loc[trade_mask, TRADE_COLUMNS]
