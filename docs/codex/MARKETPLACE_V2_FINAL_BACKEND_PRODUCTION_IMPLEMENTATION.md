# BREERO Marketplace V2 — Final Backend Production Implementation

**Repository:** existing `appolon1908-hue/Breero.com` monorepo
**Backend application:** `apps/api`
**Implementation principle:** domain-first modular monolith
**Database:** existing PostgreSQL/PostGIS database and naming conventions
**Current safety foundation:** PR #35
**First implementation branch:** `be/marketplace-v2-p0-api-foundation`

---

## 1. Architectural rule

BREERO is a domain application exposed through HTTP.

The dependency direction is:

```text
FastAPI Router
      ↓
Application Command
      ↓
Domain Service
      ↓
Policies + State Machine
      ↓
Repository / Query
      ↓
SQLAlchemy
      ↓
PostgreSQL/PostGIS

```

A router may:

- parse HTTP input;
- resolve Principal;
- resolve command context;
- call a domain service;
- map domain result to response DTO.

A router must not contain:

- marketplace state transitions;
- matching logic;
- provider eligibility;
- credential rules;
- financial rules;
- direct third-party calls;
- tenant ownership logic;
- outbox delivery;
- database transaction orchestration beyond dependency injection.

---

## 2. Canonical marketplace lifecycle

```text
Customer Intent
      ↓
ProjectRequest
      ↓
Qualification
      ↓
Fulfillment Decision
      ↓
Matching
      ↓
Opportunity
      ↓
LeadConnection
      ↓
Conversation + Quote
      ↓
Scheduling
      ↓
Booking
      ↓
Job
      ↓
Completion
      ↓
Verified Review

```

Definitions:

```text
ProjectRequest = customer demand
Matching       = provider eligibility + ranking
Opportunity    = controlled provider invitation
LeadConnection = authorized customer/provider relationship
Quote          = commercial proposal
Booking        = scheduling outcome
Job            = field execution
Review         = completed-job trust signal

```

---

## 3. Backend branch sequence

P0 shared foundation:

```text
be/marketplace-v2-p0-api-foundation
be/marketplace-v2-p0-database
be/marketplace-v2-p0-authentication
be/marketplace-v2-p0-authorization
be/marketplace-v2-p0-capabilities-idempotency
be/marketplace-v2-p0-integration-reliability
be/marketplace-v2-p0-storage-uploads
be/marketplace-v2-p0-operations-foundation

```

Marketplace domains:

```text
be/marketplace-v2-catalog
be/marketplace-v2-project-requests

be/marketplace-v2-provider-core
be/marketplace-v2-provider-onboarding
be/marketplace-v2-provider-trust
be/marketplace-v2-provider-availability

be/marketplace-v2-matching
be/marketplace-v2-opportunities

be/marketplace-v2-quotes
be/marketplace-v2-messaging

be/marketplace-v2-booking-job
be/marketplace-v2-reviews

be/marketplace-v2-notifications
be/marketplace-v2-disputes

be/marketplace-v2-ops
be/marketplace-v2-admin

be/marketplace-v2-analytics
be/marketplace-v2-third-party-adapters

```

Later gated domains:

```text
be/marketplace-v2-payments
be/marketplace-v2-payouts
be/marketplace-v2-subscriptions

```

One PR per workstream.

Never recreate a 100+ commit integration PR.

---

# 4. Shared domain infrastructure

Add/normalize under the existing domain/common architecture:

```text
apps/api/app/domains/common/

commands.py
command_context.py

domain_event.py
state_machine.py

idempotency_service.py
audit_service.py

outbox_service.py
inbox_service.py

exception_service.py

pagination.py
money.py
clock.py

```

Authorization:

```text
apps/api/app/domains/authorization/

principal.py
permissions.py
policies.py
dependencies.py

```

Capabilities:

```text
apps/api/app/domains/capabilities/

service.py
registry.py
dependencies.py
schemas.py

```

Do not duplicate the capability implementation already created by PR #35.

---

# 5. Command context

Every important mutation receives:

```python
@dataclass(frozen=True)
class CommandContext:
    actor_id: UUID | None
    principal_type: str

    tenant_id: UUID | None
    legal_entity_id: UUID | None

    idempotency_key: str | None

    request_id: str
    correlation_id: str

    ip_address: str | None
    user_agent: str | None

```

All domain audit/outbox records inherit the correlation ID.

