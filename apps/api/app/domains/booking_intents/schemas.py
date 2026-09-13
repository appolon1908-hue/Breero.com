import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.booking.schemas import BookingAnswerInput, CustomerInput

from .models import BookingIntentStatus


class BookingIntentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: uuid.UUID


class SlotSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_token: str = Field(min_length=16, max_length=512)
    start_local: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_local: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @model_validator(mode="after")
    def end_after_start(self) -> "SlotSelection":
        if time.fromisoformat(self.end_local) <= time.fromisoformat(self.start_local):
            raise ValueError("end_local must be after start_local")
        return self


class BookingIntentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: uuid.UUID | None = None
    address_id: uuid.UUID | None = None
    timezone_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        # Allows both multi-segment zones ("America/Los_Angeles") and the valid IANA
        # zones with no "/" at all ("UTC", "GMT+0", "EST5EDT"). ZoneInfo() itself is
        # the actual validity check (see BookingIntentService._timezone) — this is
        # only a shape pre-filter, so it must not reject real zone names.
        pattern=r"^[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+.-]+)*$",
    )
    requested_date: date | None = None
    selected_slot: SlotSelection | None = None
    clear_selected_slot: bool = False

    @model_validator(mode="after")
    def validate_patch(self) -> "BookingIntentUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one booking-intent field is required")
        if self.selected_slot is not None and self.clear_selected_slot:
            raise ValueError("selected_slot and clear_selected_slot cannot be combined")
        return self


class BookingIntentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_reference: str
    service_id: uuid.UUID
    address_id: uuid.UUID | None
    timezone_id: str | None
    requested_date: date | None
    selected_slot: SlotSelection | None
    status: BookingIntentStatus
    expires_at: datetime
    version: int
    booking_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class BookingIntentSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: CustomerInput
    answers: list[BookingAnswerInput] = Field(default_factory=list)
