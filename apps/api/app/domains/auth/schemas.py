import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.auth.models import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)
    phone: str | None = Field(default=None, min_length=5, max_length=32)


class ProviderRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    contact_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=5, max_length=32)
    legal_name: str = Field(min_length=2, max_length=180)
    display_name: str = Field(min_length=2, max_length=120)
    provider_type: str = Field(default="COMPANY", pattern="^(COMPANY|INDEPENDENT)$")
    business_address: str = Field(min_length=5, max_length=240)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=3)
    postal_code: str = Field(pattern=r"^\d{5}(?:-\d{4})?$")
    timezone_id: str = Field(min_length=3, max_length=64)
    service_slugs: list[str] = Field(min_length=1, max_length=50)
    service_postal_codes: list[str] = Field(min_length=1, max_length=500)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class TokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(TokenRequest):
    new_password: str = Field(min_length=10, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class SetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool


class ProviderRegistrationResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    user: UserRead
    provider_organization_id: uuid.UUID
    onboarding_status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    user: UserRead


class BrowserSessionResponse(BaseModel):
    user: UserRead


class MessageResponse(BaseModel):
    message: str
