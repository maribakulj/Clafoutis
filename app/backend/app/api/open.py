"""Open-in-Mirador endpoint.

Produces a minimal Mirador workspace state for a list of manifest URLs.
Logic stays on the server so the MCP layer (specs §13) can reuse the
exact same flow without duplicating Mirador config code.
"""

from fastapi import APIRouter

from app.models.manifest_models import (
    MiradorWorkspaceState,
    OpenInMiradorRequest,
    OpenInMiradorResponse,
)
from app.utils.errors import BadRequestError
from app.utils.url_validation import validate_http_url

router = APIRouter(tags=["open"])


@router.post("/open", response_model=OpenInMiradorResponse)
async def open_in_mirador(payload: OpenInMiradorRequest) -> OpenInMiradorResponse:
    """Validate manifest URLs and return a shareable Mirador workspace state."""

    deduped: list[str] = []
    seen: set[str] = set()
    for raw in payload.manifest_urls:
        try:
            safe = validate_http_url(raw)
        except BadRequestError as err:
            raise BadRequestError(f"Invalid manifest URL '{raw}': {err}") from err
        if safe in seen:
            continue
        seen.add(safe)
        deduped.append(safe)

    windows = [{"manifestId": url} for url in deduped]
    state = MiradorWorkspaceState(
        windows=windows,
        catalog=windows,
        workspace={
            "id": payload.workspace,
            "viewingDirection": "left-to-right",
            "showZoomControls": True,
        },
    )
    return OpenInMiradorResponse(manifest_urls=deduped, mirador_state=state)
