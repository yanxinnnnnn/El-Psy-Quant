"""Typed local experiment configuration loaded from YAML."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml

from el_psy_quant.data.universe import build_symbol_universe
from el_psy_quant.paper.account import PaperAccountState, create_paper_account_state
from el_psy_quant.paper.fills import PaperFill, create_paper_fill
from el_psy_quant.paper.orders import (
    PaperOrderRecord,
    create_paper_order_ledger,
    create_paper_order_record,
)
from el_psy_quant.paper.run_request import PaperRunRequest, create_paper_run_request


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
class PaperRunConfig:
    """Explicit local paper-run input settings."""

    run_id: str
    created_timestamp: object
    starting_account_state: PaperAccountState
    ending_account_state: PaperAccountState
    orders: tuple[PaperOrderRecord, ...]
    fills: tuple[PaperFill, ...]


@dataclass(frozen=True)
class ExperimentConfig:
    """Validated configuration for one local research experiment."""

    name: str
    strategy: Literal["moving_average_crossover"]
    data: ExperimentDataConfig
    parameters: MovingAverageCrossoverParameters
    evaluation: ExperimentEvaluationConfig
    paper_run: PaperRunConfig | None = None


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


def _timestamp(value: object, field: str) -> object:
    try:
        normalized = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be convertible to a pandas Timestamp") from exc
    if pd.isna(normalized):
        raise ValueError(f"{field} must be valid")
    return value


def _require_field(mapping: Mapping[str, Any], key: str, section: str) -> object:
    if key not in mapping:
        raise ValueError(f"{section}.{key} is required")
    return mapping[key]


def _parse_data(raw: object) -> ExperimentDataConfig:
    data = _require_mapping(raw, "data")
    source = data.get("source")
    if source not in ("csv", "cache"):
        raise ValueError("data.source must be 'csv' or 'cache'")

    if source == "csv":
        raw_paths = _require_mapping(data.get("paths"), "data.paths")
        if not raw_paths:
            raise ValueError("data.paths must not be empty")
        symbols = build_symbol_universe(raw_paths)
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
        symbols=build_symbol_universe(raw_symbols),
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


def _parse_paper_account_state(raw: object, section: str) -> PaperAccountState:
    account_state = _require_mapping(raw, section)
    return create_paper_account_state(
        timestamp=_require_field(account_state, "timestamp", section),
        starting_cash=_require_field(account_state, "starting_cash", section),
        current_cash=_require_field(account_state, "current_cash", section),
        positions=_require_mapping(
            _require_field(account_state, "positions", section),
            f"{section}.positions",
        ),
    )


def _parse_paper_order(raw: object, section: str) -> PaperOrderRecord:
    order = _require_mapping(raw, section)
    return create_paper_order_record(
        order_id=_require_field(order, "order_id", section),
        timestamp=_require_field(order, "timestamp", section),
        symbol=_require_field(order, "symbol", section),
        side=_require_field(order, "side", section),
        quantity=_require_field(order, "quantity", section),
        status=_require_field(order, "status", section),
    )


def _parse_paper_fill(raw: object, section: str) -> PaperFill:
    fill = _require_mapping(raw, section)
    kwargs: dict[str, object] = {
        "timestamp": _require_field(fill, "timestamp", section),
        "symbol": _require_field(fill, "symbol", section),
        "side": _require_field(fill, "side", section),
        "quantity": _require_field(fill, "quantity", section),
        "price": _require_field(fill, "price", section),
    }
    if "order_id" in fill:
        kwargs["order_id"] = fill["order_id"]
    return create_paper_fill(**kwargs)


def _parse_paper_run(raw: object) -> PaperRunConfig:
    paper_run = _require_mapping(raw, "paper_run")

    run_id = _non_empty_string(
        _require_field(paper_run, "run_id", "paper_run"),
        "paper_run.run_id",
    )
    created_timestamp = _timestamp(
        _require_field(paper_run, "created_timestamp", "paper_run"),
        "paper_run.created_timestamp",
    )
    starting_account_state = _parse_paper_account_state(
        _require_field(paper_run, "starting_account_state", "paper_run"),
        "paper_run.starting_account_state",
    )
    ending_account_state = _parse_paper_account_state(
        _require_field(paper_run, "ending_account_state", "paper_run"),
        "paper_run.ending_account_state",
    )

    raw_orders = _require_field(paper_run, "orders", "paper_run")
    if not isinstance(raw_orders, list):
        raise ValueError("paper_run.orders must be a list")
    orders = tuple(
        _parse_paper_order(order, f"paper_run.orders[{index}]")
        for index, order in enumerate(raw_orders)
    )
    create_paper_order_ledger(orders)

    raw_fills = _require_field(paper_run, "fills", "paper_run")
    if not isinstance(raw_fills, list):
        raise ValueError("paper_run.fills must be a list")
    fills = tuple(
        _parse_paper_fill(fill, f"paper_run.fills[{index}]")
        for index, fill in enumerate(raw_fills)
    )

    return PaperRunConfig(
        run_id=run_id,
        created_timestamp=created_timestamp,
        starting_account_state=starting_account_state,
        ending_account_state=ending_account_state,
        orders=orders,
        fills=fills,
    )


def create_paper_run_request_from_config(
    paper_run: PaperRunConfig,
) -> PaperRunRequest:
    """Convert validated paper-run config into a paper run request."""
    if not isinstance(paper_run, PaperRunConfig):
        raise ValueError("paper_run must be a PaperRunConfig")
    return create_paper_run_request(
        run_id=paper_run.run_id,
        created_timestamp=paper_run.created_timestamp,
        starting_account_state=paper_run.starting_account_state,
        ending_account_state=paper_run.ending_account_state,
        orders=paper_run.orders,
        fills=paper_run.fills,
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
        paper_run=(
            _parse_paper_run(raw["paper_run"])
            if "paper_run" in raw
            else None
        ),
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
