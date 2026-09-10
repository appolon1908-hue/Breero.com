from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domains.common.clock import SystemClock, require_aware
from app.domains.common.command_context import CommandContext
from app.domains.common.domain_event import DomainEvent
from app.domains.common.money import Money
from app.domains.common.pagination import PageRequest
from app.domains.common.state_machine import InvalidStateTransition, StateMachine


def test_command_context_is_immutable_and_requires_trace_identifiers() -> None:
    context = CommandContext(
        actor_id=uuid4(),
        principal_type="human",
        tenant_id=None,
        legal_entity_id=None,
        idempotency_key="submit-1",
        request_id="request-1",
        correlation_id="correlation-1",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    with pytest.raises(FrozenInstanceError):
        context.request_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="correlation_id"):
        CommandContext(
            actor_id=None,
            principal_type="anonymous",
            tenant_id=None,
            legal_entity_id=None,
            idempotency_key=None,
            request_id="request-2",
            correlation_id=" ",
            ip_address=None,
            user_agent=None,
        )


def test_state_machine_rejects_undeclared_transition() -> None:
    machine = StateMachine({"DRAFT": frozenset({"SUBMITTED"}), "SUBMITTED": frozenset()})

    machine.require_transition("DRAFT", "SUBMITTED")
    with pytest.raises(InvalidStateTransition):
        machine.require_transition("SUBMITTED", "DRAFT")


def test_domain_event_requires_aware_time_and_correlation() -> None:
    event = DomainEvent(
        event_type="marketplace.request.submitted",
        aggregate_type="project_request",
        aggregate_id=uuid4(),
        aggregate_version=1,
        occurred_at=SystemClock().now(),
        correlation_id="correlation-1",
    )

    assert event.occurred_at.tzinfo is UTC
    with pytest.raises(ValueError, match="timezone-aware"):
        require_aware(datetime.now())


def test_money_and_pagination_validate_boundary_values() -> None:
    assert Money(Decimal("12.50"), "usd").currency == "USD"
    assert PageRequest(limit=200).limit == 200

    with pytest.raises(ValueError, match="currency"):
        Money(Decimal("12.50"), "US")
    with pytest.raises(ValueError, match="limit"):
        PageRequest(limit=0)