---

# 6. Production authentication

Production authentication authority:

```text
Keycloak / OIDC

```

Human users:

```text
Authorization Code + PKCE

```

Machine identities:

```text
Client Credentials

```

Validate:

```text
signature
issuer
audience
authorized party where applicable
subject
expiration
not-before
issued-at
token algorithm
key id

```

JWKS:

```text
cache keys
support rotation
refresh once on unknown kid
reject after failed refresh

```

---

# 7. External identity binding

Identity is:

```text
OIDC issuer + subject

```

Never email.

Add an additive migration for:

```text
external_identities

```

Fields:

```text
id UUID PK
user_id UUID FK

issuer VARCHAR NOT NULL
subject VARCHAR NOT NULL

email_at_link_time VARCHAR NULL

created_at TIMESTAMPTZ
last_seen_at TIMESTAMPTZ

UNIQUE(issuer, subject)

```

Email may change without creating a second user.

---

# 8. Principal

Resolve authentication into:

```python
@dataclass(frozen=True)
class Principal:
    user_id: UUID

    issuer: str
    subject: str

    roles: frozenset[str]
    permissions: frozenset[str]

    provider_ids: frozenset[UUID]

    worker_id: UUID | None

    tenant_id: UUID | None
    legal_entity_ids: frozenset[UUID]

```

Domain services consume Principal rather than JWT dictionaries.

---

# 9. Roles

```text
CUSTOMER

PROVIDER_OWNER
PROVIDER_MANAGER
WORKER

DISPATCHER
CUSTOMER_SUPPORT
TRUST_SAFETY
FINANCE

ADMIN
SUPER_ADMIN

```

---

# 10. Permissions

At minimum:

```text
project_request.read
project_request.manage

matching.run
matching.inspect

opportunity.read
opportunity.respond
opportunity.manage

quote.read
quote.create
quote.send
quote.accept

conversation.read
conversation.send

booking.read
booking.manage

job.read
job.assign
job.execute
job.complete

provider.read
provider.manage

provider.credentials.manage
provider.credentials.verify

provider.suspend

review.create
review.respond
review.moderate

dispute.create
dispute.manage

integration.read
integration.retry

finance.refund
finance.payout.approve

admin.users.manage
admin.features.manage
admin.audit.read

```

Role is not authorization by itself.

---

# 11. Record-level authorization

Authorization requires:

```text
authentication
+
permission
+
record ownership
+
provider membership
+
tenant/legal entity
+
resource state

```

Customer example:

```text
request.customer_id == principal.customer_id

```

Provider example:

```text
active provider membership
AND
resource.provider_id is in principal.provider_ids

```

Worker example:

```text
job.worker_id == principal.worker_id

```

Whenever practical, ownership filtering belongs in SQL.

Prefer:

```python
repository.quote_for_provider(
    quote_id,
    provider_id,
)

```

instead of:

```python
quote = repository.by_id(quote_id)

if quote.provider_id != provider_id:
    ...

```

---

# 12. Capabilities

Keep the existing canonical capability authority introduced by PR #35.

Do not create a second configuration system.

The domain registry eventually represents:

```text
request_intake

marketplace_matching
provider_opportunities
provider_self_service

quotes
messaging
reviews

instant_booking
automatic_assignment

payments
payouts
paid_leads

marketing

```

A capability becomes effective only when:

```text
code available
AND
release flag enabled
AND
dependencies enabled
AND
runtime provider ready
AND
environment permits it

```

Every sensitive backend command checks the capability.

Frontend visibility is not enforcement.

---

# 13. Capability guard

Concept:

```python
def require_capability(name: str):
    async def dependency(
        registry: CapabilityRegistry = Depends(get_capabilities),
    ):
        if not registry.enabled(name):
            raise CapabilityDisabled(name)

    return dependency

```

Domain service still validates capability for important commands so internal callers cannot bypass it.

---

# 14. Idempotency

Add:

```text
idempotency_records

```

Using current table naming conventions.

Fields:

```text
id UUID PK

actor_key VARCHAR
operation VARCHAR
idempotency_key VARCHAR

request_hash VARCHAR

status VARCHAR

resource_type VARCHAR NULL
resource_id UUID NULL

response_code INTEGER NULL
response_json JSONB NULL

created_at
updated_at
expires_at

UNIQUE(actor_key, operation, idempotency_key)

```

States:

```text
IN_PROGRESS
COMPLETED
FAILED

```

---

# 15. Commands requiring idempotency

At minimum:

```text
ProjectRequest submit

Provider application submit

Opportunity accept
Opportunity decline

Quote send
Quote revise
Quote accept
Quote decline

Booking confirm
Booking cancel

Job assignment
Job transition
Job completion

Review submit

Dispute create

Integration manual retry

Payment intent
Refund
Payout

```

Rules:

```text
same key + same request
→ same business result

same key + different request
→ 409

same key + processing
→ conflict/retry response

```

---

# 16. Optimistic concurrency

Important aggregates carry:

```text
version INTEGER NOT NULL

```

At minimum:

```text
ProjectRequest
Opportunity
Quote
Booking
Job
Provider

```

Update pattern:

```sql
UPDATE ...
SET ...,
    version = version + 1
WHERE id = :id
  AND version = :expected_version

```

Zero updated rows:

```text
409 CONCURRENT_MODIFICATION

```

Use row locks for commands where serialization is required.

---

# 17. Atomic business command

Important mutation transaction:

```text
business mutation
+
status history
+
audit event
+
idempotency completion
+
outbox event
=
ONE POSTGRESQL COMMIT

```

Never emit domain events after committing business state.

---

# 18. API V2 foundation

Create under:

```text
apps/api/app/api/v2/

```

Routers:

```text
router.py

catalog.py
project_requests.py
providers.py

customer.py
partner.py
worker.py

matching.py
opportunities.py

quotes.py
conversations.py

bookings.py
jobs.py
reviews.py

notifications.py
disputes.py

operations.py
admin.py

analytics.py
integrations.py
uploads.py

```

Keep V1 routes during migration.

No placeholder production endpoints returning fake success.

---

# 19. Capability endpoint compatibility

The existing canonical capability contract introduced by PR #35 remains authoritative.

If API V2 later exposes a compatibility projection, it must call the same `CapabilityService`.

Do not maintain:

```text
V1 capabilities
and
different V2 capabilities

```

---

# 20. API error contract

Standardize errors:

```json
{
  "code": "QUOTE_EXPIRED",
  "message": "The quote has expired.",
  "correlation_id": "...",
  "fields": null
}

```

Common status behavior:

```text
400 malformed command
401 authentication
403 authorization
404 unavailable/not found
409 state/concurrency/idempotency conflict
422 field/domain validation
429 rate limit
5xx platform/dependency failure

```

Do not expose internal stack traces.

---

# 21. Catalog API

```http
GET /api/v2/catalog/categories
GET /api/v2/catalog/categories/{slug}

GET /api/v2/catalog/services
GET /api/v2/catalog/services/{slug}
GET /api/v2/catalog/services/{id}/questions

```

Admin:

```http
POST  /api/v2/admin/catalog/categories
PATCH /api/v2/admin/catalog/categories/{id}

POST  /api/v2/admin/catalog/services
PATCH /api/v2/admin/catalog/services/{id}

POST  /api/v2/admin/catalog/services/{id}/questions
PATCH /api/v2/admin/catalog/questions/{id}
DELETE /api/v2/admin/catalog/questions/{id}

```

---

# 22. ProjectRequest domain

Tables:

```text
project_requests
project_request_answers
project_request_attachments
project_request_status_history

```

States:

```text
DRAFT
SUBMITTED
QUALIFYING
MATCHING
MATCHED
QUOTING
BOOKED

CANCELLED
EXPIRED
UNSERVICEABLE

```

Fulfillment:

```text
INSTANT_BOOK
QUOTE_REQUIRED
MANUAL_DISPATCH
UNSERVICEABLE

```

---

# 23. ProjectRequest API

```http
POST   /api/v2/project-requests
GET    /api/v2/project-requests/{id}
PATCH  /api/v2/project-requests/{id}

PUT    /api/v2/project-requests/{id}/answers/{questionId}
DELETE /api/v2/project-requests/{id}/answers/{questionId}

POST   /api/v2/project-requests/{id}/attachments
DELETE /api/v2/project-requests/{id}/attachments/{attachmentId}

POST /api/v2/project-requests/{id}/submit
POST /api/v2/project-requests/{id}/cancel

GET /api/v2/project-requests/{id}/matches
GET /api/v2/project-requests/{id}/quotes
GET /api/v2/project-requests/{id}/availability

```

---

