"""Run a deterministic, network-free research example."""

from pprint import pprint

import pandas as pd

from el_psy_quant.backtesting import moving_average_crossover_pipeline
from el_psy_quant.performance import backtest_summary


def main() -> None:
    """Run the minimal research pipeline and print its key outputs."""
    close = pd.Series(
        [1.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0, 2.0, 3.0, 4.0, 3.0, 2.0],
        name="close",
    )
    result = moving_average_crossover_pipeline(
        close,
        fast_window=2,
        slow_window=3,
        initial_capital=1_000.0,
    )
    summary = backtest_summary(result)

    print("result tail:")
    print(result.tail())
    print("\nsummary:")
    pprint(summary, sort_dicts=False)


if __name__ == "__main__":
    main()

