"""Minimal strategy interface and result-shape validation."""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

import pandas as pd

REQUIRED_STRATEGY_RESULT_COLUMNS = frozenset({"equity", "strategy_return"})


@runtime_checkable
class Strategy(Protocol):
    """Structural contract for a research strategy."""

    name: str

    def run(
        self,
        prices: pd.DataFrame,
        parameters: Mapping[str, object],
    ) -> pd.DataFrame:
        """Return a pipeline result compatible with existing summaries."""
        ...


def validate_strategy_result(result: pd.DataFrame) -> None:
    """Validate the basic shape required from a strategy result."""
    if not isinstance(result, pd.DataFrame):
        raise ValueError("strategy result must be a pandas DataFrame")
    if result.empty:
        raise ValueError("strategy result must not be empty")

    missing_columns = REQUIRED_STRATEGY_RESULT_COLUMNS.difference(result.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"strategy result is missing required columns: {missing}")
