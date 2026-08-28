import enum
import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.common.models import TimestampMixin, UUIDPrimaryKeyMixin


class BookingIntentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ADDRESS_VALIDATED = "ADDRESS_VALIDATED"
    COVERAGE_CONFIRMED = "COVERAGE_CONFIRMED"
    AVAILABILITY_FOUND = "AVAILABILITY_FOUND"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"


class BookingIntent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "booking_intents"
    __table_args__ = (
        CheckConstraint("version > 0", name="booking_intent_positive_version"),
        CheckConstraint("expires_at > created_at", name="booking_intent_expiry_after_creation"),
    )

    public_reference: Mapped[str] = mapped_column(String(24), unique=True)
    anonymous_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"), index=True
    )
    timezone_id: Mapped[str | None] = mapped_column(String(64))
    requested_date: Mapped[date | None] = mapped_column(Date)
    selected_slot: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[BookingIntentStatus] = mapped_column(
        Enum(BookingIntentStatus, name="booking_intent_status", native_enum=True),
        nullable=False,
        default=BookingIntentStatus.DRAFT,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), index=True
    )
