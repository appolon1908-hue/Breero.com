import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.booking.models import Booking, BookingStatus
from app.domains.common.command_context import CommandContext
from app.domains.common.outbox import AuditLog, IntegrationEvent
from app.domains.jobs.models import WorkRequest, WorkRequestStatus
from app.domains.payments.exceptions import IdempotencyConflict, InvalidPaymentState
from app.domains.payments.models import (
    IdempotencyRecord,
    Payment,
    PaymentEvent,
    PaymentPurpose,
    PaymentStatus,
    RefundStatus,
)
from app.domains.payments.schemas import PaymentIntentCreate, ProviderIntent, ProviderRefund
from app.domains.payments.service import PaymentService


def _context(key: str | None = None, actor_id: uuid.UUID | None = None) -> CommandContext:
    """The request-scoped facts the HTTP layer hands to every payment command."""
    return CommandContext(
        actor_id=actor_id,
        principal_type="user",
        tenant_id=None,
        legal_entity_id=None,
        idempotency_key=key,
        request_id="req-test-1",
        correlation_id="corr-test-1",
        ip_address="203.0.113.10",
        user_agent="pytest",
    )


@pytest.fixture
def service() -> PaymentService:
    session = AsyncMock()
    session.add = MagicMock()
    provider = MagicMock()
    provider.create_intent = AsyncMock()
    provider.capture_intent = AsyncMock()
    result = PaymentService(session, provider)
    result.repo = AsyncMock()
    result.repo.get_event.return_value = None
    return result


@pytest.mark.asyncio
async def test_create_intent_persists_provider_result(service: PaymentService) -> None:
    booking_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    service.provider.create_intent.return_value = ProviderIntent(
        id="pi_123", status="requires_capture", client_secret="secret"
    )

    async def add(payment: Payment) -> Payment:
        payment.id = payment_id
        payment.created_at = payment.updated_at = datetime.now(UTC)
        return payment

    service.repo.add.side_effect = add
    service.repo.get_idempotency.return_value = None
    service.session.scalar.return_value = Booking(
        id=booking_id,
        total_amount=129,
        currency="USD",
        status=BookingStatus.PENDING_PAYMENT,
    )
    result = await service.create_intent(
        PaymentIntentCreate(booking_id=booking_id, amount_minor=12900), _context("request-key-123")
    )

    assert result.id == payment_id
    assert result.status == PaymentStatus.AUTHORIZED
    service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_idempotency_key_rejects_different_payload(service: PaymentService) -> None:
    service.repo.get_idempotency.return_value = IdempotencyRecord(
        operation="create_intent",
        idempotency_key="request-key-123",
        request_hash="different",
    )
    with pytest.raises(IdempotencyConflict):
        await service.create_intent(
            PaymentIntentCreate(booking_id=uuid.uuid4(), amount_minor=1000), _context("request-key-123")
        )


@pytest.mark.asyncio
async def test_capture_requires_authorization(service: PaymentService) -> None:
    service.repo.get.return_value = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        amount_minor=1000,
        currency="usd",
        status=PaymentStatus.CREATED,
    )
    with pytest.raises(InvalidPaymentState):
        await service.capture(service.repo.get.return_value.id, None, _context("capture-key-123"))


@pytest.mark.asyncio
async def test_duplicate_webhook_is_noop(service: PaymentService) -> None:
    service.provider.verify_webhook.return_value = {
        "id": "evt_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {}},
    }
    service.repo.get_event.return_value = PaymentEvent(
        provider="stripe",
        provider_event_id="evt_123",
        event_type="payment_intent.succeeded",
        payload={},
        status="processed",
    )

    assert await service.process_webhook(b"{}", "signature", _context()) == ("evt_123", True)
    service.repo.add_event.assert_not_awaited()
    service.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_payment_webhook_records_failure(service: PaymentService) -> None:
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        provider_payment_id="pi_failed",
        payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
        amount_minor=1000,
        captured_amount_minor=0,
        currency="usd",
        status=PaymentStatus.CREATED,
    )
    service.provider.verify_webhook.return_value = {
        "id": "evt_failed",
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "object": "payment_intent",
                "id": "pi_failed",
                "last_payment_error": {"code": "card_declined"},
            }
        },
    }
    service.repo.get_by_provider_id.return_value = payment

    event_id, duplicate = await service.process_webhook(b"{}", "signature", _context())

    assert (event_id, duplicate) == ("evt_failed", False)
    assert payment.status == PaymentStatus.FAILED
    assert payment.failure_code == "card_declined"


@pytest.mark.asyncio
async def test_webhook_settlement_failure_rolls_back_then_records_failed_event(
    service: PaymentService,
) -> None:
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        provider_payment_id="pi_rollback",
        payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
        amount_minor=1000,
        captured_amount_minor=0,
        currency="usd",
        status=PaymentStatus.CREATED,
    )
    service.provider.verify_webhook.return_value = {
        "id": "evt_rollback",
        "type": "payment_intent.succeeded",
        "data": {"object": {"object": "payment_intent", "id": "pi_rollback", "status": "succeeded", "amount_received": 1000}},
    }
    service.repo.get_by_provider_id.return_value = payment
    service.repo.get_event.side_effect = [None, None]
    service._settle = AsyncMock(side_effect=RuntimeError("forced settlement failure"))

    with pytest.raises(Exception, match="Webhook processing failed"):
        await service.process_webhook(b"{}", "signature", _context())

    service.session.rollback.assert_awaited_once()
    assert any(
        isinstance(call.args[0], PaymentEvent)
        and call.args[0].provider_event_id == "evt_rollback"
        and call.args[0].status == "failed"
        for call in service.session.add.call_args_list
    )


