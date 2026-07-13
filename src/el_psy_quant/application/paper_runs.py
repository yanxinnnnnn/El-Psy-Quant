"""Synchronous in-memory paper-run application command boundary."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, cast

from el_psy_quant.paper import (
    PAPER_RUN_REQUEST_SCHEMA_VERSION,
    PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
    PaperAccountState,
    PaperFill,
    PaperOrderRecord,
    PaperTradingArtifact,
    create_paper_account_state,
    create_paper_fill,
    create_paper_order_record,
    create_paper_run_request,
    run_paper_trading_request,
)

_INVALID_MESSAGE = "paper run request is invalid"


class PaperRunInvalidError(Exception):
    """Sanitized failure for one invalid paper-run command."""

    def __init__(self) -> None:
        super().__init__(_INVALID_MESSAGE)


@dataclass(frozen=True)
class PaperAccountStateCommandInput:
    """Transport values for one explicit paper account state."""

    timestamp: object
    starting_cash: object
    current_cash: object
    positions: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", MappingProxyType(dict(self.positions)))


@dataclass(frozen=True)
class PaperOrderCommandInput:
    """Transport values for one explicit paper order."""

    order_id: object
    timestamp: object
    symbol: object
    side: object
    quantity: object
    status: object


@dataclass(frozen=True)
class PaperFillCommandInput:
    """Transport values for one explicit paper fill."""

    timestamp: object
    symbol: object
    side: object
    quantity: object
    price: object
    order_id: object | None = None


@dataclass(frozen=True)
class PaperRunCommand:
    """Explicit synchronous command for one in-memory paper run."""

    run_id: object
    created_timestamp: object
    starting_account_state: PaperAccountStateCommandInput
    ending_account_state: PaperAccountStateCommandInput
    orders: tuple[PaperOrderCommandInput, ...]
    fills: tuple[PaperFillCommandInput, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "orders", tuple(self.orders))
        object.__setattr__(self, "fills", tuple(self.fills))


@dataclass(frozen=True)
class PaperPositionView:
    symbol: str
    quantity: float


@dataclass(frozen=True)
class PaperAccountStateView:
    timestamp: str
    starting_cash: float
    current_cash: float
    positions: tuple[PaperPositionView, ...]


@dataclass(frozen=True)
class PaperOrderView:
    order_id: str
    timestamp: str
    symbol: str
    side: str
    quantity: float
    status: str


@dataclass(frozen=True)
class PaperFillView:
    timestamp: str
    symbol: str
    side: str
    quantity: float
    price: float
    order_id: str | None


@dataclass(frozen=True)
class PaperPositionChangeView:
    symbol: str
    starting_quantity: float
    ending_quantity: float
    quantity_change: float


@dataclass(frozen=True)
class PaperSessionSummaryView:
    session_start_timestamp: str
    session_end_timestamp: str
    starting_cash: float
    ending_cash: float
    cash_change: float
    starting_positions: tuple[PaperPositionView, ...]
    ending_positions: tuple[PaperPositionView, ...]
    position_changes: tuple[PaperPositionChangeView, ...]
    order_count: int
    fill_count: int


@dataclass(frozen=True)
class PaperTradingArtifactView:
    schema_version: Literal[1]
    created_timestamp: str
    starting_account_state: PaperAccountStateView
    ending_account_state: PaperAccountStateView
    orders: tuple[PaperOrderView, ...]
    fills: tuple[PaperFillView, ...]
    session_summary: PaperSessionSummaryView


@dataclass(frozen=True)
class PaperRunCommandResult:
    run_id: str
    request_schema_version: Literal[1]
    artifact: PaperTradingArtifactView


def _account_state(command: PaperAccountStateCommandInput) -> PaperAccountState:
    return create_paper_account_state(
        timestamp=command.timestamp,
        starting_cash=command.starting_cash,  # type: ignore[arg-type]
        current_cash=command.current_cash,  # type: ignore[arg-type]
        positions=command.positions,  # type: ignore[arg-type]
    )


def _order(command: PaperOrderCommandInput) -> PaperOrderRecord:
    return create_paper_order_record(
        order_id=command.order_id,  # type: ignore[arg-type]
        timestamp=command.timestamp,
        symbol=command.symbol,  # type: ignore[arg-type]
        side=command.side,  # type: ignore[arg-type]
        quantity=command.quantity,  # type: ignore[arg-type]
        status=command.status,  # type: ignore[arg-type]
    )


def _fill(command: PaperFillCommandInput) -> PaperFill:
    return create_paper_fill(
        timestamp=command.timestamp,
        symbol=command.symbol,  # type: ignore[arg-type]
        side=command.side,  # type: ignore[arg-type]
        quantity=command.quantity,  # type: ignore[arg-type]
        price=command.price,  # type: ignore[arg-type]
        order_id=command.order_id,  # type: ignore[arg-type]
    )


def _position_views(
    positions: Sequence[tuple[str, float]],
) -> tuple[PaperPositionView, ...]:
    return tuple(
        PaperPositionView(symbol=symbol, quantity=quantity)
        for symbol, quantity in positions
    )


def _account_view(state: PaperAccountState) -> PaperAccountStateView:
    return PaperAccountStateView(
        timestamp=state.timestamp.isoformat(),
        starting_cash=state.starting_cash,
        current_cash=state.current_cash,
        positions=_position_views(state.positions),
    )


def _order_view(order: PaperOrderRecord) -> PaperOrderView:
    return PaperOrderView(
        order_id=order.order_id,
        timestamp=order.timestamp.isoformat(),
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        status=order.status,
    )


def _fill_view(fill: PaperFill) -> PaperFillView:
    return PaperFillView(
        timestamp=fill.timestamp.isoformat(),
        symbol=fill.symbol,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        order_id=fill.order_id,
    )


def _session_view(artifact: PaperTradingArtifact) -> PaperSessionSummaryView:
    payload = artifact.session_summary.to_dict()
    changes = cast(list[dict[str, object]], payload["position_changes"])
    return PaperSessionSummaryView(
        session_start_timestamp=cast(str, payload["session_start_timestamp"]),
        session_end_timestamp=cast(str, payload["session_end_timestamp"]),
        starting_cash=cast(float, payload["starting_cash"]),
        ending_cash=cast(float, payload["ending_cash"]),
        cash_change=cast(float, payload["cash_change"]),
        starting_positions=_position_views(
            artifact.session_summary.starting_account_state.positions
        ),
        ending_positions=_position_views(
            artifact.session_summary.ending_account_state.positions
        ),
        position_changes=tuple(
            PaperPositionChangeView(
                symbol=cast(str, change["symbol"]),
                starting_quantity=cast(float, change["starting_quantity"]),
                ending_quantity=cast(float, change["ending_quantity"]),
                quantity_change=cast(float, change["quantity_change"]),
            )
            for change in changes
        ),
        order_count=cast(int, payload["order_count"]),
        fill_count=cast(int, payload["fill_count"]),
    )


def _artifact_view(artifact: PaperTradingArtifact) -> PaperTradingArtifactView:
    return PaperTradingArtifactView(
        schema_version=PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
        created_timestamp=artifact.created_timestamp.isoformat(),
        starting_account_state=_account_view(artifact.starting_account_state),
        ending_account_state=_account_view(artifact.ending_account_state),
        orders=tuple(_order_view(order) for order in artifact.orders),
        fills=tuple(_fill_view(fill) for fill in artifact.fills),
        session_summary=_session_view(artifact),
    )


def execute_paper_run(*, command: PaperRunCommand) -> PaperRunCommandResult:
    """Execute one explicit paper run synchronously and only in memory."""
    if type(command) is not PaperRunCommand:
        raise PaperRunInvalidError()
    try:
        starting_state = _account_state(command.starting_account_state)
        ending_state = _account_state(command.ending_account_state)
        orders = tuple(_order(order) for order in command.orders)
        fills = tuple(_fill(fill) for fill in command.fills)
        request = create_paper_run_request(
            run_id=command.run_id,  # type: ignore[arg-type]
            created_timestamp=command.created_timestamp,
            starting_account_state=starting_state,
            ending_account_state=ending_state,
            orders=orders,
            fills=fills,
        )
        artifact = run_paper_trading_request(request)
    except ValueError as exc:
        raise PaperRunInvalidError() from exc
    return PaperRunCommandResult(
        run_id=request.run_id,
        request_schema_version=PAPER_RUN_REQUEST_SCHEMA_VERSION,
        artifact=_artifact_view(artifact),
    )
