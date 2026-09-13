from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domains.common.clock import require_aware


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    aggregate_version: int
    occurred_at: datetime
    correlation_id: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type.strip() or not self.aggregate_type.strip():
            raise ValueError("event and aggregate types must not be empty")
        if self.aggregate_version < 1:
            raise ValueError("aggregate_version must be positive")
        require_aware(self.occurred_at)
        if not self.correlation_id.strip():
            raise ValueError("correlation_id must not be empty")
