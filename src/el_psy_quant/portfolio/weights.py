"""Validation of user-supplied static portfolio weights."""

import math
from collections.abc import Iterable, Mapping
from numbers import Real

import pandas as pd

from el_psy_quant.data.universe import build_symbol_universe


def validate_static_weights(
    symbols: Iterable[str],
    weights: Mapping[str, float],
) -> pd.Series:
    """Validate static weights and return them in configured symbol order."""
    normalized_symbols = build_symbol_universe(symbols)
    normalized_weight_symbols = (
        build_symbol_universe(weights) if weights else ()
    )
    normalized_weights = dict(
        zip(normalized_weight_symbols, weights.values(), strict=True)
    )

    missing = [
        symbol for symbol in normalized_symbols if symbol not in normalized_weights
    ]
    if missing:
        raise ValueError(f"weights missing symbols: {', '.join(missing)}")
    expected = set(normalized_symbols)
    extra = [symbol for symbol in normalized_weight_symbols if symbol not in expected]
    if extra:
        raise ValueError(f"weights contain unknown symbols: {', '.join(extra)}")

    ordered_weights: list[float] = []
    for symbol in normalized_symbols:
        value = normalized_weights[symbol]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{symbol} weight must be numeric")
        numeric_value = float(value)
        if math.isnan(numeric_value):
            raise ValueError(f"{symbol} weight must not be missing")
        if numeric_value < 0:
            raise ValueError(f"{symbol} weight must be non-negative")
        ordered_weights.append(numeric_value)

    if not math.isclose(sum(ordered_weights), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("weights must sum to 1.0")
    return pd.Series(ordered_weights, index=normalized_symbols, dtype=float)
