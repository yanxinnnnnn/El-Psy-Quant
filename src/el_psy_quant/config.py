"""Typed local experiment configuration loaded from YAML."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml


@dataclass(frozen=True)
class ExperimentDataConfig:
    """Local input settings for an experiment."""

    source: Literal["csv", "cache"]
    paths: dict[str, str] | None = None
    cache_dir: str | None = None
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True)
class MovingAverageCrossoverParameters:
    """Parameters accepted by the moving-average crossover pipeline."""

    fast_window: int
    slow_window: int
    initial_capital: float = 1.0
    transaction_cost_rate: float = 0.0
    slippage_rate: float = 0.0


@dataclass(frozen=True)
class ExperimentEvaluationConfig:
    """Optional annualized evaluation assumptions."""

    periods_per_year: int | float | None = None
    annual_risk_free_rate: float = 0.0


@dataclass(frozen=True)
class ExperimentConfig:
    """Validated configuration for one local research experiment."""

    name: str
    strategy: Literal["moving_average_crossover"]
    data: ExperimentDataConfig
    parameters: MovingAverageCrossoverParameters
    evaluation: ExperimentEvaluationConfig


def _require_mapping(value: object, section: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{section} must be a mapping")
    return value


def _non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_integer(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    return float(value)


def _normalize_symbols(symbols: list[object]) -> tuple[str, ...]:
    normalized_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = _non_empty_string(symbol, "symbol").upper()
        if normalized in seen:
            raise ValueError(f"duplicate symbol: {normalized}")
        seen.add(normalized)
        normalized_symbols.append(normalized)
    return tuple(normalized_symbols)


def _parse_data(raw: object) -> ExperimentDataConfig:
    data = _require_mapping(raw, "data")
    source = data.get("source")
    if source not in ("csv", "cache"):
        raise ValueError("data.source must be 'csv' or 'cache'")

    if source == "csv":
        raw_paths = _require_mapping(data.get("paths"), "data.paths")
        if not raw_paths:
            raise ValueError("data.paths must not be empty")
        symbols = _normalize_symbols(list(raw_paths))
        paths = {
            symbol: _non_empty_string(path, f"data.paths.{symbol}")
            for symbol, path in zip(symbols, raw_paths.values(), strict=True)
        }
        return ExperimentDataConfig(source="csv", paths=paths)

    cache_dir = _non_empty_string(data.get("cache_dir"), "data.cache_dir")
    raw_symbols = data.get("symbols")
    if not isinstance(raw_symbols, list) or not raw_symbols:
        raise ValueError("data.symbols must be a non-empty list")
    return ExperimentDataConfig(
        source="cache",
        cache_dir=cache_dir,
        symbols=_normalize_symbols(raw_symbols),
    )


def _parse_parameters(raw: object) -> MovingAverageCrossoverParameters:
    parameters = _require_mapping(raw, "parameters")
    fast_window = _positive_integer(parameters.get("fast_window"), "fast_window")
    slow_window = _positive_integer(parameters.get("slow_window"), "slow_window")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be less than slow_window")

    initial_capital = _number(parameters.get("initial_capital", 1.0), "initial_capital")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    transaction_cost_rate = _number(
        parameters.get("transaction_cost_rate", 0.0), "transaction_cost_rate"
    )
    if transaction_cost_rate < 0:
        raise ValueError("transaction_cost_rate must be non-negative")
    slippage_rate = _number(parameters.get("slippage_rate", 0.0), "slippage_rate")
    if slippage_rate < 0:
        raise ValueError("slippage_rate must be non-negative")

    return MovingAverageCrossoverParameters(
        fast_window=fast_window,
        slow_window=slow_window,
        initial_capital=initial_capital,
        transaction_cost_rate=transaction_cost_rate,
        slippage_rate=slippage_rate,
    )


def _parse_evaluation(raw: object) -> ExperimentEvaluationConfig:
    evaluation = _require_mapping(raw, "evaluation")
    periods_per_year = evaluation.get("periods_per_year")
    if periods_per_year is not None:
        periods_per_year = _number(periods_per_year, "periods_per_year")
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
    annual_risk_free_rate = _number(
        evaluation.get("annual_risk_free_rate", 0.0), "annual_risk_free_rate"
    )
    return ExperimentEvaluationConfig(
        periods_per_year=periods_per_year,
        annual_risk_free_rate=annual_risk_free_rate,
    )


def parse_experiment_config(raw: Mapping[str, Any]) -> ExperimentConfig:
    """Validate a parsed experiment configuration mapping."""
    experiment = _require_mapping(raw.get("experiment"), "experiment")
    name = _non_empty_string(experiment.get("name"), "experiment.name")
    strategy = experiment.get("strategy")
    if strategy != "moving_average_crossover":
        raise ValueError(
            "experiment.strategy must be 'moving_average_crossover'"
        )

    if "data" not in raw:
        raise ValueError("data section is required")
    if "parameters" not in raw:
        raise ValueError("parameters section is required")

    return ExperimentConfig(
        name=name,
        strategy="moving_average_crossover",
        data=_parse_data(raw["data"]),
        parameters=_parse_parameters(raw["parameters"]),
        evaluation=_parse_evaluation(raw.get("evaluation", {})),
    )


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load and validate one local YAML experiment configuration file."""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError("config file must contain valid YAML") from error
    if raw is None:
        raise ValueError("config file must not be empty")
    if not isinstance(raw, Mapping):
        raise ValueError("config file must contain a top-level mapping")
    return parse_experiment_config(raw)
