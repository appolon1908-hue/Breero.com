# BREERO Marketplace V2 — Domain, Staging, Testing, and Delivery Implementation

The target should look like this:

```
```

```
Frontend / External API
        ↓
FastAPI Router
        ↓
Application Command
        ↓
Domain Service
        ↓
Policies + State Machine
        ↓
Repository
        ↓
PostgreSQL/PostGIS
        │
        ├── Audit
        ├── Idempotency
        └── Transactional Outbox
```

The router should never contain important marketplace logic.

# 1. Backend domain structure

I would make every major domain follow this pattern:

```
```

```
app/domains/
├── project_requests/
│   ├── models.py
│   ├── schemas.py
│   ├── commands.py
│   ├── service.py
│   ├── policies.py
│   ├── state_machine.py
│   ├── repository.py
│   ├── queries.py
│   ├── events.py
│   └── errors.py
│
├── providers/
├── credentials/
├── availability/
├── matching/
├── opportunities/
├── quotes/
├── conversations/
├── bookings/
├── jobs/
├── reviews/
├── payments/
├── compliance/
└── integrations/
```

Responsibility should be clear:

| LayerResponsibility |                                                  |
| ------------------- | ------------------------------------------------ |
| Router              | HTTP parsing, dependency injection, response DTO |
| Command             | Explicit user/system intention                   |
| Domain Service      | Business transaction/orchestration               |
| Policy              | Is this action legally/business-wise allowed?    |
| State Machine       | Is this transition valid?                        |
| Repository          | Persistence/query                                |
| Event               | What happened?                                   |
| Outbox              | Reliable external publication                    |

---

# 2. Example: ProjectRequest domain

A route should be very thin:

```
```

```
@router.post("/{request_id}/submit")
async def submit_request(
    request_id: UUID,
    principal: Principal = Depends(current_principal),
    context: CommandContext = Depends(command_context),
    session: AsyncSession = Depends(get_session),
):
    return await ProjectRequestService(session).submit(
        SubmitProjectRequest(
            project_request_id=request_id,
            principal=principal,
            context=context,
        )
    )
```

The actual logic belongs here:

```
```

```
class ProjectRequestService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProjectRequestRepository(session)
        self.outbox = OutboxService(session)
        self.audit = AuditService(session)
        self.idempotency = IdempotencyService(session)

    async def submit(
        self,
        command: SubmitProjectRequest,
    ) -> ProjectRequestView:

        request = await self.repository.for_update(
            command.project_request_id
        )

        ProjectRequestPolicy.require_owner(
            request,
            command.principal,
        )

        ProjectRequestStateMachine.require_transition(
            request.status,
            "SUBMITTED",
        )

        ProjectRequestPolicy.require_complete(request)

        await self.idempotency.acquire(
            command.context,
            "project_request.submit",
        )

        request.status = "SUBMITTED"
        request.version += 1
        request.submitted_at = utcnow()

        await self.audit.record(
            actor=command.principal,
            action="PROJECT_REQUEST_SUBMITTED",
            resource=request,
        )

        await self.outbox.add(
            event=ProjectRequestSubmitted.from_aggregate(
                request,
                command.context,
            )
        )

        await self.idempotency.complete(
            command.context,
            resource=request,
        )

        await self.session.commit()

        return ProjectRequestView.from_model(request)
```

That is the style I would enforce across the whole backend.

---

# 3. Policies become first-class code

For example:

```
```

```
class OpportunityPolicy:

    @staticmethod
    def can_accept(
        opportunity,
        provider,
        capability_registry,
    ) -> None:

        if not capability_registry.enabled(
            "provider_opportunities"
        ):
            raise CapabilityDisabled()

        if provider.status != "ACTIVE":
            raise ProviderNotActive()

        if provider.suspended:
            raise ProviderSuspended()

        if opportunity.provider_id != provider.id:
            raise Forbidden()

        if opportunity.status not in {
            "SENT",
            "VIEWED",
        }:
            raise InvalidOpportunityState()

        if opportunity.expires_at <= utcnow():
            raise OpportunityExpired()
```

