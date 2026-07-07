"""Local in-memory paper run execution boundary."""

from el_psy_quant.paper.artifact import (
    PaperTradingArtifact,
    create_paper_trading_artifact,
)
from el_psy_quant.paper.run_request import PaperRunRequest
from el_psy_quant.paper.session import create_paper_trading_session_summary


def run_paper_trading_request(
    request: PaperRunRequest,
) -> PaperTradingArtifact:
    """Build an in-memory paper trading artifact from an explicit request."""
    if not isinstance(request, PaperRunRequest):
        raise ValueError("request must be a PaperRunRequest")

    session_summary = create_paper_trading_session_summary(
        starting_account_state=request.starting_account_state,
        ending_account_state=request.ending_account_state,
        orders=request.orders,
        fills=request.fills,
    )

    return create_paper_trading_artifact(
        created_timestamp=request.created_timestamp,
        starting_account_state=request.starting_account_state,
        ending_account_state=request.ending_account_state,
        orders=request.orders,
        fills=request.fills,
        session_summary=session_summary,
    )
