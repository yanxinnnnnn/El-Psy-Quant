"""Versioned synchronous in-memory paper-run command route."""

from http import HTTPStatus

from fastapi import APIRouter

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.paper_run_schemas import (
    PaperAccountStateCommandRequest,
    PaperAccountStateResponse,
    PaperFillCommandRequest,
    PaperFillResponse,
    PaperOrderCommandRequest,
    PaperOrderResponse,
    PaperPositionChangeResponse,
    PaperPositionResponse,
    PaperRunCommandRequest,
    PaperRunCommandResponse,
    PaperSessionSummaryResponse,
    PaperTradingArtifactResponse,
)
from el_psy_quant.application import (
    PaperAccountStateCommandInput,
    PaperAccountStateView,
    PaperFillCommandInput,
    PaperFillView,
    PaperOrderCommandInput,
    PaperOrderView,
    PaperPositionView,
    PaperRunCommand,
    PaperRunCommandResult,
    PaperRunInvalidError,
    execute_paper_run,
)

router = APIRouter(prefix="/paper-runs")


def _account_command(
    request: PaperAccountStateCommandRequest,
) -> PaperAccountStateCommandInput:
    return PaperAccountStateCommandInput(
        timestamp=request.timestamp,
        starting_cash=request.starting_cash,
        current_cash=request.current_cash,
        positions=request.positions,
    )


def _order_command(request: PaperOrderCommandRequest) -> PaperOrderCommandInput:
    return PaperOrderCommandInput(
        order_id=request.order_id,
        timestamp=request.timestamp,
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        status=request.status,
    )


def _fill_command(request: PaperFillCommandRequest) -> PaperFillCommandInput:
    return PaperFillCommandInput(
        timestamp=request.timestamp,
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        price=request.price,
        order_id=request.order_id,
    )


def _position_response(position: PaperPositionView) -> PaperPositionResponse:
    return PaperPositionResponse(symbol=position.symbol, quantity=position.quantity)


def _account_response(state: PaperAccountStateView) -> PaperAccountStateResponse:
    return PaperAccountStateResponse(
        timestamp=state.timestamp,
        starting_cash=state.starting_cash,
        current_cash=state.current_cash,
        positions=[_position_response(position) for position in state.positions],
    )


def _order_response(order: PaperOrderView) -> PaperOrderResponse:
    return PaperOrderResponse(
        order_id=order.order_id,
        timestamp=order.timestamp,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        status=order.status,
    )


def _fill_response(fill: PaperFillView) -> PaperFillResponse:
    return PaperFillResponse(
        timestamp=fill.timestamp,
        symbol=fill.symbol,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        order_id=fill.order_id,
    )


def _result_response(result: PaperRunCommandResult) -> PaperRunCommandResponse:
    artifact = result.artifact
    summary = artifact.session_summary
    return PaperRunCommandResponse(
        run_id=result.run_id,
        request_schema_version=result.request_schema_version,
        artifact=PaperTradingArtifactResponse(
            schema_version=artifact.schema_version,
            created_timestamp=artifact.created_timestamp,
            starting_account_state=_account_response(
                artifact.starting_account_state
            ),
            ending_account_state=_account_response(artifact.ending_account_state),
            orders=[_order_response(order) for order in artifact.orders],
            fills=[_fill_response(fill) for fill in artifact.fills],
            session_summary=PaperSessionSummaryResponse(
                session_start_timestamp=summary.session_start_timestamp,
                session_end_timestamp=summary.session_end_timestamp,
                starting_cash=summary.starting_cash,
                ending_cash=summary.ending_cash,
                cash_change=summary.cash_change,
                starting_positions=[
                    _position_response(position)
                    for position in summary.starting_positions
                ],
                ending_positions=[
                    _position_response(position) for position in summary.ending_positions
                ],
                position_changes=[
                    PaperPositionChangeResponse(
                        symbol=change.symbol,
                        starting_quantity=change.starting_quantity,
                        ending_quantity=change.ending_quantity,
                        quantity_change=change.quantity_change,
                    )
                    for change in summary.position_changes
                ],
                order_count=summary.order_count,
                fill_count=summary.fill_count,
            ),
        ),
    )


@router.post("", response_model=PaperRunCommandResponse)
async def post_paper_run(request: PaperRunCommandRequest) -> PaperRunCommandResponse:
    """Execute one explicit paper run synchronously and only in memory."""
    command = PaperRunCommand(
        run_id=request.run_id,
        created_timestamp=request.created_timestamp,
        starting_account_state=_account_command(request.starting_account_state),
        ending_account_state=_account_command(request.ending_account_state),
        orders=tuple(_order_command(order) for order in request.orders),
        fills=tuple(_fill_command(fill) for fill in request.fills),
    )
    try:
        result = execute_paper_run(command=command)
    except PaperRunInvalidError as exc:
        raise PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="paper_run_invalid",
            message="Paper run request is invalid",
        ) from exc
    return _result_response(result)
