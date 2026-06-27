"""Run deterministic research from the bundled sample CSV."""

from pathlib import Path
from pprint import pprint

from el_psy_quant.backtesting import moving_average_crossover_pipeline
from el_psy_quant.data import load_daily_prices_csv
from el_psy_quant.performance import backtest_summary

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_daily_prices.csv"


def main() -> None:
    """Load sample prices, run the research pipeline, and print its outputs."""
    prices = load_daily_prices_csv(SAMPLE_CSV)
    result = moving_average_crossover_pipeline(
        prices["Close"],
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