@pytest.mark.asyncio
async def test_quote_intent_requires_customer_approval(service: PaymentService) -> None:
    quote_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    service.repo.get_idempotency.return_value = None
    service.provider.create_intent.return_value = ProviderIntent(
        id="pi_quote", status="requires_action", client_secret="secret"
    )
    service.session.scalar.return_value = WorkRequest(
        id=quote_id,
        job_id=uuid.uuid4(),
        status=WorkRequestStatus.APPROVED_PENDING_PAYMENT,
        total_minor=2050,
        currency="USD",
    )

    async def add(payment: Payment) -> Payment:
        payment.id = payment_id
        payment.created_at = payment.updated_at = datetime.now(UTC)
        return payment

    service.repo.add.side_effect = add
    result = await service.create_intent(
        PaymentIntentCreate(
            quote_id=quote_id,
            payment_purpose=PaymentPurpose.QUOTE_ADDITIONAL_WORK,
            amount_minor=2050,
            currency="usd",
        ),
        _context("quote-payment-key"),
    )
    assert result.payment_purpose == PaymentPurpose.QUOTE_ADDITIONAL_WORK
    assert result.quote_id == quote_id


@pytest.mark.asyncio
async def test_partial_refund_updates_payment(service: PaymentService) -> None:
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        provider_payment_id="pi_123",
        payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
        amount_minor=1000,
        captured_amount_minor=1000,
        currency="usd",
        status=PaymentStatus.CAPTURED,
    )
    service.repo.get.return_value = payment
    service.repo.refund_by_key.return_value = None
    service.session.scalar.return_value = 0
    service.provider.create_refund = AsyncMock(
        return_value=ProviderRefund(id="re_123", status="succeeded")
    )

    async def refresh(refund) -> None:
        refund.id = uuid.uuid4()
        refund.created_at = datetime.now(UTC)

    service.session.refresh.side_effect = refresh
    actor_id = uuid.uuid4()
    result = await service.refund(
        payment.id, 400, None, _context("refund-key-123", actor_id=actor_id)
    )
    assert result.amount_minor == 400
    assert result.status == RefundStatus.SUCCEEDED
    assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
    assert any(
        isinstance(call.args[0], AuditLog) and call.args[0].action == "refund.create"
        for call in service.session.add.call_args_list
    )


@pytest.mark.asyncio
async def test_refund_records_request_provenance_and_correlation(
    service: PaymentService,
) -> None:
    """The command context must reach both the audit trail and the outbox.

    Before CommandContext was threaded through, a refund's audit row recorded the
    actor but nothing about the request, and the emitted integration event carried no
    correlation id -- so a delivered event could not be tied back to the call.
    """
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        provider_payment_id="pi_456",
        payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
        amount_minor=1000,
        captured_amount_minor=1000,
        currency="usd",
        status=PaymentStatus.CAPTURED,
    )
    service.repo.get.return_value = payment
    service.repo.refund_by_key.return_value = None
    service.session.scalar.return_value = 0
    service.provider.create_refund = AsyncMock(
        return_value=ProviderRefund(id="re_456", status="succeeded")
    )

    async def refresh(refund) -> None:
        refund.id = uuid.uuid4()
        refund.created_at = datetime.now(UTC)

    service.session.refresh.side_effect = refresh
    actor_id = uuid.uuid4()
    await service.refund(
        payment.id, 400, "duplicate charge", _context("refund-key-456", actor_id=actor_id)
    )

    added = [call.args[0] for call in service.session.add.call_args_list]
    audit = next(item for item in added if isinstance(item, AuditLog))
    assert audit.metadata_json["request_id"] == "req-test-1"
    assert audit.metadata_json["correlation_id"] == "corr-test-1"
    assert audit.metadata_json["ip_address"] == "203.0.113.10"
    assert audit.metadata_json["principal_type"] == "user"
    assert audit.actor_id == actor_id

    event = next(item for item in added if isinstance(item, IntegrationEvent))
    assert event.event_type == "refund_created"
    assert event.payload["correlation_id"] == "corr-test-1"


@pytest.mark.asyncio
async def test_commands_require_an_idempotency_key(service: PaymentService) -> None:
    with pytest.raises(InvalidPaymentState, match="Idempotency-Key is required"):
        await service.create_intent(
            PaymentIntentCreate(booking_id=uuid.uuid4(), amount_minor=1000), _context()
        )


@pytest.mark.asyncio
async def test_refund_requires_an_authenticated_actor(service: PaymentService) -> None:
    # Refund.created_by is NOT NULL; an actor-less context must fail as a domain
    # error rather than reaching the database.
    with pytest.raises(InvalidPaymentState, match="requires an authenticated actor"):
        await service.refund(uuid.uuid4(), 400, None, _context("refund-key-789"))
