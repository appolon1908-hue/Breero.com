# BREERO Marketplace V2 — Integration Adapters and Production Gates

Yes. **You do need adapters**, but the important rule is that BREERO's domain must never depend directly on vendor SDKs or vendor-specific HTTP calls. The marketplace should depend on interfaces such as `EmailProvider`, `SmsProvider`, `CrmProjection`, `PaymentProvider`, `Geocoder`, `ObjectStorage`, and `WorkflowProvider`; production implementations then sit behind those interfaces.

The target should be:

```text
Customer / Provider / Worker / Ops / Admin
                    │
                    ▼
               BREERO API
                    │
              Domain Services
                    │
      ┌─────────────┼──────────────┐
      │             │              │
 PostgreSQL      Outbox         Audit
      │             │
      │             ▼
      │       Integration Workers
      │             │
      │     ┌───────┼─────────┬─────────┐
      │     ▼       ▼         ▼         ▼
      │  Codestra  Storage  Geocoder   Stripe
      │     │
      │     ├── Odoo
      │     ├── Klyrow
      │     ├── Telnexa
      │     └── approved n8n
      │
      └── Webhook Inbox ◀ external callbacks
```

## Adapters BREERO should have

| AdapterPurposeRequired for initial production?Direction |                                           |                                                           |                      |
| ------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------- | -------------------- |
| `IdentityProvider`                                      | Keycloak/OIDC identities and service auth | **Yes**                                                   | inbound auth         |
| `MiddlewareProvider`                                    | Codestra control-plane integration        | **Yes**                                                   | outbound + callbacks |
| `EmailProvider`                                         | Klyrow transactional email                | **Yes** if email notifications enabled                    | outbound + receipts  |
| `SmsProvider`                                           | Telnexa transactional SMS                 | Optional at first                                         | outbound + receipts  |
| `CrmProjection`                                         | Odoo CRM projection                       | Optional to customer transaction, important operationally | outbound/inbound ack |
| `WorkflowProvider`                                      | approved n8n workflows                    | Optional                                                  | outbound/callback    |
| `ObjectStorage`                                         | request photos, credentials, job evidence | **Yes**                                                   | read/write           |
| `MalwareScanner`                                        | uploaded-file scanning                    | **Yes** for public/provider uploads                       | internal             |
| `Geocoder`                                              | addresses → lat/lng                       | **Yes** for reliable matching                             | outbound             |
| `MapsProvider`                                          | maps/routes/distance UX where needed      | Recommended                                               | outbound             |
| `PaymentProvider`                                       | Stripe payment/refund                     | Later; **disabled now**                                   | outbound + webhook   |
| `PayoutProvider`                                        | Stripe Connect/provider settlement        | Later                                                     | outbound + webhook   |
| `SearchProvider`                                        | provider/service search index             | Later                                                     | projection           |
| `AnalyticsSink`                                         | product/marketplace analytics             | Recommended                                               | outbound             |
| `BackgroundCheckProvider`                               | provider/worker screening                 | Depends on business policy                                | outbound + callback  |
| `LicenseVerificationProvider`                           | trade/license checks                      | Depends on jurisdiction                                   | outbound + callback  |

The interfaces should look broadly like:

```python
class EmailProvider(Protocol):
    async def send(
        self,
        *,
        template: str,
        recipient: str,
        data: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProviderResult: ...


class Geocoder(Protocol):
    async def geocode(
        self,
        address: PostalAddress,
    ) -> GeocodeResult: ...


class ObjectStorage(Protocol):
    async def create_upload(
        self,
        *,
        key: str,
        content_type: str,
        max_size: int,
    ) -> UploadTarget: ...


class PaymentProvider(Protocol):
    async def create_payment_intent(...): ...
    async def refund(...): ...


class CrmProjection(Protocol):
    async def project_event(
        self,
        event: DomainEvent,
    ) -> None: ...
```

Then implementations are isolated:

```text
integrations/
├── identity/
│   └── keycloak.py
├── middleware/
│   └── codestra.py
├── email/
│   └── klyrow.py
├── sms/
│   └── telnexa.py
├── crm/
│   └── odoo.py
├── workflows/
│   └── n8n.py
├── storage/
│   └── object_storage.py
├── geocoding/
│   └── provider.py
├── payments/
│   └── stripe.py
└── search/
    └── search_projection.py
```

That way changing from one geocoder, storage provider, email provider, or payment provider does not force you to rewrite ProjectRequest, Matching, Quote, Job, etc.

# What is still required to reach final production

The remaining system is best thought of as **nine production gates**.