# 24. Customer API

```http
GET   /api/v2/customer/profile
PATCH /api/v2/customer/profile

GET  /api/v2/customer/properties
POST /api/v2/customer/properties

GET    /api/v2/customer/properties/{id}
PATCH  /api/v2/customer/properties/{id}
DELETE /api/v2/customer/properties/{id}

GET /api/v2/customer/project-requests
GET /api/v2/customer/quotes
GET /api/v2/customer/conversations
GET /api/v2/customer/bookings
GET /api/v2/customer/jobs
GET /api/v2/customer/reviews

GET /api/v2/customer/notifications

POST /api/v2/customer/notifications/{id}/read

GET /api/v2/customer/communication-preferences
PUT /api/v2/customer/communication-preferences

```

---

# 25. Provider core

Add/extend using existing provider/vendor naming conventions:

```text
provider organizations/profile
provider members
provider workers
provider services
provider service areas
provider gallery

```

Do not create duplicate provider and vendor concepts if the existing domain can be migrated/extended.

---

# 26. Provider onboarding

Tables:

```text
provider_applications
provider_application_status_history

```

States:

```text
DRAFT
SUBMITTED
UNDER_REVIEW
NEEDS_INFORMATION
APPROVED
REJECTED

```

API:

```http
POST /api/v2/public/provider-applications

GET   /api/v2/partner/onboarding
PATCH /api/v2/partner/onboarding
POST  /api/v2/partner/onboarding/submit

GET /api/v2/admin/provider-applications
GET /api/v2/admin/provider-applications/{id}

POST /api/v2/admin/provider-applications/{id}/request-information
POST /api/v2/admin/provider-applications/{id}/approve
POST /api/v2/admin/provider-applications/{id}/reject

```

---

# 27. Provider portal API

```http
GET /api/v2/partner/dashboard

GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

GET /api/v2/partner/services
PUT /api/v2/partner/services

GET    /api/v2/partner/service-areas
POST   /api/v2/partner/service-areas
PATCH  /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

GET  /api/v2/partner/workers
POST /api/v2/partner/workers
GET /api/v2/partner/workers/{id}
PATCH /api/v2/partner/workers/{id}

GET /api/v2/partner/availability
PUT /api/v2/partner/availability

POST   /api/v2/partner/availability/exceptions
PATCH  /api/v2/partner/availability/exceptions/{id}
DELETE /api/v2/partner/availability/exceptions/{id}

GET  /api/v2/partner/credentials
POST /api/v2/partner/credentials

GET   /api/v2/partner/credentials/{id}
PATCH /api/v2/partner/credentials/{id}

POST /api/v2/partner/credentials/{id}/documents

GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads
GET /api/v2/partner/leads/{id}

GET /api/v2/partner/quotes
GET /api/v2/partner/quotes/{id}

POST /api/v2/partner/project-requests/{id}/quotes

PATCH /api/v2/partner/quotes/{id}

POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
POST /api/v2/partner/quotes/{id}/withdraw

GET /api/v2/partner/jobs
GET /api/v2/partner/jobs/{id}

GET /api/v2/partner/customers
GET /api/v2/partner/customers/{id}

GET /api/v2/partner/reviews

POST /api/v2/partner/reviews/{id}/response

GET /api/v2/partner/notifications

GET /api/v2/partner/analytics/overview
GET /api/v2/partner/analytics/funnel
GET /api/v2/partner/analytics/jobs
GET /api/v2/partner/analytics/revenue

```

---

# 28. Worker API

```http
GET /api/v2/worker/profile

GET /api/v2/worker/jobs
GET /api/v2/worker/jobs/{id}

POST /api/v2/worker/jobs/{id}/en-route
POST /api/v2/worker/jobs/{id}/arrive
POST /api/v2/worker/jobs/{id}/start
POST /api/v2/worker/jobs/{id}/complete

POST /api/v2/worker/jobs/{id}/notes
POST /api/v2/worker/jobs/{id}/evidence

GET /api/v2/worker/availability
PUT /api/v2/worker/availability

GET /api/v2/worker/credentials
GET /api/v2/worker/notifications

```

---

# 29. Credentials

Tables:

```text
credential_requirements
provider_credentials
credential_verifications
provider_documents

```

Credential states:

```text
PENDING
VERIFIED
REJECTED
EXPIRED
REVOKED

```

Requirements vary by:

```text
service
jurisdiction
provider/worker

```

Required credential invalid:

```text
provider is not eligible

```

Fail closed.

---

# 30. Availability

Tables:

```text
provider_availability_rules
provider_availability_exceptions

```

Support:

```text
timezone
multiple intervals
worker schedule
capacity
blackouts
vacation
effective date range
date overrides

```

Do not impose one universal work window.

---

# 31. Matching

Tables:

```text
matching_runs
match_candidates
match_reasons

```

Hard eligibility:

```text
provider active
service supported
service area match
credentials valid
insurance valid where required
not suspended
qualified worker available
schedule available
capacity available
legal entity compatible

```

V1 ranking:

```text
Availability               20
Distance                   20
Verified rating            15
Completion rate            10
Opportunity acceptance     10
Response speed             10
Price competitiveness       5
Prior relationship          5
BREERO quality score        5

```

Store the full score explanation.

No ML in V1.

---

# 32. Matching API

```http
POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates
GET /api/v2/ops/matching-runs/{id}/candidates/{candidateId}

```

Customer-safe:

```http
GET /api/v2/project-requests/{id}/matches

```

---

# 33. Opportunities

States:

```text
SENT
VIEWED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN

```

Tables:

```text
opportunities
opportunity_status_history
lead_connections

```

Customer PII remains restricted until LeadConnection policy authorizes disclosure.

---

# 34. Quotes

Tables:

```text
quotes
quote_versions
quote_line_items
quote_status_history

```

States:

```text
DRAFT
SENT
REVISED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN

```

Sent quote version is immutable.

Customer:

```http
GET /api/v2/project-requests/{id}/quotes
GET /api/v2/quotes/{id}

POST /api/v2/quotes/{id}/accept
POST /api/v2/quotes/{id}/decline

```

---

# 35. Conversations

Tables:

```text
conversations
conversation_participants
messages
message_attachments
message_receipts

```

Types:

```text
TEXT
IMAGE
DOCUMENT
QUOTE
APPOINTMENT_PROPOSAL
SYSTEM

```

API:

```http
GET /api/v2/conversations
GET /api/v2/conversations/{id}

GET /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/attachments

POST /api/v2/conversations/{id}/read

```

---

# 36. Booking bridge

Extend existing booking records additively.

Add nullable relationships:

```text
project_request_id
accepted_quote_id
provider_id
worker_id

```

Do not rewrite ambiguous historical rows.

API:

```http
GET /api/v2/bookings/{id}
GET /api/v2/bookings/{id}/timeline

POST /api/v2/bookings/{id}/confirm
POST /api/v2/bookings/{id}/reschedule-request
POST /api/v2/bookings/{id}/cancel

```

---

# 37. Job execution

States:

```text
CREATED
ASSIGNED
EN_ROUTE
ARRIVED
DIAGNOSING
AWAITING_APPROVAL
IN_PROGRESS
COMPLETED
CANCELLED

```

History:

```text
job_status_history
job_assignments
job_notes
job_evidence
job_additional_work

```

API:

```http
GET /api/v2/jobs/{id}
GET /api/v2/jobs/{id}/timeline

POST /api/v2/jobs/{id}/en-route
POST /api/v2/jobs/{id}/arrive
POST /api/v2/jobs/{id}/start
POST /api/v2/jobs/{id}/complete

POST /api/v2/jobs/{id}/notes
POST /api/v2/jobs/{id}/evidence
POST /api/v2/jobs/{id}/additional-work

```

---

# 38. Reviews

Tables:

```text
reviews
review_dimensions
review_responses
review_moderation

```

Only a completed BREERO job can create a verified review.

Dimensions:

```text
Overall
Quality
Communication
Timeliness
Value

```

API:

```http
POST /api/v2/jobs/{id}/review
GET /api/v2/reviews/{id}

GET /api/v2/providers/{slug}/reviews

POST /api/v2/partner/reviews/{id}/response

POST /api/v2/admin/reviews/{id}/moderate

```

---

# 39. Disputes

Add a real dispute domain before payments are activated.

Tables:

```text
disputes
dispute_status_history
dispute_evidence
dispute_notes

```

States:

```text
OPEN
UNDER_REVIEW
WAITING_CUSTOMER
WAITING_PROVIDER
RESOLVED
REJECTED
CLOSED

```

Customer:

