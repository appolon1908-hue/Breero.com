"""Third-party API client, key and webhook management.

The security posture here is deliberately narrow. A third-party credential is not a
user session: it has no password, no refresh, no portal access, and cannot be resolved
through any interactive auth path. It carries an explicit scope set, a mandatory
expiry, a per-key rate ceiling, and an optional single-vendor confinement.
"""

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domains.common.domain_event import DomainEvent
from app.domains.common.outbox import AuditLog
from app.domains.common.outbox_service import to_integration_event

from .models import ApiClient, ApiClientStatus, ApiKey, ApiScope, WebhookSubscription
from .repository import PartnerApiRepository
from .schemas import (
    ApiClientCreate,
    ApiKeyCreate,
    ApiKeyIssued,
    WebhookSubscriptionCreate,
    WebhookSubscriptionIssued,
)

# A recognisable, greppable prefix. If one leaks into a log or a paste, it is obvious
# what it is and which environment it belongs to.
KEY_PREFIX = "brk"
SECRET_BYTES = 32
WEBHOOK_EVENT_TYPES = frozenset(
    {
        "service_request.received",
        "service_request.dispatched",
        "service_request.completed",
        "service_request.cancelled",
    }
)


class PartnerApiDisabled(HTTPException):
    def __init__(self) -> None:
        super().__init__(503, "The third-party API is not enabled in this environment")


def require_partner_api_enabled() -> None:
    """Fail closed. The capability is off by default and off in this release."""
    if not settings.third_party_api_enabled:
        raise PartnerApiDisabled()


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def sign_payload(secret: str, body: bytes, timestamp: str) -> str:
    """Signature a receiver recomputes to authenticate a delivery.

    The timestamp is inside the signed material, so a captured delivery cannot be
    replayed later against a receiver that enforces a freshness window.
    """
    message = timestamp.encode() + b"." + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