| GateRequired workProduction definition |                                                                                                     |                                                                  |
| -------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **1. API foundation**                  | full `/api/v2`, DTOs, error model, OpenAPI                                                          | all defined routes implemented; no placeholder production routes |
| **2. Database**                        | additive Alembic migrations, indexes, FK constraints, PostGIS                                       | empty→head and current-production→head both pass                 |
| **3. Identity/security**               | Keycloak/OIDC, issuer+subject linking, RBAC, record-level authorization                             | cross-customer/provider/worker isolation proven                  |
| **4. Command safety**                  | capabilities, idempotency, optimistic concurrency, audit                                            | duplicate/replayed commands create one business effect           |
| **5. Marketplace domains**             | requests, providers, matching, opportunities, leads, quotes, conversations, bookings, jobs, reviews | full marketplace lifecycle passes against real Postgres          |
| **6. Integrations**                    | adapters, outbox, inbox, webhooks, retries, circuit breaking                                        | vendor outage cannot lose BREERO transaction                     |
| **7. Storage/data**                    | object storage, malware scanning, retention, PII controls                                           | uploads private, authorized, scanned, lifecycle-managed          |
| **8. Operations**                      | Ops/Admin exception management, failed-event retry, audit, feature gates                            | operators can recover failures without DB editing                |
| **9. Production platform**             | staging, CI/CD, backups, restore, monitoring, TLS, secrets, rollback                                | staging soak + restore rehearsal + deployment canary pass        |

## The most important missing foundation after API work

The next code shouldn't jump directly from `/api/v2` into UI features. The shared backend production primitives should come first:

```text
Principal
Permission
RecordPolicy

CapabilityRegistry

CommandContext
IdempotencyService
OptimisticConcurrency

AuditService

DomainEvent
TransactionalOutbox

WebhookInbox

IntegrationAdapter
ProviderResult

CorrelationContext

ProblemDetails/ErrorContract
```

Every future domain then uses the same system.

For example:

```text
AcceptQuoteCommand
      │
      ▼
QuoteService.accept()
      │
      ├── require capability "quotes"
      ├── require authenticated customer
      ├── QuotePolicy.require_customer_access()
      ├── QuotePolicy.require_acceptance_allowed()
      ├── acquire idempotency
      ├── lock quote
      ├── transition SENT → ACCEPTED
      ├── transition ProjectRequest
      ├── create scheduling/booking result where policy permits
      ├── append history
      ├── append audit event
      ├── append quote.accepted.v1 outbox event
      ├── complete idempotency
      └── COMMIT
```

That pattern should be repeated throughout BREERO.

# Uploads are another major production area

Because customers will upload job photos and providers will upload licenses/insurance documents, add a real storage subsystem rather than storing blobs in PostgreSQL.

Recommended flow:

```text
Frontend
   ↓
POST /api/v2/uploads
   ↓
BREERO creates authorized upload session
   ↓
Object storage
   ↓
scan
   ↓
CLEAN
   ↓
attachment may be used
```

States:

```text
PENDING_UPLOAD
UPLOADED
SCANNING
CLEAN
REJECTED
QUARANTINED
DELETED
```

Private documents should use short-lived signed access, never permanent public URLs.

# Webhook infrastructure should be generic

Do not make six unrelated webhook systems.

Use:

```text
/webhooks/v1/codestra
/webhooks/v1/klyrow
/webhooks/v1/telnexa
/webhooks/v1/odoo
/webhooks/v1/n8n
/webhooks/v1/stripe
```

All pass through:

```text
raw request
    ↓
provider-specific authentication
    ↓
timestamp/replay validation
    ↓
external event ID
    ↓
request hash
    ↓
integration_inbox INSERT
    ↓
202
    ↓
worker
    ↓
event translator
    ↓
authorized domain command
```

The generic table should track:

```text
provider
external_event_id
event_type
schema_version

signature_verified
request_hash

status

attempt_count
next_attempt_at

received_at
processing_started_at
processed_at

correlation_id

last_error_code
```

Unique:

```text
(provider, external_event_id)
```

This is what makes third-party callbacks production-safe.

# Background worker architecture

You need more than the API process.

At minimum:

```text
breero-api
breero-outbox-worker
breero-inbox-worker
breero-scheduler
```

Scheduler responsibilities include:

```text
expire opportunities
expire quotes
expire temporary booking holds

detect credential expiration
create credential warnings

detect stale requests
detect scheduling exceptions

retry eligible integrations

create review reminders
```

Never use incoming HTTP traffic as the mechanism for scheduled business housekeeping.

# Operational exception system

A mature marketplace needs first-class exception records.

Examples:

```text
NO_ELIGIBLE_PROVIDER
NO_PROVIDER_RESPONSE

QUOTE_OVERDUE
QUOTE_EXPIRED

CREDENTIAL_EXPIRING
CREDENTIAL_EXPIRED

UNASSIGNED_JOB
JOB_LATE
SCHEDULING_CONFLICT

INTEGRATION_RETRY_EXHAUSTED
WEBHOOK_PROCESSING_FAILED

PAYMENT_FAILED
PAYOUT_FAILED
```

Ops should be able to:

```text
view
acknowledge
assign owner
add note
retry when applicable
resolve
```

with audit history.

# Notifications need their own policy layer

Don't simply send an email for every event.

Use:

```text
Domain Event
    ↓
NotificationPolicy
    ↓
Notification Intent
    ↓
channel preference / consent
    ↓
Email/SMS/In-app
```

Example:

```text
quote.sent.v1
    ↓
Customer notification
    ├── in-app always
    ├── transactional email if permitted
    └── transactional SMS if permitted/enabled
```