Same concept for:

```
```

```
ProjectRequestPolicy
ProviderPolicy
CredentialPolicy
AvailabilityPolicy
MatchingPolicy
OpportunityPolicy
LeadConnectionPolicy
QuotePolicy
ConversationPolicy
BookingPolicy
JobPolicy
ReviewPolicy
PaymentPolicy
RefundPolicy
PayoutPolicy
```

---

# 4. Explicit state machines

Do not scatter:

```
```

```
if status == ...
```

everywhere.

Centralize transitions.

### ProjectRequest

```
```

```
DRAFT
 ↓
SUBMITTED
 ↓
QUALIFYING
 ↓
MATCHING
 ↓
MATCHED
 ↓
QUOTING
 ↓
BOOKED

terminal:
CANCELLED
EXPIRED
UNSERVICEABLE
```

### Opportunity

```
```

```
SENT
 ├── VIEWED
 │     ├── ACCEPTED
 │     └── DECLINED
 │
 ├── EXPIRED
 └── WITHDRAWN
```

### Quote

```
```

```
DRAFT
 ↓
SENT
 ├── ACCEPTED
 ├── DECLINED
 ├── EXPIRED
 ├── WITHDRAWN
 └── REVISED
        ↓
       SENT
```

### Job

```
```

```
CREATED
 ↓
ASSIGNED
 ↓
EN_ROUTE
 ↓
ARRIVED
 ↓
DIAGNOSING
 ↓
IN_PROGRESS
 ↓
COMPLETED
```

Optional:

```
```

```
AWAITING_APPROVAL
CANCELLED
```

Each state machine gets transition tests.

---

# 5. Domain events

Business state changes should produce domain events automatically.

Example:

```
```

```
@dataclass(frozen=True)
class JobCompleted:
    event_type = "job.completed.v1"

    job_id: UUID
    project_request_id: UUID
    provider_id: UUID
    customer_id: UUID
    occurred_at: datetime
```

Events:

```
```

```
project_request.submitted.v1
project_request.qualified.v1

matching.started.v1
matching.completed.v1

opportunity.sent.v1
opportunity.accepted.v1

lead.connected.v1

quote.sent.v1
quote.revised.v1
quote.accepted.v1

conversation.message_sent.v1

booking.created.v1
booking.confirmed.v1

job.assigned.v1
job.en_route.v1
job.started.v1
job.completed.v1

review.submitted.v1

credential.verified.v1
credential.expired.v1
```

---

# 6. Database transaction boundary

Every business command should ideally commit:

```
```

```
Business record changes
+
Status history
+
Audit record
+
Idempotency completion
+
Outbox event
```

in **one PostgreSQL transaction**.

That protects you from:

```
```

```
Job completed
but event never emitted
```

or:

```
```

```
Quote accepted
but duplicate retry creates another booking
```

---

# 7. Production staging environment

You should have at least:

```
```

```
development
staging
production
```

Prefer:

```
```

```
dev.breero.internal

staging-api.breero.com
staging.breero.com

api.breero.com
breero.com
```

Staging should be technically equivalent to production:

```
```

```
same container images
same Postgres major version
same PostGIS extension
same Redis major version
same migration chain
same reverse proxy
same Keycloak integration pattern
same middleware adapters
different credentials/data
```

Do not make staging a completely different Compose architecture.

---

# 8. Staging third-party mode

Staging should use:

```
```

```
Codestra test tenant
Klyrow sandbox/test routing
Telnexa sandbox/test recipients
Odoo staging DB
n8n staging workflow IDs
Stripe test mode
```

If a vendor has no sandbox:

```
```

```
adapter safe mode
+
recipient allowlist
+
maximum count
+
explicit staging flag
```