```http
POST /api/v2/jobs/{id}/disputes
GET /api/v2/customer/disputes
GET /api/v2/customer/disputes/{id}

```

Provider:

```http
GET /api/v2/partner/disputes
GET /api/v2/partner/disputes/{id}

POST /api/v2/partner/disputes/{id}/respond

```

Ops:

```http
GET /api/v2/ops/disputes
GET /api/v2/ops/disputes/{id}

POST /api/v2/ops/disputes/{id}/request-information
POST /api/v2/ops/disputes/{id}/resolve

```

---

# 40. Notifications

Do not let domain services call email/SMS directly.

Flow:

```text
Domain Event
    ↓
NotificationPolicy
    ↓
Notification Intent
    ↓
Preference/Consent
    ↓
In-app
Email
SMS

```

Tables:

```text
notification_intents
notifications
notification_deliveries

```

Channels:

```text
IN_APP
EMAIL
SMS

```

Delivery states:

```text
PENDING
SENT
DELIVERED
FAILED_RETRYABLE
FAILED_TERMINAL
SUPPRESSED

```

---

# 41. Object storage / uploads

Add:

```text
storage_objects
upload_sessions

```

Purposes:

```text
PROJECT_ATTACHMENT
PROVIDER_CREDENTIAL
PROVIDER_GALLERY
JOB_EVIDENCE
DISPUTE_EVIDENCE

```

States:

```text
PENDING_UPLOAD
UPLOADED
SCANNING
CLEAN
QUARANTINED
REJECTED
DELETED

```

API:

```http
POST /api/v2/uploads
POST /api/v2/uploads/{id}/complete

GET /api/v2/uploads/{id}

DELETE /api/v2/uploads/{id}

```

Download access must be temporary and authorized.

Never publish permanent credential document URLs.

---

# 42. Malware scanning

Introduce interface:

```python
class MalwareScanner(Protocol):
    async def scan(
        self,
        object_ref: StorageObjectRef,
    ) -> ScanResult:
        ...

```

Only `CLEAN` files are available to domain consumers.

---

# 43. Geocoder

Introduce:

```python
class Geocoder(Protocol):
    async def geocode(
        self,
        address: PostalAddress,
    ) -> GeocodeResult:
        ...

```

Store normalized:

```text
latitude
longitude
timezone
normalized address
provider result code

```

PostGIS remains matching authority.

---

# 44. Operational exceptions

Add:

```text
operational_exceptions
exception_status_history
exception_notes

```

Types:

```text
NO_ELIGIBLE_PROVIDER
NO_PROVIDER_RESPONSE

STALE_OPPORTUNITY

QUOTE_OVERDUE
QUOTE_EXPIRED

CREDENTIAL_EXPIRING
CREDENTIAL_EXPIRED

SCHEDULING_CONFLICT
UNASSIGNED_JOB
LATE_JOB

INTEGRATION_RETRY_EXHAUSTED
WEBHOOK_PROCESSING_FAILED

PAYMENT_FAILED
PAYOUT_FAILED

```

States:

```text
OPEN
ACKNOWLEDGED
IN_PROGRESS
RESOLVED
IGNORED

```

API:

```http
GET /api/v2/ops/exceptions
GET /api/v2/ops/exceptions/{id}

POST /api/v2/ops/exceptions/{id}/acknowledge
POST /api/v2/ops/exceptions/{id}/assign
POST /api/v2/ops/exceptions/{id}/note
POST /api/v2/ops/exceptions/{id}/resolve

```

---

# 45. Operations APIs

```http
GET /api/v2/ops/project-requests
GET /api/v2/ops/project-requests/{id}

POST /api/v2/ops/project-requests/{id}/qualify
POST /api/v2/ops/project-requests/{id}/mark-unserviceable

POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates

POST /api/v2/ops/project-requests/{id}/opportunities
POST /api/v2/ops/opportunities/{id}/withdraw

GET /api/v2/ops/jobs
GET /api/v2/ops/jobs/{id}

POST /api/v2/ops/jobs/{id}/assign
POST /api/v2/ops/jobs/{id}/reassign
POST /api/v2/ops/jobs/{id}/cancel

GET /api/v2/ops/providers
GET /api/v2/ops/providers/{id}

GET /api/v2/ops/exceptions

GET /api/v2/ops/integration-events
GET /api/v2/ops/integration-failures

POST /api/v2/ops/integration-events/{id}/retry

```

---

