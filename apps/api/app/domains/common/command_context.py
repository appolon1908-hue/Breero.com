from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Request-scoped facts passed to every state-changing domain command."""

    actor_id: UUID | None
    principal_type: str

    tenant_id: UUID | None
    legal_entity_id: UUID | None

    idempotency_key: str | None

    request_id: str
    correlation_id: str

    ip_address: str | None
    user_agent: str | None

    def __post_init__(self) -> None:
        for field_name in ("principal_type", "request_id", "correlation_id"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("idempotency_key must be non-empty when supplied")
