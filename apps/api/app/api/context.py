"""Build the request-scoped facts every state-changing domain command needs."""

import uuid

from fastapi import Request

from app.domains.common.command_context import CommandContext

WEBHOOK_PRINCIPAL = "stripe-webhook"


def command_context(
    request: Request,
    *,
    principal_type: str = "user",
    actor_id: uuid.UUID | None = None,
    idempotency_key: str | None = None,
) -> CommandContext:
    """Assemble a CommandContext from the request the middleware has already tagged.

    ``request_id`` and ``correlation_id`` are set by the request-context middleware in
    ``app.main``; falling back to a fresh id keeps a directly-constructed test request
    from failing the CommandContext invariants.
    """
    fallback = str(uuid.uuid4())
    request_id = getattr(request.state, "request_id", None) or fallback
    return CommandContext(
        actor_id=actor_id,
        principal_type=principal_type,
        tenant_id=None,
        legal_entity_id=None,
        idempotency_key=idempotency_key,
        request_id=request_id,
        correlation_id=getattr(request.state, "correlation_id", None) or request_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