That keeps compliance logic out of Klyrow/Telnexa adapters.

# Search/discovery eventually needs a projection

For the first release, Postgres/PostGIS can do provider selection and geographic matching.

Later, public discovery can project provider profiles into a search engine:

```text
PostgreSQL
    ↓
provider.updated.v1
    ↓
Search projection worker
    ↓
Azure AI Search / OpenSearch / equivalent
```

Never make the search index authoritative for provider eligibility.

Matching always checks current PostgreSQL state.

# Production security still needs these controls

Before production marketplace activation, make sure you have:

```text
OIDC/JWT verification

issuer+subject identity link

record-level authorization

tenant/provider ownership filtering

capability enforcement

rate limiting

request size limits

upload type/size limits

malware scan

PII redaction

credential encryption

secret manager / *_FILE secret mounts

CSRF appropriate to auth architecture

CORS allowlist

webhook authentication

replay protection

idempotency

audit trails

dependency scanning

container scanning

SBOM

non-root containers
```

And the provider adapters should have:

```text
connect timeout
read timeout
bounded retries
exponential backoff
jitter
circuit breaker
health state
idempotency
structured error mapping
redacted logs
```

# Data retention and privacy

Before launch, define configurable retention jobs for:

```text
guest abandoned requests
customer account data
messages
job photos
provider credential documents
audit events
webhook payloads
integration logs
payment records
```

Don't leave these forever because the initial schema has no cleanup process.

Use policy configuration so legal/business decisions can change without rewriting domain logic.

# Deployment automation

The final deployment system should enforce:

```text
Git PR
  ↓
lint
  ↓
unit/domain tests
  ↓
PostgreSQL/PostGIS integration
  ↓
migration rehearsal
  ↓
authorization tests
  ↓
API/OpenAPI contract
  ↓
container build
  ↓
security scan/SBOM
  ↓
immutable image digest
  ↓
staging
  ↓
migration
  ↓
smoke
  ↓
full E2E
  ↓
approval
  ↓
production canary
  ↓
health/metrics
  ↓
production rollout
```

No production deployment from a developer laptop.

# Backup/disaster recovery

Also add:

```text
automated PostgreSQL backups
off-host encrypted copies
retention

object-storage replication/versioning where appropriate

backup monitoring

automated restore rehearsal

RPO target
RTO target
```

And actually test:

```text
backup
→ isolated DB
→ restore
→ migration validation
→ API boot
→ smoke marketplace flow
```

# The final page/domain surfaces

Once everything is assembled, the product surface should be:

```text
breero.com
Customer marketplace

pro.breero.com
Provider + Worker application

ops.breero.com
Marketplace operations

admin.breero.com
Administration / Trust / RBAC

api.breero.com
BREERO API

api.breero.com/webhooks/v1/*
Provider callback boundary
```

Customer core URLs:

```text
/
 /services
 /services/:slug

 /pros
 /pros/:slug

 /request/:id/*
 /requests
 /requests/:id

 /messages/:conversationId

 /bookings/:id
 /jobs/:id

 /reviews/:jobId

 /account/*
```

Provider:

```text
/overview
/opportunities
/leads
/quotes
/messages
/schedule
/jobs
/customers
/workers
/services
/service-areas
/availability
/credentials
/reviews
/analytics
/settings
```

Ops:

```text
/dashboard
/requests
/matching
/jobs
/providers
/exceptions
/integrations
/map
/analytics
```

Admin:

```text
/dashboard
/provider-applications
/providers
/credentials
/users
/roles
/catalog
/features
/reviews
/integrations
/audit
/system
```

## What I would build next

After the PR #35 foundation is incorporated, I would use this production sequence:

```text
be/marketplace-v2-p0-api-foundation
                    ↓
be/marketplace-v2-p0-database
                    ↓
be/marketplace-v2-p0-auth
                    ↓
be/marketplace-v2-p0-authorization
                    ↓
be/marketplace-v2-p0-capabilities-idempotency
                    ↓
be/marketplace-v2-p0-outbox-inbox
                    ↓
──────── SECURITY/RELIABILITY GATE ────────
                    ↓
ProjectRequest + Catalog
                    ↓
Provider + Trust + Availability
                    ↓
Matching
                    ↓
Opportunities + LeadConnection
                    ↓
Quotes
                    ↓
Messaging
                    ↓
Booking + Jobs
                    ↓
Reviews
                    ↓
Ops/Admin
                    ↓
Third-party adapters
                    ↓
Observability + backup + deployment automation
                    ↓
Frontend implementation
                    ↓
Full staging E2E
                    ↓
Production canary
```

So yes: **adapters are one missing piece, but not the only piece**. The biggest remaining work to reach a final production platform is the shared domain-command infrastructure, production authentication/record authorization, idempotency/concurrency, durable outbox/inbox, object storage/uploads, scheduled workers, operational exception handling, observability, backups/restores, and automated deployment gates. Once those are implemented under the existing domain architecture, the marketplace features can sit on a foundation that is much harder to corrupt or lose data from.