Never let staging accidentally send production SMS/email.

---

# 9. Testing architecture

Use several layers.

```
```

```
Unit
 ↓
Domain
 ↓
Repository
 ↓
API
 ↓
Integration
 ↓
Contract
 ↓
E2E
 ↓
Production smoke
```

### Unit tests

Test:

```
```

```
policy
state machine
scoring
money calculations
capability logic
validation
```

### Domain tests

Example:

```
```

```
expired credential
→ MatchingPolicy rejects provider

Quote SENT
→ revision allowed

Quote ACCEPTED
→ second acceptance denied/idempotent
```

### Database integration

Use real PostgreSQL/PostGIS.

Never SQLite for PostgreSQL-specific behavior.

Test:

```
```

```
foreign keys
transactions
locking
SKIP LOCKED
GiST indexes
ST_DWithin
unique constraints
concurrency
```

### API tests

Test:

```
```

```
200/201
400
401
403
404
409
422
429
5xx
```

### Security tests

Mandatory:

```
```

```
Customer A → Customer B resource denied

Provider A → Provider B resource denied

Worker → unassigned job denied

expired credential → matching denied

suspended provider → matching denied

disabled feature → backend denies
```

---

# 10. Concurrency tests

Especially for:

```
```

```
ProjectRequest submit
Opportunity accept
Quote accept
Booking creation
Job assignment
Review create
Payment webhook
Payout
```

Example:

```
```

```
20 simultaneous quote.accept requests
       ↓
exactly 1 acceptance
exactly 1 booking
19 replay/conflict responses
```

---

# 11. Integration testing

Every external adapter gets contract tests.

Example interface:

```
```

```
class NotificationProvider(Protocol):
    async def send_transactional_email(...)
    async def send_transactional_sms(...)
```

Test:

```
```

```
success
400
401
403
429
500
timeout
connection reset
duplicate
malformed response
```

---

# 12. Webhook testing

Every webhook must test:

```
```

```
valid signature
invalid signature
expired timestamp
duplicate event
replayed event
unknown event
malformed JSON
wrong tenant
wrong audience
processing failure
retry
```

Webhook must not create duplicate business effects.

---

# 13. Backup design

PostgreSQL needs:

```
```

```
automated scheduled backup
encrypted backup
off-server copy
retention
checksum
restore test
```

A reasonable starting policy:

```
```

```
Daily full/logical backup
Retain 14–30 days

Weekly longer-term
Retain 8–12 weeks
```

For stronger RPO:

```
```

```
WAL archiving / PITR
```

---

# 14. Restore rehearsal

At least monthly or before large production changes:

```
```

```
create isolated Postgres
 ↓
restore backup
 ↓
run consistency checks
 ↓
run migrations if required
 ↓
launch API
 ↓
execute smoke test
 ↓
destroy environment
```

Track:

```
```

```
BACKUP_SHA
BACKUP_DATE
RESTORE_STARTED
RESTORE_COMPLETED
RESTORE_DURATION
ROW_CHECKS
MIGRATION_HEAD
APPLICATION_HEALTH
```

---

# 15. Observability

Use structured logging.

Example:

```
```

```
{
  "level": "INFO",
  "event": "opportunity.accepted",
  "request_id": "...",
  "correlation_id": "...",
  "actor_id": "...",
  "provider_id": "...",
  "opportunity_id": "...",
  "duration_ms": 38
}
```

Never log:

```
```

```
JWT
Cookie
Authorization
password
API secret
private key
credential number
card data
```

---

# 16. Metrics

At minimum:

```
```

```
HTTP request count
HTTP latency
HTTP errors

DB query latency
connection pool

Redis latency

worker heartbeat
queue depth

outbox pending
outbox retryable
outbox terminal

webhook received
webhook duplicate
webhook invalid signature

matching duration
matching zero candidates

opportunity response time

quote send count
quote acceptance %

booking creation

job completion
job cancellation

provider response time
provider acceptance rate
```

