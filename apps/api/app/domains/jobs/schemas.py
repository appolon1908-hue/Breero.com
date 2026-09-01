import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import JobStatus, WorkRequestStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JobRead(ORMModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID | None
    service_id: uuid.UUID
    status: JobStatus
    scheduled_start: datetime
    scheduled_end: datetime
    vendor_id: uuid.UUID | None
    worker_id: uuid.UUID | None
    diagnostic_notes: str | None
    completion_notes: str | None


class TransitionRequest(BaseModel):
    status: JobStatus
    reason: str | None = Field(default=None, max_length=1000)


class TechnicianNoteRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=10000)


class WorkLineItem(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(ge=1, le=1000)
    unit_price_minor: int = Field(ge=0)


class WorkRequestCreate(BaseModel):
    description: str = Field(min_length=1, max_length=5000)
    line_items: list[WorkLineItem] = Field(min_length=1, max_length=100)
    tax_minor: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class WorkRequestRead(ORMModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: WorkRequestStatus
    description: str
    line_items: list[WorkLineItem]
    subtotal_minor: int
    tax_minor: int
    total_minor: int
    currency: str
    created_at: datetime


class WorkRequestDecision(BaseModel):
    approve: bool