class PartnerApiService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PartnerApiRepository(session)

    # -- clients -------------------------------------------------------------

    async def create_client(self, data: ApiClientCreate, actor_id: uuid.UUID) -> ApiClient:
        client = await self.repo.add_client(
            ApiClient(
                name=data.name.strip(),
                contact_email=str(data.contact_email).lower(),
                vendor_id=data.vendor_id,
                status=ApiClientStatus.ACTIVE,
                created_by=actor_id,
            )
        )
        self._audit(actor_id, "partner_api.client.create", client.id, {"name": client.name})
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def set_client_status(
        self, client_id: uuid.UUID, status: ApiClientStatus, actor_id: uuid.UUID
    ) -> ApiClient:
        client = await self.repo.get_client(client_id)
        if not client:
            raise HTTPException(404, "API client not found")
        client.status = status
        self._audit(
            actor_id, "partner_api.client.status", client.id, {"status": status.value}
        )
        await self.session.commit()
        await self.session.refresh(client)
        return client

    # -- keys ----------------------------------------------------------------

    async def issue_key(
        self, client_id: uuid.UUID, data: ApiKeyCreate, actor_id: uuid.UUID
    ) -> ApiKeyIssued:
        client = await self.repo.get_client(client_id)
        if not client:
            raise HTTPException(404, "API client not found")
        if client.status is not ApiClientStatus.ACTIVE:
            raise HTTPException(409, "Keys can only be issued for an active client")

        secret_part = secrets.token_urlsafe(SECRET_BYTES)
        prefix = f"{KEY_PREFIX}_{secrets.token_hex(4)}"
        secret = f"{prefix}.{secret_part}"

        key = await self.repo.add_key(
            ApiKey(
                client_id=client.id,
                label=data.label.strip(),
                prefix=prefix,
                key_hash=hash_secret(secret),
                scopes=[scope.value for scope in data.scopes],
                expires_at=datetime.now(UTC) + timedelta(days=data.expires_in_days),
                rate_limit_per_minute=data.rate_limit_per_minute,
            )
        )
        # The scope set is audited, not the secret. An audit row must never be a place
        # a credential can be recovered from.
        self._audit(
            actor_id,
            "partner_api.key.issue",
            key.id,
            {"client_id": str(client.id), "prefix": prefix, "scopes": key.scopes},
        )
        await self.session.commit()
        await self.session.refresh(key)
        return ApiKeyIssued(
            **{field: getattr(key, field) for field in ApiKeyIssued.model_fields if field != "secret"},
            secret=secret,
        )

    async def revoke_key(self, key_id: uuid.UUID, actor_id: uuid.UUID) -> ApiKey:
        key = await self.repo.get_key(key_id)
        if not key:
            raise HTTPException(404, "API key not found")
        if key.revoked_at is None:
            key.revoked_at = datetime.now(UTC)
        self._audit(actor_id, "partner_api.key.revoke", key.id, {"prefix": key.prefix})
        await self.session.commit()
        await self.session.refresh(key)
        return key

    async def authenticate(self, presented: str) -> tuple[ApiClient, ApiKey]:
        """Resolve a presented secret to its client, or refuse.

        Every rejection returns the same message. A caller must not be able to tell an
        unknown key from a revoked, expired or suspended one, because that difference
        is a probing oracle.
        """
        rejection = HTTPException(401, "Invalid API credentials")
        if not presented or "." not in presented:
            raise rejection

        key = await self.repo.key_by_hash(hash_secret(presented))
        if key is None:
            raise rejection
        # Constant-time even though the lookup already matched: the digest comparison
        # is what actually authenticates, and it should not be timing-variable.
        if not hmac.compare_digest(key.key_hash, hash_secret(presented)):
            raise rejection
        if key.revoked_at is not None:
            raise rejection
        if key.expires_at <= datetime.now(UTC):
            raise rejection

        client = await self.repo.active_client_for_key(key)
        if client is None:
            raise rejection

        await self.repo.touch_key(key)
        return client, key

    @staticmethod
    def require_scope(key: ApiKey, scope: ApiScope) -> None:
        if scope.value not in (key.scopes or []):
            # 403, not 401: the credential is valid, the grant is not. Retrying with
            # the same key will never help, and the message says so.
            raise HTTPException(403, f"This API key does not hold the {scope.value} scope")

    @staticmethod
    def submission_key(client_id: uuid.UUID, idempotency_key: str) -> str:
        """Namespace an integrator's idempotency key by its client.

        Two integrators must not be able to collide on the same key, and one must not
        be able to replay another's submission by guessing it.
        """
        return f"partner:{client_id}:{idempotency_key}"

    async def owned_submission(self, request_id: uuid.UUID, client_id: uuid.UUID):
        """Fetch a submission only if this client made it.

        Ownership is carried by the namespaced idempotency key rather than a new
        column: the prefix is already unforgeable, because the server builds it from
        the authenticated client rather than from anything the caller sends.
        """
        from app.domains.public_submissions.models import PublicSubmission

        submission = await self.session.get(PublicSubmission, request_id)
        if submission is None:
            return None
        if not submission.idempotency_key.startswith(f"partner:{client_id}:"):
            return None
        return submission

    # -- webhooks ------------------------------------------------------------

    async def create_subscription(
        self, client_id: uuid.UUID, data: WebhookSubscriptionCreate
    ) -> WebhookSubscriptionIssued:
        unknown = sorted(set(data.event_types) - WEBHOOK_EVENT_TYPES)
        if unknown:
            raise HTTPException(400, f"Unknown event types: {', '.join(unknown)}")

        subscription = await self.repo.add_subscription(
            WebhookSubscription(
                client_id=client_id,
                url=str(data.url),
                event_types=sorted(set(data.event_types)),
                secret=secrets.token_urlsafe(SECRET_BYTES),
                active=True,
            )
        )
        await self.session.commit()
        await self.session.refresh(subscription)
        return WebhookSubscriptionIssued.model_validate(subscription)

    async def enqueue_event(self, event_type: str, aggregate_id: uuid.UUID, payload: dict) -> int:
        """Queue a webhook delivery per subscriber, through the existing outbox.

        Delivery is not attempted inline. The outbox already owns leasing, retry with
        backoff, terminal classification and operator retry, and a third-party endpoint
        is exactly the kind of dependency that should never be able to slow down or
        fail the request that produced the event.
        """
        subscriptions = await self.repo.active_subscriptions_for(event_type)
        for subscription in subscriptions:
            self.session.add(
                to_integration_event(
                    DomainEvent(
                        event_type=f"webhook.{event_type}",
                        aggregate_type="webhook_subscription",
                        aggregate_id=subscription.id,
                        aggregate_version=1,
                        occurred_at=datetime.now(UTC),
                        correlation_id=str(aggregate_id),
                        payload={
                            "subscription_id": str(subscription.id),
                            "event_type": event_type,
                            "data": payload,
                        },
                    )
                )
            )
        return len(subscriptions)

    @staticmethod
    def delivery_headers(secret: str, payload: dict, *, now: datetime | None = None) -> dict[str, str]:
        moment = now or datetime.now(UTC)
        timestamp = str(int(moment.timestamp()))
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return {
            "Content-Type": "application/json",
            "X-Breero-Timestamp": timestamp,
            "X-Breero-Signature": f"sha256={sign_payload(secret, body, timestamp)}",
        }

    # -- shared --------------------------------------------------------------

    def _audit(
        self, actor_id: uuid.UUID | None, action: str, resource_id: uuid.UUID, metadata: dict
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                actor_type="user",
                action=action,
                resource_type="partner_api",
                resource_id=resource_id,
                metadata_json=metadata,
                created_at=datetime.now(UTC),
            )
        )
