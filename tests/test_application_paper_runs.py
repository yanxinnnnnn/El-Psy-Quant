"""Tests for the synchronous in-memory paper-run application command."""

import inspect
import math
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import el_psy_quant.application.paper_runs as service
from el_psy_quant import configured_paper
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperAccountStateView,
    PaperFillCommandInput,
    PaperFillView,
    PaperOrderCommandInput,
    PaperOrderView,
    PaperPositionChangeView,
    PaperPositionView,
    PaperRunCommand,
    PaperRunCommandResult,
    PaperRunInvalidError,
    PaperSessionSummaryView,
    PaperTradingArtifactView,
    execute_paper_run,
)
from el_psy_quant.strategies.moving_average import MovingAverageCrossoverStrategy


def _account(
    *,
    timestamp: object,
    current_cash: object,
    positions: dict[str, object],
) -> PaperAccountStateCommandInput:
    return PaperAccountStateCommandInput(
        timestamp=timestamp,
        starting_cash=10_000,
        current_cash=current_cash,
        positions=positions,
    )


def _command(
    *,
    run_id: object = " paper-run-001 ",
    created_timestamp: object = "2026-07-13T12:00:00Z",
    starting: PaperAccountStateCommandInput | None = None,
    ending: PaperAccountStateCommandInput | None = None,
    orders: tuple[PaperOrderCommandInput, ...] | None = None,
    fills: tuple[PaperFillCommandInput, ...] | None = None,
) -> PaperRunCommand:
    return PaperRunCommand(
        run_id=run_id,
        created_timestamp=created_timestamp,
        starting_account_state=starting
        or _account(
            timestamp="2026-07-13T12:00:00Z",
            current_cash=10_000,
            positions={"MSFT": 1, "aapl": 2},
        ),
        ending_account_state=ending
        or _account(
            timestamp="2026-07-13T12:05:00Z",
            current_cash=9_000,
            positions={"MSFT": 0.5, "aapl": 12},
        ),
        orders=orders
        if orders is not None
        else (
            PaperOrderCommandInput(
                order_id=" order-002 ",
                timestamp="2026-07-13T12:03:00Z",
                symbol="msft",
                side="SELL",
                quantity=0.5,
                status="FILLED",
            ),
            PaperOrderCommandInput(
                order_id=" order-001 ",
                timestamp="2026-07-13T12:01:00Z",
                symbol="aapl",
                side="BUY",
                quantity=10,
                status="FILLED",
            ),
        ),
        fills=fills
        if fills is not None
        else (
            PaperFillCommandInput(
                order_id=None,
                timestamp="2026-07-13T12:04:00Z",
                symbol="msft",
                side="SELL",
                quantity=0.5,
                price=200,
            ),
            PaperFillCommandInput(
                order_id=" order-001 ",
                timestamp="2026-07-13T12:02:00Z",
                symbol="aapl",
                side="BUY",
                quantity=10,
                price=100,
            ),
        ),
    )


def test_public_command_and_result_contracts_are_immutable_and_keyword_only() -> None:
    command = _command()
    result = execute_paper_run(command=command)

    assert list(inspect.signature(execute_paper_run).parameters.values())[0].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    for value in (
        command,
        command.starting_account_state,
        command.orders[0],
        command.fills[0],
        result,
        result.artifact,
        result.artifact.starting_account_state,
        result.artifact.orders[0],
        result.artifact.fills[0],
        result.artifact.session_summary,
        result.artifact.session_summary.starting_positions[0],
        result.artifact.session_summary.position_changes[0],
    ):
        with pytest.raises(FrozenInstanceError):
            value.unexpected = "changed"  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        command.starting_account_state.positions["AAPL"] = 99  # type: ignore[index]
    assert isinstance(command.orders, tuple)
    assert isinstance(command.fills, tuple)


