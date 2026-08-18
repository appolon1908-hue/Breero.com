from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ProviderRegisterRequest,
    ProviderRegistrationResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SetPasswordRequest,
    TokenRequest,
    TokenResponse,
    UserRead,
)
from app.domains.auth.service import AuthService

router = APIRouter()


def client(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("user-agent"), request.client.host if request.client else None


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("register", 5, 60))],
) -> TokenResponse:
    if settings.keycloak_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public account registration is disabled",
        )
    return await AuthService(session).register(data, *client(request))


@router.post("/register/client", response_model=TokenResponse, status_code=201)
async def register_client(
    data: RegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("register-client", 5, 60))],
) -> TokenResponse:
    if settings.keycloak_enabled:
        raise HTTPException(status_code=403, detail="Public account registration is disabled")
    return await AuthService(session).register(data, *client(request))


@router.post("/register/provider", response_model=ProviderRegistrationResponse, status_code=201)
async def register_provider(
    data: ProviderRegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("register-provider", 3, 300))],
) -> ProviderRegistrationResponse:
    if settings.keycloak_enabled:
        raise HTTPException(status_code=403, detail="Public provider registration is disabled")
    token, vendor = await AuthService(session).register_provider(data, *client(request))
    return ProviderRegistrationResponse(
        **token.model_dump(),
        provider_organization_id=vendor.id,
        onboarding_status=vendor.onboarding_status,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("login", 10, 60))],
) -> TokenResponse:
    return await AuthService(session).login(data, *client(request))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest, request: Request, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).refresh(data.refresh_token, *client(request))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, session: Annotated[AsyncSession, Depends(get_db)]) -> None:
    await AuthService(session).logout(data.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await AuthService(session).logout_all(user)


@router.post("/password/forgot", response_model=MessageResponse)
async def forgot(
    data: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("password-forgot", 5, 300))],
) -> MessageResponse:
    await AuthService(session).forgot_password(str(data.email))
    return MessageResponse(message="If the account exists, reset instructions have been sent")


@router.post("/password/reset", response_model=MessageResponse)
async def reset(
    data: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("password-reset", 10, 300))],
) -> MessageResponse:
    await AuthService(session).reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset")


@router.post("/password/change", response_model=MessageResponse)
async def change(
    data: ChangePasswordRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await AuthService(session).change_password(user, data.current_password, data.new_password)
    return MessageResponse(message="Password changed; active sessions revoked")


@router.post("/password/set", response_model=MessageResponse)
async def set_password(
    data: SetPasswordRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await AuthService(session).set_initial_password(user, data.new_password)
    return MessageResponse(message="Password set; active sessions revoked")


@router.post("/email/verify", response_model=MessageResponse)
async def verify(
    data: TokenRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).verify_email(data.token)
    return MessageResponse(message="Email verified")


@router.post("/email/resend-verification", response_model=MessageResponse)
async def resend(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).resend_verification(user)
    return MessageResponse(message="Verification sent if required")


@router.post("/email/resend", response_model=MessageResponse)
async def resend_alias(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    return await resend(user, session)


@router.post("/phone/verify", response_model=MessageResponse)
async def verify_phone(
    data: TokenRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await AuthService(session).verify_phone(user, data.token)
    return MessageResponse(message="Phone verified")


@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user
