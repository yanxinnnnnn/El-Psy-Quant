"""Read-only discovery of one explicitly installed demo workspace."""

from http import HTTPStatus

from fastapi import APIRouter, Request

from el_psy_quant.api.demo_workspace_schemas import (
    DemoWorkspaceDescriptorResponse,
)
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.demo_workspace import (
    DEMO_WORKSPACE_MODE,
    DemoWorkspaceUnavailableError,
    load_demo_workspace_descriptor,
)

router = APIRouter(prefix="/demo-workspace")


@router.get("", response_model=DemoWorkspaceDescriptorResponse)
def get_demo_workspace(request: Request) -> DemoWorkspaceDescriptorResponse:
    """Return path-free guided navigation only when demo mode is configured."""
    mode = getattr(request.app.state, "workspace_mode", None)
    root = getattr(request.app.state, "demo_workspace_root", None)
    if mode != DEMO_WORKSPACE_MODE or root is None:
        raise PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="demo_workspace_not_configured",
            message="Demo workspace is not configured",
        )
    try:
        descriptor = load_demo_workspace_descriptor(root)
        return DemoWorkspaceDescriptorResponse.model_validate(descriptor.to_dict())
    except (DemoWorkspaceUnavailableError, ValueError) as exc:
        raise PublicApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="demo_workspace_unavailable",
            message="Demo workspace is unavailable",
        ) from exc
