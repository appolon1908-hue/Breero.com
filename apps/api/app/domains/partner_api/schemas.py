import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from .models import ApiClientStatus, ApiScope


class ApiClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    contact_email: EmailStr
    vendor_id: uuid.UUID | None = None


class ApiClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    contact_email: str
    status: ApiClientStatus
    vendor_id: uuid.UUID | None
    created_at: datetime


class ApiKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=2, max_length=120)
    scopes: list[ApiScope] = Field(min_length=1)
    expires_in_days: int = Field(default=90, ge=1, le=365)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=6000)

    @field_validator("scopes")
    @classmethod
    def unique_scopes(cls, value: list[ApiScope]) -> list[ApiScope]:
        if len(set(value)) != len(value):
            raise ValueError("scopes must be unique")
        return value


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    label: str
    prefix: str
    scopes: list[str]
    expires_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None
    rate_limit_per_minute: int


class ApiKeyIssued(ApiKeyRead):
    """The only response that ever carries the secret.

    Returned once, at creation. Nothing stores it and no later read can reproduce it.
    """

    secret: str


class WebhookSubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    event_types: list[str] = Field(min_length=1, max_length=20)

    @field_validator("url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        # Deliveries carry customer data and a signature; plaintext transport would
        # expose both.
        if value.scheme != "https":
            raise ValueError("webhook URL must use https")
        return value


class WebhookSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    url: str
    event_types: list[str]
    active: bool
    failure_count: int
    disabled_reason: str | None
    created_at: datetime


class WebhookSubscriptionIssued(WebhookSubscriptionRead):
    """Carries the signing secret once, at creation."""

    secret: str
