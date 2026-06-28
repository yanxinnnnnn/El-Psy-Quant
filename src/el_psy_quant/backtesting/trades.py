"""Trade record helpers for backtesting results."""

import pandas as pd

from el_psy_quant.portfolio import long_only_trade_records

OPTIONAL_TRADE_COLUMNS = [
    "transaction_cost",
    "slippage",
    "net_strategy_return",
    "equity",
]


def moving_average_crossover_trade_records(result: pd.DataFrame) -> pd.DataFrame:
    """Extract position-change records from a crossover pipeline result."""
    missing = [column for column in ("position", "close") if column not in result]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    trades = long_only_trade_records(result["position"], result["close"])
    for column in OPTIONAL_TRADE_COLUMNS:
        if column in result:
            trades[column] = result.loc[trades.index, column]
    return trades
