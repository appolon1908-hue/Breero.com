import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import BookingStatus


class AddressValidateRequest(BaseModel):
    address: str = Field(min_length=5, max_length=500)
    line1: str | None = None
    city: str | None = None
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    postal_code: str | None = None
    country_code: str = Field(default="US", min_length=2, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinates_are_a_pair(self) -> "AddressValidateRequest":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class AddressValidationResponse(BaseModel):
    serviceable: bool
    formatted_address: str
    address_id: uuid.UUID | None
    service_area_id: uuid.UUID | None
    legal_entity_code: str | None


class AvailabilitySearchRequest(BaseModel):
    service_id: uuid.UUID
    address_id: uuid.UUID
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def valid_range(self) -> "AvailabilitySearchRequest":
        if self.date_to < self.date_from:
            raise ValueError("date_to must not be before date_from")
        if (self.date_to - self.date_from).days > 31:
            raise ValueError("availability range cannot exceed 31 days")
        return self


class AvailabilitySlot(BaseModel):
    start: datetime
    end: datetime
    remaining_capacity: int


class CustomerInput(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=40)


class BookingWindow(BaseModel):
    start: datetime
    end: datetime


class BookingAnswerInput(BaseModel):
    question_id: uuid.UUID
    value: str = Field(min_length=1, max_length=4000)


class BookingCreateRequest(BaseModel):
    service_id: uuid.UUID
    customer: CustomerInput
    address_id: uuid.UUID
    window: BookingWindow
    answers: list[BookingAnswerInput] = Field(default_factory=list)


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reference: str
    status: BookingStatus
    total_amount: Decimal
    currency: str
    window_start: datetime
    window_end: datetime
    payment_required: bool


class BookingCreateResponse(BookingResponse):
    """Creation-only response carrying the one-time guest credential."""

    guest_confirmation_token: str | None = None


class BookingConfirmation(BaseModel):
    booking_id: uuid.UUID
    reference: str
    booking_status: BookingStatus
    payment_status: str
    window_start: datetime
    window_end: datetime
    amount_minor: int
    currency: str
    next_action: Literal[
        "confirmed",
        "retry_payment",
        "booking_unavailable",
        "await_payment_confirmation",
    ]


class CustomerBookingList(BaseModel):
    items: list[BookingResponse]


class OperatorBookingConfirmation(BaseModel):
    worker_id: uuid.UUID
    reason: str = Field(min_length=3, max_length=500)


class OperatorBookingReschedule(BaseModel):
    window: BookingWindow
    reason: str = Field(min_length=3, max_length=500)


class OperatorBookingReassignment(BaseModel):
    worker_id: uuid.UUID
    reason: str = Field(min_length=3, max_length=500)


class OperatorBookingCancellation(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
