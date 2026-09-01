"""API-key authentication for the third-party surface.

Separate from `app.domains.auth.dependencies` on purpose. An integrator credential
must never traverse the interactive auth path: no session, no refresh, no role
mapping, no portal access.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis_client
from app.db.session import get_db

from .models import ApiClient, ApiKey, ApiScope
from .service import PartnerApiService, require_partner_api_enabled

bearer = HTTPBearer(auto_error=False)


class PartnerPrincipal:
    """The authenticated third party, and the grant it presented."""

    def __init__(self, client: ApiClient, key: ApiKey) -> None:
        self.client = client
        self.key = key

    @property
    def vendor_id(self):
        """The provider this client is confined to, or None for platform-wide."""
        return self.client.vendor_id


async def _enforce_key_rate_limit(request: Request, key: ApiKey) -> None:
    """Per-key ceiling, so one integrator cannot consume the shared budget.

    Keyed by the key prefix rather than the caller address: an integrator behind a
    NAT or a serverless platform has no stable address, and the credential is the
    thing being budgeted.
    """
    import redis.asyncio as redis

    client = get_redis_client(request.app)
    bucket = f"partner-api:{key.prefix}"
    try:
        async with client.pipeline(transaction=True) as pipeline:
            pipeline.incr(bucket)
            pipeline.expire(bucket, 60, nx=True)
            count, _ = await pipeline.execute()
    except redis.RedisError as exc:
        raise HTTPException(503, "Rate limiter unavailable") from exc
    if int(count) > key.rate_limit_per_minute:
        raise HTTPException(
            429,
            "API rate limit exceeded",
            headers={"Retry-After": "60"},
        )


async def partner_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PartnerPrincipal:
    require_partner_api_enabled()
    if not credentials:
        raise HTTPException(401, "Invalid API credentials")
    client, key = await PartnerApiService(session).authenticate(credentials.credentials)
    await _enforce_key_rate_limit(request, key)
    # The touch from authenticate() is worth persisting even on an otherwise read-only
    # request, so an operator can see which keys are actually in use before revoking.
    await session.commit()
    return PartnerPrincipal(client, key)


def require_api_scope(scope: ApiScope):
    async def dependency(
        principal: Annotated[PartnerPrincipal, Depends(partner_principal)],
    ) -> PartnerPrincipal:
        PartnerApiService.require_scope(principal.key, scope)
        return principal

    return dependency