---

# 17. Alerts

Production alerts:

```
```

```
API 5xx > threshold

API latency > threshold

DB unavailable
DB pool exhausted

Redis unavailable

worker missing heartbeat

outbox backlog increasing
FAILED_TERMINAL > 0

invalid webhook spike

matching zero-result spike

job assignment backlog

backup failed
restore check failed

disk usage high
certificate problem
```

---

# 18. Health endpoints

```
```

```
GET /health/live
GET /health/ready
GET /health/version
```

`/health/live`:

```
```

```
process alive
```

`/health/ready`:

```
```

```
PostgreSQL available
migration head valid
required internal dependencies valid
```

Do not make disabled optional vendors break readiness.

`/health/version`:

```
```

```
{
  "version": "2.3.1",
  "git_sha": "...",
  "build": "...",
  "migration_head": "..."
}
```

---

# 19. Deployment automation

Recommended pipeline:

```
```

```
Pull Request
   ↓
Lint
   ↓
Typecheck
   ↓
Unit tests
   ↓
Postgres/PostGIS tests
   ↓
Migration test
   ↓
Security tests
   ↓
OpenAPI check
   ↓
Build image
   ↓
SBOM/security scan
   ↓
Staging deploy
   ↓
Staging migrations
   ↓
Smoke tests
   ↓
E2E
   ↓
Approval
   ↓
Production deploy
   ↓
Production migration
   ↓
Health
   ↓
Canary
   ↓
Complete
```

---

# 20. Immutable deployment

Production should deploy:

```
```

```
image digest
+
git SHA
+
migration SHA
+
configuration checksum
```

not:

```
```

```
latest
```

Example:

```
```

```
ghcr.io/breero/api@sha256:...
```

---

# 21. Deployment rollback

Before deployment capture:

```
```

```
previous image digest
current migration revision
backup reference
configuration checksum
```

Rollback:

```
```

```
route/drain
 ↓
restore previous image
 ↓
verify schema compatibility
 ↓
health check
 ↓
smoke
```

Destructive migrations require a specific rollback strategy.

---

# 22. Database migration deployment

Use:

```
```

```
expand
 ↓
deploy compatible application
 ↓
backfill
 ↓
verify
 ↓
contract later
```

Do not deploy:

```
```

```
DROP COLUMN
```

that current production code still needs.

---

# 23. Customer page URLs

Public:

```
```

```
/
 /services
 /services/:slug

 /pros
 /pros/:slug

 /how-it-works
 /trust
 /about
 /contact

 /become-a-pro
```

Authentication:

```
```

```
/login
/register
/forgot-password
/reset-password
```

Request:

```
```

```
/request
/request/:id

/request/:id/questions
/request/:id/details
/request/:id/photos
/request/:id/property
/request/:id/location
/request/:id/timing
/request/:id/review
/request/:id/submitted
```

Customer account:

```
```

```
/account
/account/profile
/account/properties
/account/properties/:id
/account/communications
```

Marketplace:

```
```

```
/requests
/requests/:id

/requests/:id/matches
/requests/:id/quotes
```

Communication:

```
```

```
/messages
/messages/:conversationId
```

Fulfillment:

```
```

```
/bookings
/bookings/:id

/jobs
/jobs/:id

/reviews/:jobId
```

---

# 24. Provider portal URLs

I recommend a dedicated host:

```
```

```
pro.breero.com
```

Routes:

```
```

```
/
 /overview

 /onboarding

 /opportunities
 /opportunities/:id

 /leads
 /leads/:id

 /quotes
 /quotes/new
 /quotes/:id

 /messages
 /messages/:conversationId

 /schedule

 /jobs
 /jobs/:id

 /customers
 /customers/:id

 /workers
 /workers/new
 /workers/:id

 /services

 /service-areas

 /availability

 /credentials
 /credentials/new
 /credentials/:id

 /reviews

 /analytics

 /billing

 /settings
 /settings/profile
 /settings/team
 /settings/notifications
```

