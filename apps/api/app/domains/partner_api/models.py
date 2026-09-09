import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.common.models import TimestampMixin, UUIDPrimaryKeyMixin


class ApiScope(str, enum.Enum):
    """Least-privilege scopes. A key is granted the smallest set that works.

    Deliberately narrow and read-biased: the only write a third party can perform is
    submitting a service request, which enters manual dispatch and promises nothing.
    """

    CATALOG_READ = "catalog:read"
    COVERAGE_READ = "coverage:read"
    SERVICE_REQUEST_WRITE = "service_request:write"
    SERVICE_REQUEST_READ = "service_request:read"
    WEBHOOK_MANAGE = "webhook:manage"


class ApiClientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class ApiClient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A third-party integrator.

    Separate from `User` on purpose: an integrator is not a person, has no password,
    no session and no portal access, and must never be resolvable through the
    interactive auth paths.
    """

    __tablename__ = "api_clients"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[ApiClientStatus] = mapped_column(
        String(16), nullable=False, default=ApiClientStatus.ACTIVE, index=True
    )
    # Optional tenancy. When set, everything this client can see is confined to one
    # provider, so an integrator built for a single vendor cannot enumerate others.
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A credential belonging to an `ApiClient`.

    The secret is never stored. `key_hash` is a SHA-256 of the presented secret, and
    `prefix` is the short public identifier shown in listings and logs so a key can be
    named and revoked without anyone ever handling the secret again.
    """

    __tablename__ = "api_keys"
    __table_args__ = (UniqueConstraint("prefix", name="uq_api_keys_prefix"),)

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_clients.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scopes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Expiry is mandatory in practice: the service refuses to mint a key without one.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Per-key ceiling, so one noisy integrator cannot consume the shared budget.
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)


class WebhookSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Where a client wants events delivered.

    Deliveries are signed with a per-subscription secret, and that secret is stored
    because signing requires it -- unlike an API key, which only ever needs comparing.
    """

    __tablename__ = "webhook_subscriptions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_clients.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    event_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    disabled_reason: Mapped[str | None] = mapped_column(String(200))
