"""Small, explicit research pipelines."""

from el_psy_quant.backtesting.benchmarks import compare_to_buy_and_hold_benchmark
from el_psy_quant.backtesting.experiments import (
    moving_average_crossover_parameter_sweep,
    summarize_parameter_sweep_results,
)
from el_psy_quant.backtesting.multi import moving_average_crossover_multi_symbol
from el_psy_quant.backtesting.pipelines import moving_average_crossover_pipeline
from el_psy_quant.backtesting.trades import moving_average_crossover_trade_records
from el_psy_quant.backtesting.workflows import moving_average_crossover_from_csv

__all__ = [
    "compare_to_buy_and_hold_benchmark",
    "moving_average_crossover_from_csv",
    "moving_average_crossover_multi_symbol",
    "moving_average_crossover_parameter_sweep",
    "moving_average_crossover_pipeline",
    "moving_average_crossover_trade_records",
    "summarize_parameter_sweep_results",
]

