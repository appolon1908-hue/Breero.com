import secrets
import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.booking.models import Address, Booking
from app.domains.booking.schemas import (
    AvailabilitySearchRequest,
    BookingAnswerInput,
    BookingCreateRequest,
    BookingWindow,
    CustomerInput,
)
from app.domains.booking.service import AvailabilityService, BookingService
from app.domains.catalog.models import Service
from app.domains.common.clock import Clock, SystemClock
from app.domains.common.outbox import AuditLog

from .models import BookingIntent, BookingIntentStatus
from .repository import BookingIntentRepository
from .schemas import BookingIntentCreate, BookingIntentUpdate, SlotSelection

BOOKING_INTENT_TTL = timedelta(minutes=120)
EDITABLE_STATUSES = frozenset(
    {
        BookingIntentStatus.DRAFT,
        BookingIntentStatus.ADDRESS_VALIDATED,
        BookingIntentStatus.COVERAGE_CONFIRMED,
        BookingIntentStatus.AVAILABILITY_FOUND,
    }
)


class BookingIntentService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Clock | None = None,
        ttl: timedelta = BOOKING_INTENT_TTL,
    ) -> None:
        self.session = session
        self.clock = clock or SystemClock()
        self.ttl = ttl
        self.repository = BookingIntentRepository(session)

    async def create(
        self,
        command: BookingIntentCreate,
        anonymous_session_id: uuid.UUID,
    ) -> BookingIntent:
        await self._active_service(command.service_id)
        now = self.clock.now()
        intent = BookingIntent(
            public_reference=self._reference(),
            anonymous_session_id=anonymous_session_id,
            service_id=command.service_id,
            status=BookingIntentStatus.DRAFT,
            expires_at=now + self.ttl,
            version=1,
        )
        await self.repository.add(intent)
        self._audit(
            intent,
            "booking_intent.create",
            {"service_id": str(intent.service_id)},
        )
        await self.session.commit()
        await self.session.refresh(intent)
        return intent

    async def get(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
    ) -> BookingIntent:
        # Locked: _reject_expired below can mutate and commit as a side effect of a
        # read, so two concurrent GETs on an already-expired intent must not both
        # try to apply that transition.
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        await self._reject_expired(intent)
        return intent

    async def update(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        command: BookingIntentUpdate,
        *,
        expected_version: int,
    ) -> BookingIntent:
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        await self._reject_expired(intent)
        self._require_version(intent, expected_version)
        if intent.status not in EDITABLE_STATUSES:
            raise DomainError(
                "BOOKING_INTENT_NOT_EDITABLE",
                "Booking intent cannot be changed in its current state.",
                409,
            )

        values = command.model_dump(exclude_unset=True, exclude={"clear_selected_slot"})
        if "service_id" in values:
            service_id = values["service_id"]
            if service_id is None:
                raise DomainError(
                    "SERVICE_REQUIRED",
                    "A service is required for the booking intent.",
                    422,
                )
            await self._active_service(service_id)
            if service_id != intent.service_id:
                intent.service_id = service_id
                intent.address_id = None
                intent.timezone_id = None
                intent.requested_date = None
                intent.selected_slot = None
                intent.status = BookingIntentStatus.DRAFT

        if "address_id" in values:
            address_id = values["address_id"]
            address: Address | None = None
            if address_id is not None:
                address = await self.session.get(Address, address_id)
                # Same error for "doesn't exist" and "belongs to someone else": an
                # anonymous session has no identity to own an address by, so any
                # address already linked to a registered customer must be rejected
                # here or it could be attached to an unrelated session's intent.
                # A distinct error would let a caller enumerate other customers'
                # address_ids by observing which ones return a different response.
                if address is None or address.customer_id is not None:
                    raise DomainError(
                        "ADDRESS_NOT_FOUND",
                        "Validated address was not found.",
                        422,
                    )
            if address_id != intent.address_id:
                intent.address_id = address_id
                intent.timezone_id = None
                intent.requested_date = None
                intent.selected_slot = None
            if address_id is None:
                intent.status = BookingIntentStatus.DRAFT
            elif address is not None and address.service_area_id is not None:
                intent.status = BookingIntentStatus.COVERAGE_CONFIRMED
            else:
                intent.status = BookingIntentStatus.ADDRESS_VALIDATED

        if "timezone_id" in values:
            timezone_id = values["timezone_id"]
            if timezone_id is not None:
                self._timezone(timezone_id)
            intent.timezone_id = timezone_id
            intent.selected_slot = None

        if "requested_date" in values:
            requested_date = values["requested_date"]
            if requested_date is not None:
                zone = self._timezone(intent.timezone_id) if intent.timezone_id else ZoneInfo("UTC")
                if requested_date < self.clock.now().astimezone(zone).date():
                    raise DomainError(
                        "REQUESTED_DATE_IN_PAST",
                        "Requested service date cannot be in the past.",
                        422,
                    )
            intent.requested_date = requested_date
            intent.selected_slot = None

        if command.clear_selected_slot:
            intent.selected_slot = None
            intent.status = await self._status_after_clearing_slot(intent)

        selected_slot = command.selected_slot
        if "selected_slot" in values:
            if selected_slot is None:
                # Explicit `"selected_slot": null` is distinct from omitting the
                # field and must clear the slot too, same as clear_selected_slot.
                intent.selected_slot = None
                intent.status = await self._status_after_clearing_slot(intent)
            else:
                if not intent.address_id or not intent.timezone_id or not intent.requested_date:
                    raise DomainError(
                        "BOOKING_INTENT_INCOMPLETE",
                        "Address, timezone and requested date are required before selecting a slot.",
                        422,
                    )
                service = await self._active_service(intent.service_id)
                if not service.is_bookable:
                    raise DomainError(
                        "SERVICE_NOT_BOOKABLE",
                        "This service currently supports requests only and cannot be booked.",
                        409,
                    )
                window = self._slot_window(intent, selected_slot)
                slots = await AvailabilityService(self.session).search(
                    AvailabilitySearchRequest(
                        service_id=intent.service_id,
                        address_id=intent.address_id,
                        date_from=intent.requested_date,
                        date_to=intent.requested_date,
                    )
                )
                if not any(
                    slot.start == window.start and slot.end == window.end for slot in slots
                ):
                    raise DomainError(
                        "SLOT_UNAVAILABLE",
                        "The selected time slot is no longer available.",
                        409,
                    )
                intent.selected_slot = selected_slot.model_dump()
                intent.status = BookingIntentStatus.AVAILABILITY_FOUND

        intent.version += 1
        self._audit(
            intent,
            "booking_intent.update",
            {"status": intent.status.value, "version": intent.version},
        )
        await self.session.commit()
        await self.session.refresh(intent)
        return intent

    async def abandon(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        *,
        expected_version: int,
    ) -> None:
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        self._require_version(intent, expected_version)
        if intent.status == BookingIntentStatus.SUBMITTED:
            raise DomainError(
                "BOOKING_INTENT_ALREADY_SUBMITTED",
                "Submitted booking intents cannot be abandoned.",
                409,
            )
        if intent.status != BookingIntentStatus.EXPIRED:
            intent.status = BookingIntentStatus.EXPIRED
            intent.selected_slot = None
            intent.version += 1
            self._audit(
                intent,
                "booking_intent.abandon",
                {"version": intent.version},
            )
            await self.session.commit()

    async def submit(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        customer: CustomerInput,
        answers: list[BookingAnswerInput],
        *,
        expected_version: int,
        idempotency_key: str,
    ) -> Booking:
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        await self._reject_expired(intent)
        self._require_version(intent, expected_version)
        if intent.status != BookingIntentStatus.AVAILABILITY_FOUND:
            raise DomainError(
                "BOOKING_INTENT_NOT_READY",
                "A validated address, date and slot are required before submitting.",
                409,
            )
        assert intent.address_id and intent.timezone_id and intent.requested_date
        selected_slot = SlotSelection.model_validate(intent.selected_slot)
        window = self._slot_window(intent, selected_slot)

        # Delegates to the same authoritative BookingService.create() the direct
        # /bookings endpoint uses, rather than re-deriving capacity/pricing/
        # eligibility logic here: it re-validates the slot is still free (the
        # intent could have gone stale since AVAILABILITY_FOUND was set), takes
        # the real capacity hold, and is idempotent on idempotency_key so a retry
        # after a failure between the two commits below is always safe.
        booking = await BookingService(self.session).create(
            BookingCreateRequest(
                service_id=intent.service_id,
                customer=customer,
                address_id=intent.address_id,
                window=window,
                answers=answers,
            ),
            idempotency_key,
        )

        intent.status = BookingIntentStatus.SUBMITTED
        intent.booking_id = booking.id
        intent.version += 1
        self._audit(
            intent,
            "booking_intent.submit",
            {"booking_id": str(booking.id), "version": intent.version},
        )
        await self.session.commit()
        await self.session.refresh(intent)
        return booking

    async def _active_service(self, service_id: uuid.UUID) -> Service:
        service = await self.session.get(Service, service_id)
        if not service or not service.is_active:
            raise DomainError("SERVICE_NOT_FOUND", "Service not found.", 404)
        return service

    async def _status_after_clearing_slot(self, intent: BookingIntent) -> BookingIntentStatus:
        if intent.address_id is None:
            return BookingIntentStatus.DRAFT
        address = await self.session.get(Address, intent.address_id)
        if address is not None and address.service_area_id is not None:
            return BookingIntentStatus.COVERAGE_CONFIRMED
        return BookingIntentStatus.ADDRESS_VALIDATED

    def _slot_window(self, intent: BookingIntent, selected_slot: SlotSelection) -> BookingWindow:
        zone = self._timezone(intent.timezone_id)
        assert intent.requested_date is not None
        start_local = datetime.combine(
            intent.requested_date, time.fromisoformat(selected_slot.start_local), tzinfo=zone
        )
        end_local = datetime.combine(
            intent.requested_date, time.fromisoformat(selected_slot.end_local), tzinfo=zone
        )
        return BookingWindow(start=start_local.astimezone(UTC), end=end_local.astimezone(UTC))

    async def _owned(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> BookingIntent:
        intent = await self.repository.owned(
            intent_id,
            anonymous_session_id,
            lock=lock,
        )
        if not intent:
            raise DomainError("BOOKING_INTENT_NOT_FOUND", "Booking intent not found.", 404)
        return intent

    async def _reject_expired(self, intent: BookingIntent) -> None:
        if (
            intent.status not in {BookingIntentStatus.EXPIRED, BookingIntentStatus.SUBMITTED}
            and intent.expires_at <= self.clock.now()
        ):
            intent.status = BookingIntentStatus.EXPIRED
            intent.selected_slot = None
            intent.version += 1
            self._audit(
                intent,
                "booking_intent.expire",
                {"version": intent.version},
            )
            await self.session.commit()
        if intent.status == BookingIntentStatus.EXPIRED:
            raise DomainError(
                "BOOKING_INTENT_EXPIRED",
                "Booking intent has expired.",
                410,
            )

    @staticmethod
    def _require_version(intent: BookingIntent, expected_version: int) -> None:
        if intent.version != expected_version:
            raise DomainError(
                "BOOKING_INTENT_VERSION_CONFLICT",
                "Booking intent was changed by another request.",
                409,
                fields={"current_version": intent.version},
            )

    @staticmethod
    def _timezone(timezone_id: str | None) -> ZoneInfo:
        if not timezone_id:
            raise DomainError(
                "TIMEZONE_REQUIRED",
                "Service-address timezone is required.",
                422,
            )
        try:
            return ZoneInfo(timezone_id)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(
                "TIMEZONE_INVALID",
                "Service-address timezone is invalid.",
                422,
            ) from exc

    @staticmethod
    def _reference() -> str:
        return "BI-" + secrets.token_hex(8).upper()

    def _audit(self, intent: BookingIntent, action: str, metadata: dict) -> None:
        self.session.add(
            AuditLog(
                actor_id=None,
                actor_type="anonymous_session",
                action=action,
                resource_type="booking_intent",
                resource_id=intent.id,
                metadata_json={
                    "public_reference": intent.public_reference,
                    "anonymous_session_id": str(intent.anonymous_session_id),
                    **metadata,
                },
                created_at=self.clock.now(),
            )
        )
