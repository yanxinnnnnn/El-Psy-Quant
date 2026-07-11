"""Local application-process health route."""

from fastapi import APIRouter

from el_psy_quant.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Report only that the local API process can serve a request."""
    return HealthResponse(
        status="ok",
        service="el-psy-quant",
        api_version="v1",
    )
