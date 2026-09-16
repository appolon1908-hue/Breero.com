import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.payments.models import PaymentPurpose, PaymentStatus


class ProfilePatch(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=160)
    phone: str | None = Field(None, min_length=3, max_length=40)


class ProfileRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str
    email_verified: bool


class AddressInput(BaseModel):
    line1: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=32)
    country_code: str = Field(min_length=2, max_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line1: str
    city: str
    postal_code: str
    country_code: str


class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class CustomerPaymentRead(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID | None
    quote_id: uuid.UUID | None
    payment_purpose: PaymentPurpose
    provider: str
    status: PaymentStatus
    amount_minor: int
    currency: str
    captured_amount_minor: int
    refunded_amount_minor: int
    failure_code: str | None
    created_at: datetime
    updated_at: datetime
