"""Tests for the built-in strategy catalog application service."""

import socket
from dataclasses import Field, FrozenInstanceError, fields
from pathlib import Path

import pytest

from el_psy_quant import config
from el_psy_quant.application import strategy_catalog
from el_psy_quant.application.strategy_catalog import (
    StrategyDetail,
    StrategyNotFoundError,
    StrategyParameterDefinition,
    StrategySummary,
    get_strategy_detail,
    list_strategies,
)
from el_psy_quant.config import MovingAverageCrossoverParameters
from el_psy_quant.strategies import resolve_strategy, supported_strategy_names
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy

STRATEGY_NAME = "moving_average_crossover"
DISPLAY_NAME = "Moving Average Crossover"
PARAMETER_NAMES = (
    "fast_window",
    "slow_window",
    "initial_capital",
    "transaction_cost_rate",
    "slippage_rate",
)


def test_catalog_keys_and_list_order_match_domain_source_exactly() -> None:
    supported = supported_strategy_names()

    assert supported == (STRATEGY_NAME,)
    assert tuple(strategy_catalog._STRATEGY_METADATA) == supported
    assert tuple(summary.name for summary in list_strategies()) == supported
    assert all(
        resolve_strategy(summary.name).name == summary.name
        for summary in list_strategies()
    )


def test_strategy_summary_is_stable_factual_and_immutable() -> None:
    first = list_strategies()
    second = list_strategies()
    summary = first[0]

    assert isinstance(summary, StrategySummary)
    assert summary.name == STRATEGY_NAME
    assert summary.display_name == DISPLAY_NAME
    assert summary.description
    assert "profit" not in summary.description.lower()
    assert "live" not in summary.description.lower()
    assert first is not second
    assert first[0] is not second[0]
    with pytest.raises(FrozenInstanceError):
        summary.display_name = "Changed"  # type: ignore[misc]


def test_strategy_detail_parameter_metadata_is_exact() -> None:
    detail = get_strategy_detail(STRATEGY_NAME)

    assert isinstance(detail, StrategyDetail)
    assert detail.name == STRATEGY_NAME
    assert detail.display_name == DISPLAY_NAME
    assert tuple(parameter.name for parameter in detail.parameters) == PARAMETER_NAMES
    assert tuple(parameter.value_type for parameter in detail.parameters) == (
        "integer",
        "integer",
        "number",
        "number",
        "number",
    )
    assert tuple(parameter.required for parameter in detail.parameters) == (
        True,
        True,
        False,
        False,
        False,
    )
    assert tuple(parameter.default for parameter in detail.parameters) == (
        None,
        None,
        1.0,
        0.0,
        0.0,
    )


def test_parameter_metadata_reflects_configuration_dataclass_order_and_defaults() -> (
    None
):
    config_fields = fields(MovingAverageCrossoverParameters)
    parameters = get_strategy_detail(STRATEGY_NAME).parameters

    assert tuple(field.name for field in config_fields) == PARAMETER_NAMES
    assert tuple(parameter.name for parameter in parameters) == tuple(
        field.name for field in config_fields
    )
    assert tuple(parameter.default for parameter in parameters[2:]) == tuple(
        field.default for field in config_fields[2:]
    )


def test_detail_and_parameter_records_are_immutable_and_do_not_leak_internals() -> None:
    detail = get_strategy_detail(STRATEGY_NAME)

    with pytest.raises(FrozenInstanceError):
        detail.name = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        detail.parameters[0].required = False  # type: ignore[misc]

    assert all(
        isinstance(parameter, StrategyParameterDefinition)
        for parameter in detail.parameters
    )
    for parameter in detail.parameters:
        assert not isinstance(parameter, Field)
        assert not isinstance(parameter.default, Field)
        assert not isinstance(parameter.default, type)
        assert not callable(parameter.default)
        assert parameter.default is None or isinstance(parameter.default, (int, float))


@pytest.mark.parametrize(
    "name",
    ("unknown", "Moving_Average_Crossover", " moving_average_crossover "),
)
def test_unknown_and_non_exact_names_raise_application_error(name: str) -> None:
    with pytest.raises(StrategyNotFoundError, match="strategy not found"):
        get_strategy_detail(name)


def test_catalog_reads_have_no_execution_io_network_or_config_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(MovingAverageCrossoverStrategy, "run", forbidden)
    monkeypatch.setattr(config, "load_experiment_config", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    assert list_strategies()[0].name == STRATEGY_NAME
    assert get_strategy_detail(STRATEGY_NAME).name == STRATEGY_NAME


def test_application_package_exposes_no_persistence_jobs_paper_or_lifecycle_commands() -> (
    None
):
    from el_psy_quant import application

    forbidden = {
        "Repository",
        "Database",
        "JobWorker",
        "run_strategy",
        "start_paper_run",
        "create_lifecycle_proposal",
        "review_lifecycle_proposal",
        "load_experiment_config",
        "discover_experiments",
        "inspect_artifacts",
    }
    assert all(not hasattr(application, name) for name in forbidden)
