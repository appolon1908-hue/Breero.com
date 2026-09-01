import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.booking.models import Booking, BookingStatus
from app.domains.common.command_context import CommandContext
from app.domains.common.domain_event import DomainEvent
from app.domains.common.money import Money
from app.domains.common.outbox import AuditLog, IntegrationEvent
from app.domains.common.outbox_service import to_integration_event
from app.domains.jobs.models import Job, JobEvent, JobStatus, WorkRequest, WorkRequestStatus
from app.domains.jobs.service import JobService
from app.integrations.stripe import PaymentProvider

from .exceptions import IdempotencyConflict, InvalidPaymentState, PaymentError, PaymentNotFound
from .models import (
    IdempotencyRecord,
    Payment,
    PaymentEvent,
    PaymentPurpose,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from .repository import PaymentRepository
from .schemas import PaymentIntentCreate, PaymentView, RefundView

STRIPE_STATUS = {
    "requires_payment_method": PaymentStatus.CREATED,
    "requires_confirmation": PaymentStatus.CREATED,
    "requires_action": PaymentStatus.REQUIRES_ACTION,
    "processing": PaymentStatus.AUTHORIZED,
    "requires_capture": PaymentStatus.AUTHORIZED,
    "succeeded": PaymentStatus.CAPTURED,
    "canceled": PaymentStatus.CANCELED,
}


class PaymentService:
    def __init__(self, session: AsyncSession, provider: PaymentProvider) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.provider = provider

    async def create_intent(
        self, payload: PaymentIntentCreate, context: CommandContext
    ) -> PaymentView:
        key = self._require_idempotency_key(context)
        if payload.payment_purpose == PaymentPurpose.PROFESSIONAL_LEAD:
            raise InvalidPaymentState("Professional lead payments must use the provider purchase endpoint")
        request = payload.model_dump(mode="json")
        request_hash = self._hash(request)
        await self.repo.lock_key("create_intent", key)
        existing = await self.repo.get_idempotency("create_intent", key)
        if existing:
            if existing.request_hash != request_hash:
                raise IdempotencyConflict("Idempotency key was already used with another request")
            if not existing.response_body:
                raise IdempotencyConflict("Request with this idempotency key is still processing")
            payment = await self.repo.get(uuid.UUID(existing.response_body["id"]))
            if payment is None:
                raise PaymentNotFound("Stored idempotent payment no longer exists")
            return self._view(payment)

        metadata = dict(payload.metadata)
        if payload.payment_purpose == PaymentPurpose.BOOKING_DIAGNOSTIC:
            if not payload.booking_id or payload.quote_id:
                raise InvalidPaymentState("Booking payments require only booking_id")
            booking = await self.session.scalar(
                select(Booking).where(Booking.id == payload.booking_id).with_for_update()
            )
            if not booking:
                raise PaymentNotFound("Booking not found")
            if Money.from_minor(payload.amount_minor, payload.currency) != Money(
                booking.total_amount, booking.currency
            ):
                raise InvalidPaymentState("Payment amount or currency does not match the booking")
            if booking.status != BookingStatus.PENDING_PAYMENT:
                raise InvalidPaymentState("Booking is not awaiting payment")
            metadata["booking_id"] = str(booking.id)
        else:
            if not payload.quote_id or payload.booking_id:
                raise InvalidPaymentState("Additional-work payments require only quote_id")
            quote = await self.session.scalar(
                select(WorkRequest).where(WorkRequest.id == payload.quote_id).with_for_update()
            )
            if not quote:
                raise PaymentNotFound("Quote not found")
            if quote.status != WorkRequestStatus.APPROVED_PENDING_PAYMENT:
                raise InvalidPaymentState("Quote is not awaiting payment")
            if Money.from_minor(payload.amount_minor, payload.currency) != Money.from_minor(
                quote.total_minor, quote.currency
            ):
                raise InvalidPaymentState("Payment amount or currency does not match the quote")
            metadata["quote_id"] = str(quote.id)

        record = IdempotencyRecord(
            operation="create_intent", idempotency_key=key, request_hash=request_hash
        )
        await self.repo.add_idempotency(record)
        provider_intent = await self.provider.create_intent(
            amount_minor=payload.amount_minor,
            currency=payload.currency,
            capture_method=payload.capture_method,
            metadata=metadata,
            idempotency_key=key,
        )
        payment = await self.repo.add(
            Payment(
                booking_id=payload.booking_id,
                quote_id=payload.quote_id,
                payment_purpose=payload.payment_purpose,
                provider_payment_id=provider_intent.id,
                provider="stripe",
                status=STRIPE_STATUS.get(provider_intent.status, PaymentStatus.CREATED),
                amount_minor=payload.amount_minor,
                currency=payload.currency,
                captured_amount_minor=provider_intent.amount_received,
                provider_client_secret=provider_intent.client_secret,
                metadata_=metadata,
            )
        )
        record.response_code = 201
        record.response_body = {"id": str(payment.id)}
        await self.session.commit()
        return self._view(payment)

    async def create_professional_lead_intent(
        self,
        *,
        lead_purchase_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        provider_id: uuid.UUID,
        lead_id: uuid.UUID,
        key: str,
    ) -> Payment:
        """Create the server-authoritative Stripe intent for a locked lead purchase."""
        existing = await self.session.scalar(
            select(Payment).where(Payment.lead_purchase_id == lead_purchase_id)
        )
        if existing:
            return existing
        provider_intent = await self.provider.create_intent(
            amount_minor=amount_minor,
            currency=currency,
            capture_method="automatic",
            metadata={
                "lead_purchase_id": str(lead_purchase_id),
                "lead_id": str(lead_id),
                "provider_id": str(provider_id),
                "purpose": PaymentPurpose.PROFESSIONAL_LEAD.value,
            },
            idempotency_key=f"professional-lead:{key}",
        )
        return await self.repo.add(
            Payment(
                lead_purchase_id=lead_purchase_id,
                payment_purpose=PaymentPurpose.PROFESSIONAL_LEAD,
                provider_payment_id=provider_intent.id,
                provider="stripe",
                status=STRIPE_STATUS.get(provider_intent.status, PaymentStatus.CREATED),
                amount_minor=amount_minor,
                currency=currency.upper(),
                captured_amount_minor=provider_intent.amount_received,
                provider_client_secret=provider_intent.client_secret,
                metadata_={
                    "lead_purchase_id": str(lead_purchase_id),
                    "lead_id": str(lead_id),
                    "provider_id": str(provider_id),
                },
            )
        )

    async def get(self, payment_id: uuid.UUID) -> PaymentView:
        payment = await self.repo.get(payment_id)
        if payment is None:
            raise PaymentNotFound("Payment not found")
        return self._view(payment)

    async def capture(
        self, payment_id: uuid.UUID, amount_minor: int | None, context: CommandContext
    ) -> PaymentView:
        key = self._require_idempotency_key(context)
        payment = await self.repo.get(payment_id, lock=True)
        if payment is None:
            raise PaymentNotFound("Payment not found")
        if payment.status == PaymentStatus.CAPTURED:
            return self._view(payment)
        if payment.status != PaymentStatus.AUTHORIZED or not payment.provider_payment_id:
            raise InvalidPaymentState("Only an authorized payment can be captured")
        if amount_minor is not None and amount_minor > payment.amount_minor:
            raise InvalidPaymentState("Capture amount exceeds authorized amount")
        intent = await self.provider.capture_intent(
            payment.provider_payment_id, amount_minor=amount_minor, idempotency_key=key
        )
        payment.status = STRIPE_STATUS.get(intent.status, payment.status)
        payment.captured_amount_minor = intent.amount_received
        if payment.status == PaymentStatus.CAPTURED:
            await self._settle(payment, context)
        await self.session.commit()
        return self._view(payment)

    async def process_webhook(
        self, body: bytes, signature: str, context: CommandContext
    ) -> tuple[str, bool]:
        event = self.provider.verify_webhook(body, signature)
        event_id, event_type = event["id"], event["type"]
        await self.repo.lock_key("stripe_event", event_id)
        recorded = await self.repo.get_event("stripe", event_id)
        if recorded and recorded.status == "processed":
            return event_id, True
        try:
            obj: dict[str, Any] = event.get("data", {}).get("object", {})
            provider_id = obj.get("id") if obj.get("object") == "payment_intent" else None
            payment = (
                await self.repo.get_by_provider_id(provider_id, lock=True) if provider_id else None
            )
            if payment:
                if event_type == "payment_intent.payment_failed":
                    payment.status = PaymentStatus.FAILED
                    payment.failure_code = obj.get("last_payment_error", {}).get("code")
                    await self._release_failed_lead_purchase(payment)
                elif event_type == "payment_intent.canceled":
                    payment.status = PaymentStatus.CANCELED
                    await self._release_failed_lead_purchase(payment)
                elif event_type.startswith("payment_intent."):
                    payment.status = STRIPE_STATUS.get(obj.get("status", ""), payment.status)
                    payment.captured_amount_minor = obj.get(
                        "amount_received", payment.captured_amount_minor
                    )
                    if payment.status == PaymentStatus.CAPTURED:
                        await self._settle(payment, context)
            elif obj.get("object") == "refund" and obj.get("id"):
                refund = await self.repo.refund_by_provider_id(obj["id"])
                if refund and obj.get("status") in {x.value for x in RefundStatus}:
                    refund.status = RefundStatus(obj["status"])
                    payment = await self.repo.get(refund.payment_id, lock=True)
                    if payment and refund.status == RefundStatus.SUCCEEDED:
                        refunded = int(
                            await self.session.scalar(
                                select(func.coalesce(func.sum(Refund.amount_minor), 0)).where(
                                    Refund.payment_id == payment.id,
                                    Refund.status == RefundStatus.SUCCEEDED,
                                )
                            )
                            or 0
                        )
                        payment.status = (
                            PaymentStatus.REFUNDED
                            if refunded >= payment.captured_amount_minor
                            else PaymentStatus.PARTIALLY_REFUNDED
                        )
                        if payment.payment_purpose == PaymentPurpose.PROFESSIONAL_LEAD:
                            await self._mark_lead_purchase_refunded(payment)
            if recorded:
                recorded.status = "processed"
                recorded.attempts += 1
                recorded.last_error = None
                recorded.processed_at = datetime.now(UTC)
                recorded.payment_id = payment.id if payment else None
                recorded.payload = event
            else:
                await self.repo.add_event(
                    provider="stripe",
                    event_id=event_id,
                    event_type=event_type,
                    payload=event,
                    payment_id=payment.id if payment else None,
                )
            await self.session.commit()
            return event_id, False
        except Exception as exc:
            await self.session.rollback()
            failed = await self.repo.get_event("stripe", event_id)
            if failed:
                failed.status = "failed"
                failed.attempts += 1
                failed.last_error = str(exc)[:2000]
            else:
                self.session.add(
                    PaymentEvent(
                        provider="stripe",
                        provider_event_id=event_id,
                        event_type=event_type,
                        payload=event,
                        status="failed",
                        attempts=1,
                        last_error=str(exc)[:2000],
                    )
                )
            await self.session.commit()
            if isinstance(exc, PaymentError):
                raise
            raise PaymentError("Webhook processing failed") from exc

    async def refund(
        self,
        payment_id: uuid.UUID,
        amount_minor: int | None,
        reason: str | None,
        context: CommandContext,
    ) -> RefundView:
        key = self._require_idempotency_key(context)
        actor_id = self._require_actor(context)
        payment = await self.repo.get(payment_id, lock=True)
        if not payment or not payment.provider_payment_id:
            raise PaymentNotFound("Payment not found")
        existing = await self.repo.refund_by_key(payment.id, key)
        if existing:
            return RefundView.model_validate(existing)
        if payment.status not in {PaymentStatus.CAPTURED, PaymentStatus.PARTIALLY_REFUNDED}:
            raise InvalidPaymentState("Only captured payments can be refunded")
        refunded = int(
            await self.session.scalar(
                select(func.coalesce(func.sum(Refund.amount_minor), 0)).where(
                    Refund.payment_id == payment.id,
                    Refund.status.in_([RefundStatus.PENDING, RefundStatus.SUCCEEDED]),
                )
            )
            or 0
        )
        remaining = payment.captured_amount_minor - refunded
        requested = amount_minor if amount_minor is not None else remaining
        if requested <= 0 or requested > remaining:
            raise InvalidPaymentState("Refund amount exceeds refundable balance")
        provider_refund = await self.provider.create_refund(
            payment.provider_payment_id, amount_minor=requested, idempotency_key=key
        )
        provider_status = (
            RefundStatus(provider_refund.status)
            if provider_refund.status in {x.value for x in RefundStatus}
            else RefundStatus.PENDING
        )
        refund = Refund(
            payment_id=payment.id,
            amount_minor=requested,
            status=provider_status,
            provider_refund_id=provider_refund.id,
            idempotency_key=key,
            reason=reason,
            created_by=actor_id,
        )
        self.session.add(refund)
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                action="refund.create",
                resource_type="payment",
                resource_id=payment.id,
                metadata_json={
                    "amount_minor": requested,
                    "currency": payment.currency,
                    "reason": reason,
                    "provider_refund_id": provider_refund.id,
                    "provider_status": provider_status.value,
                    **self._provenance(context),
                },
                created_at=datetime.now(UTC),
            )
        )
        if provider_status == RefundStatus.SUCCEEDED:
            payment.status = (
                PaymentStatus.REFUNDED
                if requested == remaining
                else PaymentStatus.PARTIALLY_REFUNDED
            )
            if payment.payment_purpose == PaymentPurpose.PROFESSIONAL_LEAD:
                await self._mark_lead_purchase_refunded(payment)
        self.session.add(
            self._event(
                context,
                "refund_created",
                "payment",
                payment.id,
                {
                    "payment_id": str(payment.id),
                    "refund_id": str(refund.id),
                    "amount_minor": requested,
                },
            )
        )
        await self.session.commit()
        await self.session.refresh(refund)
        return RefundView.model_validate(refund)

    async def _settle(self, payment: Payment, context: CommandContext) -> None:
        if payment.payment_purpose == PaymentPurpose.PROFESSIONAL_LEAD:
            from app.domains.professional_leads.models import (
                LeadPurchase,
                LeadPurchaseStatus,
                LeadStatus,
                ProfessionalLead,
            )

            purchase = await self.session.scalar(
                select(LeadPurchase)
                .where(LeadPurchase.id == payment.lead_purchase_id)
                .with_for_update()
            )
            if not purchase:
                raise PaymentNotFound("Payment references an unknown lead purchase")
            purchase.status = LeadPurchaseStatus.PAID
            lead = await self.session.get(ProfessionalLead, purchase.lead_id)
            if not lead or lead.status not in {LeadStatus.RESERVED, LeadStatus.PURCHASED}:
                raise InvalidPaymentState("Lead cannot be settled from its current state")
            lead.status = LeadStatus.PURCHASED
        elif payment.payment_purpose == PaymentPurpose.QUOTE_ADDITIONAL_WORK:
            quote = await self.session.scalar(
                select(WorkRequest).where(WorkRequest.id == payment.quote_id).with_for_update()
            )
            if not quote:
                raise PaymentNotFound("Payment references an unknown quote")
            if quote.status == WorkRequestStatus.APPROVED:
                return
            if quote.status != WorkRequestStatus.APPROVED_PENDING_PAYMENT:
                raise InvalidPaymentState("Quote cannot be settled from its current state")
            JobService.apply_work_request_transition(quote, WorkRequestStatus.APPROVED)
            quote.payment_id = payment.id
            job = await self.session.scalar(
                select(Job).where(Job.id == quote.job_id).with_for_update()
            )
            if job and job.status == JobStatus.AWAITING_APPROVAL:
                JobService(self.session).apply_transition(
                    job,
                    JobStatus.IN_PROGRESS,
                    None,
                    "system",
                    "additional_work_payment_captured",
                )
        else:
            await self._confirm_booking_and_create_job(payment, context)
        self.session.add(
            self._event(
                context,
                "payment_captured",
                "payment",
                payment.id,
                {"payment_id": str(payment.id), "purpose": payment.payment_purpose.value},
            )
        )

    async def _release_failed_lead_purchase(self, payment: Payment) -> None:
        if payment.payment_purpose != PaymentPurpose.PROFESSIONAL_LEAD:
            return
        from app.domains.professional_leads.models import (
            LeadPurchase,
            LeadPurchaseStatus,
            LeadStatus,
            ProfessionalLead,
        )

        purchase = await self.session.get(LeadPurchase, payment.lead_purchase_id)
        if not purchase:
            return
        purchase.status = LeadPurchaseStatus.FAILED
        lead = await self.session.get(ProfessionalLead, purchase.lead_id)
        if lead and lead.status == LeadStatus.RESERVED:
            lead.status = LeadStatus.AVAILABLE
            lead.purchased_by_vendor_id = None

    async def _mark_lead_purchase_refunded(self, payment: Payment) -> None:
        from app.domains.professional_leads.models import LeadPurchase, LeadPurchaseStatus

        purchase = await self.session.get(LeadPurchase, payment.lead_purchase_id)
        if purchase and payment.status == PaymentStatus.REFUNDED:
            purchase.status = LeadPurchaseStatus.REFUNDED

    async def _confirm_booking_and_create_job(
        self, payment: Payment, context: CommandContext
    ) -> None:
        booking = await self.session.scalar(
            select(Booking).where(Booking.id == payment.booking_id).with_for_update()
        )
        if not booking:
            raise PaymentNotFound("Payment references an unknown booking")
        if booking.status in {BookingStatus.PENDING_PROVIDER_CONFIRMATION, BookingStatus.CONFIRMED}:
            return
        if booking.status != BookingStatus.PENDING_PAYMENT:
            raise InvalidPaymentState("Booking cannot be confirmed from its current state")
        # Payment authorizes the evaluation fee; only explicit provider assignment confirms time.
        booking.status = BookingStatus.PENDING_PROVIDER_CONFIRMATION
        job = await self.session.scalar(select(Job).where(Job.booking_id == booking.id))
        if not job:
            job = Job(
                booking_id=booking.id,
                customer_id=booking.customer_id,
                service_id=booking.service_id,
                address_id=booking.address_id,
                status=JobStatus.CREATED,
                scheduled_start=booking.window_start,
                scheduled_end=booking.window_end,
                version=1,
            )
            self.session.add(job)
            await self.session.flush()
            self.session.add(
                JobEvent(
                    job_id=job.id,
                    from_status=None,
                    to_status=JobStatus.CREATED,
                    actor_id=None,
                    actor_type="system",
                    reason="payment_captured",
                )
            )
            self.session.add(
                self._event(
                    context,
                    "job.created",
                    "job",
                    job.id,
                    {"job_id": str(job.id), "booking_id": str(booking.id)},
                )
            )

    @staticmethod
    def _require_idempotency_key(context: CommandContext) -> str:
        if not context.idempotency_key:
            raise InvalidPaymentState("Idempotency-Key is required for this operation")
        return context.idempotency_key

    @staticmethod
    def _require_actor(context: CommandContext) -> uuid.UUID:
        """A refund is always attributable. ``Refund.created_by`` is NOT NULL, so an
        actor-less context has to fail here rather than as an integrity error."""
        if context.actor_id is None:
            raise InvalidPaymentState("This operation requires an authenticated actor")
        return context.actor_id

    @staticmethod
    def _provenance(context: CommandContext) -> dict[str, Any]:
        """Request provenance for the audit trail: who asked, under which request."""
        return {
            "principal_type": context.principal_type,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "ip_address": context.ip_address,
        }

    @staticmethod
    def _event(
        context: CommandContext,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> IntegrationEvent:
        return to_integration_event(
            DomainEvent(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                aggregate_version=1,
                occurred_at=datetime.now(UTC),
                correlation_id=context.correlation_id,
                payload=payload,
            )
        )

    @staticmethod
    def _hash(value: dict[str, Any]) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _view(payment: Payment) -> PaymentView:
        return PaymentView(
            id=payment.id,
            booking_id=payment.booking_id,
            quote_id=payment.quote_id,
            lead_purchase_id=payment.lead_purchase_id,
            payment_purpose=payment.payment_purpose,
            provider=payment.provider,
            status=payment.status,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            captured_amount_minor=payment.captured_amount_minor,
            client_secret=payment.provider_client_secret,
            failure_code=payment.failure_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