def test_execution_uses_all_public_factories_and_only_run_boundary(monkeypatch) -> None:
    calls: list[str] = []
    expected_counts = {
        "create_paper_account_state": 2,
        "create_paper_order_record": 2,
        "create_paper_fill": 2,
        "create_paper_run_request": 1,
        "run_paper_trading_request": 1,
    }
    for name in expected_counts:
        original = getattr(service, name)

        def tracked(*args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(service, name, tracked)

    execute_paper_run(command=_command())

    assert {name: calls.count(name) for name in expected_counts} == expected_counts
    assert calls[-1] == "run_paper_trading_request"


def test_normalized_result_preserves_explicit_order_and_domain_position_order() -> None:
    result = execute_paper_run(command=_command())

    assert isinstance(result, PaperRunCommandResult)
    assert result.run_id == "paper-run-001"
    assert result.request_schema_version == 1
    assert result.artifact.schema_version == 1
    assert result.artifact.created_timestamp == "2026-07-13T12:00:00+00:00"
    assert tuple(position.symbol for position in result.artifact.starting_account_state.positions) == (
        "AAPL",
        "MSFT",
    )
    assert tuple(order.order_id for order in result.artifact.orders) == (
        "order-002",
        "order-001",
    )
    assert tuple(fill.symbol for fill in result.artifact.fills) == ("MSFT", "AAPL")
    assert result.artifact.orders[0].side == "sell"
    assert result.artifact.orders[1].status == "filled"
    assert result.artifact.fills[0].order_id is None
    assert result.artifact.fills[1].order_id == "order-001"
    assert result.artifact.session_summary.cash_change == -1_000.0
    assert result.artifact.session_summary.order_count == 2
    assert result.artifact.session_summary.fill_count == 2


def test_empty_orders_and_fills_are_supported_without_inferring_values() -> None:
    ending = _account(
        timestamp="2026-07-13T12:05:00Z",
        current_cash=9_999,
        positions={},
    )
    result = execute_paper_run(command=_command(ending=ending, orders=(), fills=()))

    assert result.artifact.orders == ()
    assert result.artifact.fills == ()
    assert result.artifact.ending_account_state.current_cash == 9_999.0
    assert result.artifact.session_summary.order_count == 0
    assert result.artifact.session_summary.fill_count == 0


def test_source_command_objects_remain_unchanged() -> None:
    command = _command()
    before = (
        command.run_id,
        command.created_timestamp,
        dict(command.starting_account_state.positions),
        dict(command.ending_account_state.positions),
        command.orders,
        command.fills,
    )

    execute_paper_run(command=command)

    assert before == (
        command.run_id,
        command.created_timestamp,
        dict(command.starting_account_state.positions),
        dict(command.ending_account_state.positions),
        command.orders,
        command.fills,
    )


def _invalid_cases() -> tuple[PaperRunCommand, ...]:
    valid = _command()
    duplicate = replace(valid.orders[1], order_id="order-002")
    return (
        replace(valid, created_timestamp="not-a-date"),
        replace(valid, starting_account_state=replace(valid.starting_account_state, current_cash=True)),
        replace(valid, ending_account_state=replace(valid.ending_account_state, current_cash=math.inf)),
        replace(valid, starting_account_state=replace(valid.starting_account_state, positions={"AAPL": True})),
        replace(valid, starting_account_state=replace(valid.starting_account_state, positions={"AAPL": math.inf})),
        replace(valid, orders=(replace(valid.orders[0], symbol=""),)),
        replace(valid, orders=(replace(valid.orders[0], side="hold"),)),
        replace(valid, orders=(replace(valid.orders[0], status="pending"),)),
        replace(valid, orders=(replace(valid.orders[0], quantity=True),)),
        replace(valid, orders=(replace(valid.orders[0], quantity=math.inf),)),
        replace(valid, orders=(valid.orders[0], duplicate)),
        replace(valid, fills=(replace(valid.fills[0], symbol=""),)),
        replace(valid, fills=(replace(valid.fills[0], side="hold"),)),
        replace(valid, fills=(replace(valid.fills[0], quantity=True),)),
        replace(valid, fills=(replace(valid.fills[0], price=math.inf),)),
    )


@pytest.mark.parametrize("command", _invalid_cases())
def test_domain_invalid_commands_use_one_sanitized_application_error(
    command: PaperRunCommand,
) -> None:
    with pytest.raises(PaperRunInvalidError) as raised:
        execute_paper_run(command=command)

    assert str(raised.value) == "paper run request is invalid"
    assert "AAPL" not in str(raised.value)
    assert "order" not in str(raised.value)


def test_invalid_command_object_type_uses_sanitized_application_error() -> None:
    with pytest.raises(PaperRunInvalidError, match="^paper run request is invalid$"):
        execute_paper_run(command=object())  # type: ignore[arg-type]


def test_public_application_exports_are_exact_types() -> None:
    from el_psy_quant import application

    expected = (
        PaperAccountStateCommandInput,
        PaperOrderCommandInput,
        PaperFillCommandInput,
        PaperRunCommand,
        PaperPositionView,
        PaperAccountStateView,
        PaperOrderView,
        PaperFillView,
        PaperPositionChangeView,
        PaperSessionSummaryView,
        PaperTradingArtifactView,
        PaperRunCommandResult,
        PaperRunInvalidError,
    )
    assert all(getattr(application, item.__name__) is item for item in expected)
    assert application.execute_paper_run is execute_paper_run


def test_command_has_no_io_config_strategy_network_or_persistence_side_effects(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(configured_paper, "run_configured_paper_workflow", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(MovingAverageCrossoverStrategy, "run", forbidden)

    result = execute_paper_run(command=_command())

    assert result.run_id == "paper-run-001"
    assert list(tmp_path.iterdir()) == []
    for forbidden_name in (
        "path",
        "job_id",
        "status",
        "repository",
        "retry",
        "cancel",
        "broker",
    ):
        assert not hasattr(result, forbidden_name)
