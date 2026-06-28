"""Small, explicit research pipelines."""

from el_psy_quant.backtesting.experiments import (
    moving_average_crossover_parameter_sweep,
    summarize_parameter_sweep_results,
)
from el_psy_quant.backtesting.pipelines import moving_average_crossover_pipeline
from el_psy_quant.backtesting.workflows import moving_average_crossover_from_csv

__all__ = [
    "moving_average_crossover_from_csv",
    "moving_average_crossover_parameter_sweep",
    "moving_average_crossover_pipeline",
    "summarize_parameter_sweep_results",
]

