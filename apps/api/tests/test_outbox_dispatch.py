from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.domains.public_submissions.models import DownstreamStatus
from app.workers.tasks import UnhandledOutboxEvent, deliver_outbox_event


@pytest.mark.parametrize("event_type", ["job.completed", "payout.submitted", "unknown.private@example.invalid"])
async def test_unhandled_events_never_call_a_transport(event_type):
    event = SimpleNamespace(event_type=event_type, payload={"secret": "private-payload"})
    session, middleware, email = Mock(), AsyncMock(), AsyncMock()
    with pytest.raises(UnhandledOutboxEvent) as error:
        await deliver_outbox_event(event, session, middleware, email)
    assert error.value.code == "UNHANDLED_EVENT_TYPE"
    assert error.value.terminal is True
    assert event_type not in str(error.value)
    assert "private-payload" not in str(error.value)
    assert session.mock_calls == middleware.mock_calls == email.mock_calls == []


@pytest.mark.parametrize("event_type", [
    "email_verification_requested", "password_reset_requested", "password_changed",
    "payment_captured", "refund_created",
])
async def test_existing_notification_dispatch_is_preserved(event_type):
    event = SimpleNamespace(event_type=event_type, payload={"fixture": True})
    session, middleware, email = Mock(), AsyncMock(), AsyncMock()
    assert await deliver_outbox_event(event, session, middleware, email) is None
    email.send.assert_awaited_once_with(event_type, event.payload)
    assert session.mock_calls == middleware.mock_calls == []


async def test_middleware_ack_and_submission_state_are_preserved():
    event = SimpleNamespace(event_type="breero.service_request.created",
                            aggregate_type="public_submission", aggregate_id="fixture")
    submission = SimpleNamespace(downstream_status=DownstreamStatus.PENDING)
    session, middleware, email = AsyncMock(), AsyncMock(), AsyncMock()
    session.get.return_value = submission
    ack = object()
    middleware.deliver.return_value = ack
    assert await deliver_outbox_event(event, session, middleware, email) is ack
    assert submission.downstream_status == DownstreamStatus.DELIVERED
    middleware.deliver.assert_awaited_once_with(event)
    assert email.mock_calls == []
