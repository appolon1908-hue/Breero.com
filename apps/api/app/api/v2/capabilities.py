from fastapi import APIRouter

from app.api.v2.schemas import ApiError
from app.config import settings
from app.domains.capabilities.schemas import PublicCapabilities
from app.domains.capabilities.service import public_capabilities

router = APIRouter()


@router.get(
    "/capabilities",
    response_model=PublicCapabilities,
    operation_id="get_v2_capabilities",
    responses={
        429: {"model": ApiError, "description": "Rate limited"},
        500: {"model": ApiError, "description": "Platform failure"},
        503: {"model": ApiError, "description": "Dependency unavailable"},
    },
)
async def capabilities() -> PublicCapabilities:
    """Return the same effective capability projection exposed by API V1."""

    return public_capabilities(settings)