---

# 25. Worker portal URLs

Could be under provider portal:

```
```

```
pro.breero.com/worker
```

or:

```
```

```
worker.breero.com
```

Routes:

```
```

```
/
 /today

 /jobs
 /jobs/:id

 /schedule

 /availability

 /credentials

 /profile
```

For early stages I recommend keeping worker functionality under `pro.breero.com`.

---

# 26. Operations URLs

Dedicated:

```
```

```
ops.breero.com
```

Routes:

```
```

```
/
 /dashboard

 /requests
 /requests/:id

 /matching
 /matching/:runId

 /opportunities

 /jobs
 /jobs/:id

 /providers
 /providers/:id

 /exceptions
 /exceptions/:id

 /integrations
 /integrations/:eventId

 /map

 /analytics
```

---

# 27. Admin URLs

Dedicated:

```
```

```
admin.breero.com
```

Routes:

```
```

```
/
 /dashboard

 /provider-applications
 /provider-applications/:id

 /providers
 /providers/:id

 /credentials
 /credentials/:id

 /users
 /users/:id

 /roles

 /catalog
 /catalog/categories
 /catalog/services
 /catalog/services/:id

 /features

 /reviews

 /integrations

 /audit

 /system
 /system/health
 /system/releases
```

---

# 28. API URLs

Production:

```
```

```
https://api.breero.com
```

Public/customer:

```
```

```
https://api.breero.com/api/v2/...
```

Webhooks:

```
```

```
https://api.breero.com/webhooks/v1/codestra
https://api.breero.com/webhooks/v1/odoo
https://api.breero.com/webhooks/v1/klyrow
https://api.breero.com/webhooks/v1/telnexa
https://api.breero.com/webhooks/v1/n8n
https://api.breero.com/webhooks/v1/stripe
```

Health:

```
```

```
https://api.breero.com/health/live
https://api.breero.com/health/ready
```

Metrics should preferably **not** be public.

---

# 29. Staging URLs

Customer:

```
```

```
staging.breero.com
```

Provider:

```
```

```
staging-pro.breero.com
```

Ops:

```
```

```
staging-ops.breero.com
```

Admin:

```
```

```
staging-admin.breero.com
```

API:

```
```

```
staging-api.breero.com
```

Do not point staging to production DB.

---

# 30. Core navigation

Customer:

```
```

```
BREERO
├── Find Services
├── Find Pros
├── Requests
├── Messages
└── Account
```

Provider:

```
```

```
Overview
Opportunities
Leads
Quotes
Messages
Schedule
Jobs
Customers
Workers
Services
Service Areas
Availability
Credentials
Reviews
Analytics
Settings
```

Ops:

```
```

```
Dashboard
Requests
Matching
Jobs
Providers
Exceptions
Integrations
Map
Analytics
```

Admin:

```
```

```
Dashboard
Applications
Providers
Credentials
Users
Roles
Catalog
Features
Reviews
Integrations
Audit
System
```

---

# 31. Recommended implementation order

```
```

```
1 Domain architecture/common command infrastructure
2 Authentication/principal
3 Record authorization
4 Capabilities
5 Idempotency
6 Audit/outbox

7 ProjectRequest
8 Catalog/questionnaire

9 Provider core
10 Credentials
11 Availability

12 Matching
13 Opportunities
14 LeadConnection

15 Quotes
16 Conversations

17 Booking bridge
18 Jobs

19 Reviews

20 Operations
21 Admin

22 Third-party adapters
23 Webhook inbox

24 Observability
25 Backups
26 Deployment automation

27 Customer UI
28 Provider UI
29 Worker UI
30 Ops/Admin UI
```

The important change is philosophical as much as structural: **BREERO should no longer be an API with business logic embedded in routers. It should**