# 46. Admin APIs

```http
GET /api/v2/admin/users
GET /api/v2/admin/users/{id}

GET /api/v2/admin/roles
GET /api/v2/admin/permissions

PUT /api/v2/admin/users/{id}/roles

GET /api/v2/admin/provider-applications

GET /api/v2/admin/providers
GET /api/v2/admin/providers/{id}

POST /api/v2/admin/providers/{id}/approve
POST /api/v2/admin/providers/{id}/suspend
POST /api/v2/admin/providers/{id}/reactivate

GET /api/v2/admin/credentials
GET /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

GET /api/v2/admin/features
GET /api/v2/admin/features/{key}
PUT /api/v2/admin/features/{key}

GET /api/v2/admin/audit-events
GET /api/v2/admin/audit-events/{id}

GET /api/v2/admin/reviews
POST /api/v2/admin/reviews/{id}/moderate

```

---

# 47. Audit

Append-only:

```text
audit_events

```

Fields:

```text
id
actor_id
actor_type

tenant_id
legal_entity_id

action

resource_type
resource_id

correlation_id

ip_address
user_agent

metadata_json

created_at

```

Never store secrets in audit metadata.

---

# 48. Analytics

Track:

```text
request_started
request_submitted
request_qualified
request_matched

opportunity_sent
opportunity_viewed
opportunity_accepted

quote_created
quote_sent
quote_accepted

booking_created

job_started
job_completed

review_submitted

repeat_request

```

Metrics:

```text
request conversion
serviceability
match rate
time to first match

provider response time
opportunity acceptance

quote rate
quote-to-book

completion
cancellation

repeat customers
provider retention

AOV when enabled
GMV when enabled
take rate when enabled

```

Analytics must not block operational commands.

Use domain event projection.

---

# 49. Database migration rules

Use the existing Alembic head.

Do not assume revision numbers before implementation.

Conceptual order:

```text
identity binding
shared command/audit/idempotency

ProjectRequest/catalog

provider marketplace
trust/availability

matching/opportunities

quotes/messages

booking/job/reviews

storage/uploads
notifications

exceptions/disputes

integration inbox/outbox

analytics

payments later

```

Use:

```text
expand
→ compatible code
→ backfill
→ validate
→ contract

```

Never big-bang destructive migrations.

---

# 50. Database indexes

Required high-value indexes include:

```text
project_requests(customer_id, created_at)
project_requests(status, created_at)
project_requests(service_id, status)

provider status/service indexes

PostGIS GiST service-area indexes

provider_credentials(provider_id, status, expires_at)

availability(provider_id, weekday)

matching_runs(project_request_id, created_at)
match_candidates(matching_run_id, eligible, rank)

opportunities(provider_id, status, expires_at)
opportunities(project_request_id, status)

quotes(project_request_id, status)
quotes(provider_id, status)

messages(conversation_id, created_at)

bookings(provider_id, window_start)

jobs(provider_id, status)
jobs(worker_id, status)

reviews(provider_id, created_at)

outbox(status, available_at)

exceptions(status, type, created_at)

audit(resource_type, resource_id, created_at)

```

Use EXPLAIN/ANALYZE for production-heavy queries.

---

# 51. Backend testing

Every domain needs:

```text
policy tests
state-machine tests
service tests

repository tests
real PostgreSQL tests

authorization tests
negative authorization tests

idempotency tests
concurrency tests

migration tests

event/outbox tests

```

PostGIS tests must use actual PostGIS.

SQLite is not a substitute.

---

# 52. Mandatory concurrency tests

At least:

```text
ProjectRequest submit

Opportunity accept

Quote accept

Booking creation

Job assignment

Review creation

Integration inbox deduplication

Payments later

```

Example:

```text
20 simultaneous quote acceptance commands
→ exactly one accepted state
→ exactly one booking
→ remaining requests replay/conflict safely

```

---

# 53. Backend Definition of Done

Marketplace backend is not complete until:

```text
OIDC works

issuer+subject identity linking works

record authorization works

capability enforcement works

idempotency works

optimistic concurrency works

audit works

ProjectRequest works

matching works

opportunities work

quotes work

messaging works

booking/job bridge works

reviews work

storage/scanning works

notifications work

Ops exceptions work

integration outbox/inbox work

all migrations pass

PostgreSQL/PostGIS tests pass

OpenAPI is generated

payments remain disabled until separately approved

```