"""Focused inspection of the worst portfolio equity drawdown."""

import pandas as pd


def inspect_portfolio_drawdown(equity: pd.Series) -> dict[str, object]:
    """Describe the worst peak-to-trough drawdown in an equity series."""
    if not isinstance(equity, pd.Series):
        raise ValueError("equity must be a pandas Series")
    if equity.empty:
        raise ValueError("equity must not be empty")
    if not isinstance(equity.index, pd.DatetimeIndex):
        raise ValueError("equity must have a DatetimeIndex")
    if not pd.api.types.is_numeric_dtype(equity):
        raise ValueError("equity must contain numeric values")
    if equity.isna().any():
        raise ValueError("equity must not contain missing values")
    if (equity <= 0).any():
        raise ValueError("equity values must be positive")

    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    trough_position = int(drawdown.to_numpy().argmin())
    max_drawdown = float(drawdown.iloc[trough_position])

    if max_drawdown == 0.0:
        first_date = equity.index[0].isoformat()
        return {
            "max_drawdown": 0.0,
            "peak_date": first_date,
            "trough_date": first_date,
            "recovery_date": first_date,
            "recovered": True,
            "duration_periods": 0.0,
            "time_to_trough_periods": 0.0,
            "time_to_recovery_periods": 0.0,
        }

    peak_position = int(equity.iloc[: trough_position + 1].to_numpy().argmax())
    peak_equity = equity.iloc[peak_position]
    recovery_position = next(
        (
            position
            for position in range(trough_position + 1, len(equity))
            if equity.iloc[position] >= peak_equity
        ),
        None,
    )
    recovered = recovery_position is not None
    end_position = recovery_position if recovered else len(equity) - 1

    return {
        "max_drawdown": max_drawdown,
        "peak_date": equity.index[peak_position].isoformat(),
        "trough_date": equity.index[trough_position].isoformat(),
        "recovery_date": (
            equity.index[recovery_position].isoformat() if recovered else None
        ),
        "recovered": recovered,
        "duration_periods": float(end_position - peak_position),
        "time_to_trough_periods": float(trough_position - peak_position),
        "time_to_recovery_periods": (
            float(recovery_position - trough_position) if recovered else None
        ),
    }
