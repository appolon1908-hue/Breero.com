import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.domains.auth.browser_session import ACCESS_COOKIE
from app.domains.auth.models import User, UserRole
from app.domains.auth.repository import UserRepository
from app.domains.auth.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials if credentials else request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    claims = decode_access_token(token)
    repository = UserRepository(session)
    if settings.keycloak_enabled:
        email = str(claims.get("email") or "").strip().lower()
        if not email or not claims.get("email_verified"):
            raise HTTPException(status_code=401, detail="Verified account required")
        user = await repository.by_email(email)
        required_role = {
            UserRole.customer: "breero_customer",
            UserRole.vendor_admin: "breero_provider",
            UserRole.technician: "breero_worker",
            UserRole.operations: "breero_dispatcher",
            UserRole.finance: "breero_support",
            UserRole.admin: "breero_admin",
        }
        token_roles = set((claims.get("realm_access") or {}).get("roles") or [])
        if not user or required_role[user.role] not in token_roles:
            raise HTTPException(status_code=403, detail="Account role is not authorized")
    else:
        try:
            user_id = uuid.UUID(claims["sub"])
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        user = await repository.by_id(user_id)
    if not user or not user.is_active or (
        not settings.keycloak_enabled and claims.get("cv", 1) != user.credential_version
    ):
        raise HTTPException(status_code=401, detail="Invalid or inactive account")
    return user


async def optional_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if not credentials and not request.cookies.get(ACCESS_COOKIE):
        return None
    return await current_user(request, credentials, session)


def require_roles(*roles: UserRole) -> Callable:
    async def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency
