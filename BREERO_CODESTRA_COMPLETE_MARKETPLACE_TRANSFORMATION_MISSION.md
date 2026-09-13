# BREERO + CODESTRA COMPLETE MARKETPLACE TRANSFORMATION MISSION

## CODEX MASTER EXECUTION AUTHORITY

### Mission objective

Transform the existing `appolon1908-hue/Breero.com` repository into a complete, enterprise-grade, two-sided home-services marketplace operating on the shared Codestra platform.

This is an **extension, hardening, integration, and completion mission**.

Do **not** rewrite working BREERO foundations.

Preserve the existing architecture where it is sound:

* FastAPI modular monolith
* PostgreSQL/PostGIS
* async SQLAlchemy
* Psycopg
* Alembic
* Redis
* Celery/background workers
* transactional outbox
* existing domain/service/repository layering
* existing frontend applications
* existing API contracts
* Keycloak integration
* provider/vendor/worker domains
* booking and job lifecycle foundations
* Stripe/payment foundations
* finance and payout foundations
* Odoo integration foundations
* current Docker/Caddy production work
* existing security hardening
* current capability/feature-flag safety model

The objective is to turn the current system into a complete marketplace rather than replace it.

---

# 1. TARGET BUSINESS MODEL

BREERO must support the complete marketplace loop:

```text
Customer
   ↓
Project / Service Request
   ↓
Qualification
   ↓
Matching Engine
   ↓
Eligible Providers
   ↓
Opportunity / Lead
   ↓
Provider Acceptance
   ↓
Authorized Customer ↔ Provider Connection
   ↓
Conversation
   ↓
Quote
   ↓
Customer Acceptance
   ↓
Scheduling
   ↓
Capacity Reservation
   ↓
Booking
   ↓
Provider / Worker Assignment
   ↓
Job Execution
   ↓
Change Orders if required
   ↓
Completion Evidence
   ↓
Payment / Financial Ledger
   ↓
Provider Earnings
   ↓
Payout
   ↓
Verified Review
   ↓
Provider Reputation
   ↓
Better Future Matching
```

This closed loop is the primary product objective.

---

# 2. PLATFORM ARCHITECTURE

Treat Codestra as the platform.

Treat BREERO as one product running on that platform.

The major architecture is:

```text
                         INTERNET
                            │
                    Edge / WAF / CDN
                            │
                          Caddy
                            │
                           Kong
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
        BREERO            Klyrow          Telnexa
      Marketplace       Email SaaS        SMS SaaS
           │                │                │
           └────────────────┼────────────────┘
                            │
                       Event / Bus
                            │
                       Middleware
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
          Odoo           VICIdial       Other APIs
```

Shared platform services:

```text
Identity
└── Keycloak

Secrets / PKI
└── OpenBao

API Management
├── Caddy
└── Kong

Integration
└── Middleware

Email
└── Klyrow

SMS
└── Telnexa

Calling
└── VICIdial

Operational Observability
├── Codestra-Telemetry
├── Codestra-Alloy
├── Codestra-Prometheus
├── Codestra-Loki
├── Codestra-Tempo
├── Codestra-Alertmanager
├── Codestra-Grafana-
├── Codestra-Node-Exporter
├── Codestra-cAdvisor
├── Codestra-Redis-Exporter
├── Codestra-Postgres-Exporter
└── Codestra-Blackbox-Exporter

Business Analytics
└── Superset
```

---

# 3. ARCHITECTURE OWNERSHIP RULES

The following ownership rules are mandatory.

| Capability                       | Authority           |
| -------------------------------- | ------------------- |
| Marketplace transactional state  | BREERO              |
| Customers/projects/bookings/jobs | BREERO              |
| Provider network                 | BREERO              |
| Matching                         | BREERO              |
| Marketplace reviews              | BREERO              |
| Authentication                   | Keycloak            |
| Business authorization           | Product application |
| TLS ingress                      | Caddy               |
| API gateway/policies             | Kong                |
| Secrets/PKI                      | OpenBao             |
| Cross-system integrations        | Middleware          |
| Odoo writes                      | Middleware only     |
| Email transport                  | Klyrow              |
| SMS transport                    | Telnexa             |
| Calling                          | VICIdial            |
| CRM/ERP projection               | Odoo                |
| Metrics                          | Prometheus          |
| Logs                             | Loki                |
| Traces                           | Tempo               |
| Telemetry collection             | Alloy/OpenTelemetry |
| Alerting                         | Alertmanager        |
| Operational dashboards           | Grafana             |
| Business analytics               | Superset            |
| Infrastructure metrics           | Exporters           |

Do not duplicate platform responsibilities inside BREERO.

---

# 4. CRITICAL ODOO RULE

Monitoring systems must never directly mutate Odoo business data.

Forbidden:

```text
Prometheus → Odoo
Grafana → Odoo
Loki → Odoo
Tempo → Odoo
Alloy → Odoo
Exporter → Odoo
```

Correct:

```text
Operational Event
      ↓
Prometheus / Alertmanager
      ↓
Middleware
      ↓
Authorized workflow
      ↓
Odoo
```

Middleware must own:

* authentication
* authorization
* mapping
* schema translation
* deduplication
* idempotency
* retries
* audit
* dead-letter handling
* replay
* Odoo write policy

---

# 5. INITIAL CODEX PROCEDURE

Before changing code, Codex must inspect the current repository state.

Record:

```text
REPOSITORY
DEFAULT_BRANCH
CURRENT_MAIN_SHA
CURRENT_ALEMBIC_HEAD
CURRENT_OPENAPI_DIGEST
CURRENT_FRONTEND_CONTRACT_STATE
OPEN_PULL_REQUESTS
OPEN_P0_ISSUES
OPEN_P1_ISSUES
CURRENT_CAPABILITY_DEFAULTS
CURRENT_PRODUCTION_TOPOLOGY
CURRENT_STAGING_TOPOLOGY
CURRENT_KEYCLOAK_CONFIGURATION
CURRENT_KLYROW_INTEGRATION
CURRENT_TELNEXA_INTEGRATION
CURRENT_MIDDLEWARE_INTEGRATION
CURRENT_ODOO_INTEGRATION
CURRENT_OBSERVABILITY_STATE
```

Newer accepted repository state overrides older planning documents.

Do not work from stale branch assumptions.

---

# 6. DEVELOPMENT GOVERNANCE

Every substantial workstream gets its own branch and PR.

Do not create a permanent mega-branch.

Use dependency-safe sequencing.

Required rules:

```text
NO direct push to main
NO self-approval
NO ruleset bypass
NO stale-head merge
NO production deployment from feature branch
NO mutable latest image in production
NO migration first tested in production
NO capability activation hidden inside implementation PR
NO secret committed to Git
NO unreviewed Odoo write path
NO direct monitoring-to-Odoo writes
```

Each PR must have:

* focused ownership
* migrations when needed
* tests
* OpenAPI impact
* frontend contract impact
* security impact
* observability impact
* rollback/forward-fix boundary
* exact final SHA
* CI evidence
* independent review

---

# MILESTONE 0 — ARCHITECTURE INVENTORY AND BASELINE

## Objective

Establish one authoritative map of what is currently implemented.

## Tasks

Inspect:

```text
apps/api
apps/web
apps/partner
apps/ops
apps/admin
packages/ui
packages/types
packages/api-client
deploy
infrastructure
docs
odoo-addons
```

Create:

```text
docs/architecture/CURRENT_SYSTEM.md
docs/architecture/SYSTEM_OWNERSHIP.md
docs/architecture/API_REGISTRY.md
docs/architecture/CAPABILITY_REGISTRY.md
docs/architecture/INTEGRATION_REGISTRY.md
docs/architecture/DATA_CLASSIFICATION.md
```

Inventory every backend domain.

Classify each as:

```text
COMPLETE
PARTIAL
STUB
DARK
DEPRECATED
NOT_IMPLEMENTED
```

Inventory all frontend routes.

Inventory all workers.

Inventory all integrations.

Inventory all external providers.

Inventory all feature flags.

Inventory all data stores.

## Exit criteria

Milestone closes only when architecture documentation matches executable code.

---

# MILESTONE 1 — PRODUCTION SAFETY FOUNDATION

## Priority

P0

## Objective

Create a release foundation safe enough to support later marketplace activation.

## Required work

### Infrastructure

* close critical host capacity issues
* no production filesystem near exhaustion
* establish isolated staging
* ensure PostgreSQL is private
* ensure Redis is private
* ensure application ports are only exposed through approved ingress
* reconcile competing Docker Compose definitions
* establish one canonical deployment authority
* health/readiness checks
* worker heartbeat
* scheduler heartbeat

### Release artifacts

Build once in trusted CI.

Produce:

```text
IMAGE_DIGESTS
SOURCE_SHA
SBOM
PROVENANCE
DEPENDENCY_SCAN
IMAGE_SCAN
OPENAPI_DIGEST
CONFIG_DIGEST
CAPABILITY_SNAPSHOT
MIGRATION_HEAD
ROLLBACK_MANIFEST
```

### Database gate

For releases containing migrations:

```text
backup
↓
restore backup into isolated environment
↓
validate integrity
↓
run migration
↓
require exit 0
↓
verify alembic current == expected head
↓
run smoke tests
↓
start API/workers
↓
readiness
↓
canary
↓
public routing
```

## Exit criteria

No unresolved release P0 blocker.

---

# MILESTONE 2 — IDENTITY, TENANCY, RBAC AND SECURITY

## Priority

P0

## Identity authority

Keycloak.

Canonical production issuer:

```text
https://auth.codestra.co/realms/codestra
```

## Browser authentication

Use:

```text
Authorization Code
+
PKCE S256
```

## Machine authentication

Use:

```text
OAuth2 Client Credentials
```

## Backend validation

Validate:

* issuer
* audience
* azp when required
* kid
* signature
* approved algorithm
* exp
* nbf
* iat
* subject
* tenant
* roles
* permissions

## Build

* external identity binding
* tenants/legal entities
* organizations
* memberships
* roles
* permissions
* server-created principal
* command context
* record policies
* provider boundaries
* worker boundaries
* customer resource ownership
* machine-account boundaries

## Negative tests

Required:

```text
wrong issuer
wrong audience
wrong algorithm
expired token
not-yet-valid token
unknown kid
malformed token
missing token
inactive user
removed membership
cross-tenant access
cross-provider access
cross-customer access
worker-to-unassigned-job access
machine-account human-route access
role escalation
superadmin escalation
```

## OpenBao

Move secrets progressively to OpenBao.

Secret classes include:

* database credentials
* Redis credentials
* Keycloak clients
* Stripe
* Klyrow
* Telnexa
* SMTP
* SMPP
* signing keys
* webhook secrets
* Odoo credentials
* API provider credentials
* certificates

Prefer workload identities and short-lived credentials where supported.

## Exit criteria

Production authentication is Keycloak-authoritative and tenancy is fail-closed.

---

# MILESTONE 3 — API V1/V2 GOVERNANCE

## Priority

P0

## Objective

Create a predictable, versioned API platform.

Preserve compatible V1 behavior.

Introduce V2 additively.

Every endpoint must be registered.

Required registry fields:

```text
method
path
version
domain
owner
audience
authentication
permission
tenant_scope
record_policy
capability
rate_limit_class
idempotency_requirement
request_hash_policy
optimistic_version_policy
request_schema
response_schema
error_contract
PII_classification
event_effect
deprecation_state
replacement_endpoint
```

## State-changing commands

Every state-changing command must:

1. authenticate;
2. authorize;
3. validate tenant/record scope;
4. check capability;
5. validate command;
6. enforce idempotency;
7. enforce concurrency/version;
8. perform explicit state transition;
9. commit audit/history;
10. commit outbox event atomically;
11. return correlation identifier.

## Standard headers

Support where relevant:

```text
Authorization
Idempotency-Key
If-Match
ETag
X-Request-ID
X-Correlation-ID
Retry-After
WWW-Authenticate
```

## CI

CI fails if:

* OpenAPI is stale
* typed client is stale
* route missing from registry
* undocumented state-changing command exists
* frontend calls unknown route
* duplicate API ownership exists

## Exit criteria

OpenAPI and frontend typed contracts represent executable code exactly.

---

# MILESTONE 4 — CUSTOMER PROJECT AND SERVICE REQUEST SYSTEM

## Priority

P1

## Objective

Make customer demand a first-class domain.

Canonical object:

```text
ProjectRequest
```

## Lifecycle

```text
DRAFT
↓
SUBMITTED
↓
QUALIFYING
↓
QUALIFIED
↓
MATCHING
↓
MATCHED
↓
CONNECTED
↓
QUOTED
↓
CONVERTED_TO_BOOKING
```

Additional terminal states:

```text
CANCELLED
EXPIRED
UNSERVICEABLE
NEEDS_MANUAL_REVIEW
```

## Build

* project draft
* service/category
* address
* geography
* questions
* photos/files
* scope
* urgency
* preferred time
* customer contact
* communication consent
* service qualification
* price-mode classification

Supported product modes:

```text
REQUEST_ONLY
QUOTE_REQUIRED
INSTANT_BOOKABLE
```

Do not treat every service the same.

## Public submission hardening

Required:

* canonical request hash
* idempotency
* duplicate race protection
* timeout retry safety
* rate limiting
* Retry-After
* bot/honeypot controls
* consent version
* correlation ID
* safe validation errors

## Exit criteria

Customer requests are durable, observable, recoverable and cannot create fake bookings.

---

# MILESTONE 5 — PROVIDER NETWORK AND ONBOARDING

## Priority

P1

## Objective

Build a marketplace-grade supply network.

## Provider organization

Fields should include:

* legal name
* DBA
* tax/business identifiers
* addresses
* contact data
* service categories
* territories
* approval state
* compliance state
* operational state
* payout configuration state

## Membership

Support:

```text
OWNER
ADMIN
DISPATCHER
TECHNICIAN
FINANCE
READ_ONLY
```

## Provider application lifecycle

```text
DRAFT
SUBMITTED
UNDER_REVIEW
APPROVED
REJECTED
SUSPENDED
EXPIRED
```

## Compliance

Track:

* business verification
* licenses
* insurance
* background checks
* service qualification
* expiration
* reviewer
* decision
* suspension reason
* audit history

Use the central document pipeline.

Do not implement a second independent upload/security system.

## Provider catalog

Support:

* services
* skills
* capabilities
* pricing mode
* service areas
* working hours
* capacity
* worker assignments

## Exit criteria

Only approved, qualified providers can become marketplace candidates.

---

# MILESTONE 6 — GEOGRAPHY, COVERAGE, SCHEDULING AND CAPACITY

## Priority

P1

## Geography

Use PostGIS.

Support:

* country
* state/province
* city
* ZIP/postal code
* county
* radius
* polygon
* service zone

## Address validation

Backend remains authoritative.

Frontend must not decide coverage.

Address failure policy:

```text
REQUEST_ACCEPTED_FOR_REVIEW=true
AUTOMATIC_SERVICEABILITY=false
AUTOMATIC_BOOKING=false
AUTOMATIC_ASSIGNMENT=false
```

## Timezone

Use authoritative IANA timezone derived from service address.

Test:

* DST forward
* DST backward
* ambiguous local time
* nonexistent local time
* Arizona
* Hawaii
* cross-timezone operations

## Capacity

Build:

* provider schedule
* worker schedule
* time off
* vacation
* sickness
* manual block
* holidays
* BREERO policy hours
* service duration
* travel buffer
* before/after buffer
* existing jobs
* active holds
* maximum jobs/day
* maximum minutes/day
* concurrent job limits
* emergency reserve

## Capacity hold lifecycle

```text
HELD
CONVERTED
EXPIRED
RELEASED
```

Default hold duration can be 30 minutes unless product configuration says otherwise.

## Mandatory race test

```text
Customer A requests last available slot.
Customer B requests same slot concurrently.

Expected:
Only authorized capacity survives.
```

## Performance objective

Availability search must avoid repeated N+1 database work.

Profile and optimize:

* provider candidate query
* service-zone checks
* worker availability
* active holds
* booking overlap queries
* schedule rules

## Exit criteria

Availability is authoritative, concurrent-safe and performant.

---

# MILESTONE 7 — MATCHING ENGINE

## Priority

P1

## Objective

Build explainable provider matching.

## Eligibility filters

Before scoring, provider must satisfy:

```text
active
approved
compliant
service qualified
skills qualified
coverage matched
schedule matched
capacity available
not suspended
no conflicting job/time off
emergency policy when applicable
```

## Matching inputs

Possible weighting inputs:

* distance
* estimated travel time
* exact skill
* service specialization
* available capacity
* response rate
* acceptance rate
* completion rate
* cancellation rate
* on-time rate
* verified rating
* complaint rate
* prior relationship
* emergency eligibility

## Explainability

Each candidate should include reason codes.

Example:

```json
{
  "eligible": true,
  "score": 0.83,
  "reasons": [
    "SERVICE_EXACT_MATCH",
    "INSIDE_PRIMARY_SERVICE_ZONE",
    "CAPACITY_AVAILABLE",
    "HIGH_COMPLETION_RATE"
  ]
}
```

Do not expose confidential internal risk scoring publicly.

## Initial operational mode

```text
PROVIDER_ASSIGNMENT_MODE=MANUAL
AUTO_ASSIGN_PROVIDER=false
AUTO_CONFIRM_BOOKING=false
```

Matching may recommend.

Human operations initially assigns.

## Exit criteria

Operators can understand why a provider was included, excluded and ranked.

---

# MILESTONE 8 — OPPORTUNITIES, LEADS AND CONNECTIONS

## Priority

P1

Create distinct domain concepts.

Do not collapse them.

```text
ProjectRequest
     ↓
MatchingRun
     ↓
Opportunity
     ↓
Provider Acceptance
     ↓
LeadConnection
```

An opportunity is not a customer connection.

Provider customer-PII access must remain restricted until authorized connection.

## Opportunity states

```text
OFFERED
VIEWED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN
```

## Lead connection states

```text
ACTIVE
CLOSED
CONVERTED
EXPIRED
```

## Commercial lead features

Infrastructure may support:

* lead pricing
* paid lead
* subscription
* featured placement

But default:

```text
PAID_LEADS_ENABLED=false
FEATURED_PROVIDERS_ENABLED=false
```

These require later commercial activation.

## Exit criteria

Customer information is disclosed only after authorized relationship establishment.

---

# MILESTONE 9 — CONVERSATIONS, QUOTES AND CHANGE ORDERS

## Priority

P1

## Messaging

Conversation exists only for authorized relationships.

Support:

* customer/provider messages
* support participants
* read/unread
* attachments
* timestamps
* moderation
* audit
* privacy filtering

## Quote lifecycle

```text
DRAFT
SUBMITTED
PENDING_CUSTOMER
ACCEPTED
DECLINED
EXPIRED
SUPERSEDED
```

Quotes are immutable by version.

Any revision creates a new version.

Store:

* labor
* materials
* fees
* tax
* discounts
* total
* assumptions
* terms
* expiration

## Customer acceptance

Acceptance does not automatically equal:

* payment
* booking confirmation
* job assignment

Each transition remains explicit.

## Change order lifecycle

```text
PROPOSED
UNDER_REVIEW
PENDING_CUSTOMER
ACCEPTED
REJECTED
PAYMENT_PENDING
APPROVED
```

Never silently mutate agreed scope.

## Exit criteria

Every scope/price change is versioned and auditable.

---

# MILESTONE 10 — BOOKING, DISPATCH AND JOB EXECUTION

## Priority

P1

## Booking lifecycle

Implement explicit state transitions.

Example:

```text
PENDING
AWAITING_PAYMENT
CONFIRMED
ASSIGNMENT_PENDING
ASSIGNED
IN_PROGRESS
COMPLETED
CANCELLED
FAILED
```

## Dispatch

Operations portal needs:

* unassigned jobs
* urgent jobs
* failed assignment
* candidates
* alternatives
* provider capacity
* technician capacity
* map context
* service zone
* travel estimate
* compliance
* timezone
* assign
* reassign
* unassign
* hold
* escalate

Every assignment change requires a reason and audit entry.

## Job state

Example:

```text
CREATED
ASSIGNED
EN_ROUTE
ARRIVED
STARTED
DIAGNOSTIC
PAUSED_FOR_CHANGE_ORDER
RESUMED
COMPLETED
CANCELLED
```

## Completion evidence

Support:

* photos
* notes
* timestamps
* signatures where appropriate
* technician identity
* scope confirmation
* customer acknowledgment

## Exit criteria

A booking can proceed to completed job with immutable history and recovery paths.

---

# MILESTONE 11 — KLYROW EMAIL INTEGRATION

## Repository

```text
appolon1908-hue/klyrow.com
```

## Authority

Klyrow owns email transport.

BREERO does not become an SMTP platform.

## Integration path

```text
BREERO
↓
Transactional Outbox
↓
Middleware
↓
Klyrow
↓
Postal / Email transport
```

## Use Klyrow for

* email verification
* security notifications
* booking notifications
* quote notifications
* job notifications
* provider invitations
* payout notifications
* transactional receipts
* support email
* approved marketing later

## Template ownership

Version templates.

Include:

```text
template_id
template_version
locale
channel
event_type
required_variables
```

## Callbacks

Process:

* submitted
* delivered
* deferred
* bounced
* complaint
* suppressed
* unsubscribed

Return relevant state through Middleware.

## Kill switch

```text
LIVE_EMAIL_DELIVERY=false
```

When false:

* zero real Klyrow deliveries
* events parked safely
* no false success
* retries cannot bypass switch

## Exit criteria

Transactional email delivery is traceable end-to-end.

---

# MILESTONE 12 — TELNEXA SMS INTEGRATION

## Repository

```text
appolon1908-hue/telnexa
```

## Authority

Telnexa owns SMS.

## Integration path

```text
BREERO
↓
Transactional Outbox
↓
Middleware
↓
Telnexa
↓
Jasmin
↓
Carrier
```

## Support

* outbound SMS
* inbound/MO SMS
* DLR
* sender management
* messaging API
* tenant routing
* billing/quota
* carrier routing
* delivery status

## Required message controls

* tenant ID
* idempotency key
* correlation ID
* normalized destination
* sender
* template ID
* purpose
* consent status
* suppression status

## Delivery event flow

```text
Carrier
↓
Telnexa
↓
Signed provider event
↓
Middleware
↓
BREERO integration inbox
```

## Kill switch

```text
LIVE_SMS_DELIVERY=false
```

When disabled:

* no carrier submission
* no false delivered state
* message remains recoverable
* retries cannot bypass control

## Exit criteria

MT + DLR + MO flows reconcile correctly.

---

# MILESTONE 13 — SHARED EVENT CONTRACT AND EVENT BUS

## Priority

P1

Define one Codestra event envelope.

Example:

```json
{
  "event_id": "uuid",
  "event_type": "booking.confirmed",
  "event_version": 1,
  "schema_version": 1,
  "source": "breero",
  "tenant_id": "uuid",
  "correlation_id": "uuid",
  "trace_id": "trace",
  "occurred_at": "timestamp",
  "subject_type": "booking",
  "subject_id": "uuid",
  "data": {}
}
```

Required fields:

```text
event_id
event_type
event_version
schema_version
source
tenant_id
correlation_id
trace_id
occurred_at
subject_type
subject_id
data
```

## Reliability

Implement:

* transactional outbox
* durable inbox
* event deduplication
* idempotent consumer
* leases
* stale lease recovery
* exponential retry
* dead-letter handling
* replay authorization
* reconciliation

## Event infrastructure

Use an approved broker.

Preferred options:

```text
Azure Service Bus
```

or platform-neutral:

```text
RabbitMQ
```

Do not add Kafka without a demonstrated requirement.

## Exit criteria

Business events are durable and recoverable across product boundaries.

---

# MILESTONE 14 — MIDDLEWARE CONTROL PLANE

## Objective

Middleware becomes the governed cross-system integration layer.

## Responsibilities

* event ingestion
* event validation
* normalization
* workflow routing
* Klyrow adapter
* Telnexa adapter
* VICIdial adapter
* Odoo adapter
* provider API adapters
* retry
* DLQ
* reconciliation
* idempotency
* schema mapping
* audit
* operational status

## Architecture rule

Applications publish business events.

Middleware determines how outside systems are updated.

Example:

```text
BREERO
└── JobCompleted.v1
        ↓
    Middleware
       ├── Odoo
       ├── Klyrow
       ├── analytics pipeline
       └── other approved integration
```

## Odoo

BREERO database remains marketplace truth.

Odoo remains CRM/operations projection.

Never make Odoo authoritative for core booking/job state unless explicitly redesigned.

## Exit criteria

All cross-system writes have one governed path.

---

# MILESTONE 15 — PAYMENTS AND FINANCIAL LEDGER

## Priority

P1/P2

Default:

```text
PAYMENTS_ENABLED=false
```

until certified.

## Stripe

Stripe is external settlement authority.

Backend remains authoritative for marketplace state.

## Required flows

* payment intent
* authorization
* capture
* webhook signature verification
* duplicate webhook handling
* timeout reconciliation
* refund
* partial refund
* dispute
* payment failure
* cancellation

Browser redirect is never proof of payment.

Only verified provider events settle payment.

## Ledger

Create immutable financial ledger entries for:

* customer charge
* tax
* platform fee
* provider gross earning
* provider adjustment
* refund
* dispute
* payout liability
* payout settlement
* reversal

Do not rely solely on mutable payment status fields.

## Exit criteria

Finance can reconstruct every balance from immutable financial history.

---

# MILESTONE 16 — PROVIDER EARNINGS AND PAYOUTS

## Default

```text
PAYOUTS_ENABLED=false
```

## Build

* provider earning
* pending earning
* available earning
* hold
* adjustment
* provider statement
* payout batch
* payout approval
* payout submission
* payout settlement
* payout failure
* reconciliation

## Separation of duties

Dispatch cannot approve payouts.

Support cannot approve payouts.

Provider cannot approve own payout.

Finance/admin approval must be server-enforced.

## Exit criteria

Every provider payout reconciles to jobs and ledger entries.

---

# MILESTONE 17 — REVIEWS, TRUST AND REPUTATION

## Priority

P2

Default:

```text
REVIEWS_ENABLED=false
```

until implemented.

## Eligibility

Only verified completed-job customers can review.

## Review data

* overall rating
* quality
* timeliness
* communication
* value
* written review
* photos where approved
* provider response
* moderation status
* abuse report status

## Performance model

Calculate approved provider metrics from real transactions:

* acceptance rate
* response rate
* completion rate
* cancellation rate
* reassignment rate
* on-time rate
* complaint rate
* verified rating
* repeat-customer rate

## Matching integration

Only approved reputation inputs feed matching.

No opaque public-risk score.

## Exit criteria

Completed work creates trustworthy marketplace reputation.

---

# MILESTONE 18 — SUPPORT, TRUST AND SAFETY

Build:

* support cases
* disputes
* customer complaints
* provider complaints
* trust review
* fraud review
* evidence
* internal notes
* customer-visible messages
* provider-visible messages
* escalation
* resolution

Internal notes must never leak externally.

All privileged actions require audit records.

---

# MILESTONE 19 — COMPLETE FRONTEND PRODUCT SURFACES

## Customer marketplace

Build/complete:

```text
homepage
service discovery
category pages
service pages
project request wizard
quote comparison
conversation
booking
booking history
job tracking
payments
refunds
support
reviews
account
addresses
preferences
privacy
```

## Provider portal

Build:

```text
dashboard
onboarding
company
team
services
skills
coverage
schedule
capacity
compliance
opportunities
quotes
conversations
jobs
earnings
payouts
performance
security
```

## Worker portal

Build:

```text
today
upcoming jobs
job details
route/address
on-my-way
arrived
start
diagnostic
change-order request
complete
evidence
availability
credentials
```

## Operations portal

Build:

```text
requests queue
matching
dispatch
urgent work
unassigned jobs
provider review
compliance
support
disputes
exceptions
integration recovery
communications status
audit timeline
```

## Admin portal

Build:

```text
catalog
service zones
pricing
users
roles
permissions
tenants
capabilities
provider approvals
integrations
finance
audit
analytics
system health
release status
```

## Frontend quality

Every surface needs:

* loading
* empty
* disabled
* restricted
* error
* success
* retry
* offline/network failure
* responsive layout
* keyboard support
* accessible forms
* accessible dialogs
* real API data

No fake KPIs.

No fake success states.

---

# MILESTONE 20 — CODESTRA OBSERVABILITY PLATFORM

Integrate BREERO into the complete monitoring system.

## Required repositories

```text
Codestra-Prometheus
Codestra-Alertmanager
Codestra-Grafana-
Codestra-Telemetry
Codestra-Alloy
Codestra-Loki
Codestra-Tempo
Codestra-Node-Exporter
Codestra-cAdvisor
Codestra-Redis-Exporter
Codestra-Blackbox-Exporter
Codestra-Postgres-Exporter
Superset
Codestra-OpenBao
```

## Canonical telemetry flow

```text
Servers
BREERO
Middleware
Odoo
Klyrow
Telnexa
VICIdial
Keycloak
Kong
Caddy
   │
   ├── OpenTelemetry
   ├── exporters
   └── Alloy
          │
          ▼
    ┌─────────────┐
    │ Prometheus  │
    │ Loki        │
    │ Tempo       │
    └──────┬──────┘
           │
           ├──────→ Grafana
           │
           ▼
     Alertmanager
           │
           ▼
       Middleware
```

## BREERO metrics

At minimum:

### API

```text
request rate
latency
error rate
status codes
route
timeouts
rate limits
```

### Marketplace

```text
service requests
qualified requests
matching runs
matching failures
no-provider results
opportunities
connections
quote conversion
booking conversion
job completion
job cancellation
```

### Scheduling

```text
availability latency
capacity conflicts
hold count
hold expiry
slot utilization
```

### Providers

```text
active providers
approved providers
suspended providers
compliance expirations
provider response time
provider acceptance
```

### Workers

```text
active workers
assigned jobs
job state duration
late arrivals
completion
```

### Finance

```text
payment attempts
captures
payment failures
refunds
reconciliation discrepancies
payout failures
```

### Integrations

```text
outbox pending
oldest outbox age
retry count
DLQ
Klyrow latency
Telnexa latency
Odoo projection lag
Middleware failures
```

### Worker infrastructure

```text
Celery workers
queue depth
worker heartbeat
scheduler heartbeat
task failures
task retries
```

---

# MILESTONE 21 — LOGGING AND TRACING

## Loki

All structured logs should carry safe context:

```text
timestamp
service.name
service.version
deployment.environment
severity
trace_id
span_id
request_id
correlation_id
tenant_id where safe
event_name
domain
```

Never log:

* passwords
* access tokens
* refresh tokens
* reset tokens
* SMTP credentials
* SMPP credentials
* API keys
* raw payment data
* OpenBao secrets

## Tempo

Trace requests across:

```text
Browser
↓
Caddy
↓
Kong
↓
BREERO
↓
PostgreSQL / Redis
↓
Outbox
↓
Middleware
↓
Klyrow / Telnexa / Odoo
```

Preserve:

```text
trace_id
correlation_id
```

## Exit criteria

Operations can trace one business transaction across the platform.

---

# MILESTONE 22 — ALERTING

Prometheus evaluates alert conditions.

Alertmanager performs:

* grouping
* deduplication
* routing
* silence management
* escalation

Notification path:

```text
Prometheus
↓
Alertmanager
↓
Middleware
↓
Klyrow / Telnexa / VICIdial / approved channel
```

Examples:

```text
APIHighErrorRate
APIHighLatency
PostgresConnectionExhaustion
PostgresDeadlockSpike
RedisMemoryCritical
CeleryWorkerMissing
CeleryQueueBacklog
OutboxStalled
KlyrowDeliveryFailure
TelnexaDLRFailure
OdooProjectionBacklog
DiskLow
TLSExpiry
BlackboxEndpointDown
KeycloakLoginFailureSpike
```

---

# MILESTONE 23 — BUSINESS ANALYTICS / SUPERSET

Operational telemetry and business analytics must remain separate.

Correct flow:

```text
BREERO business events
Klyrow business events
Telnexa business events
Odoo business data
Middleware events
       ↓
Analytics ingestion
       ↓
Warehouse / reporting database
       ↓
Superset
```

## BREERO KPIs

Include:

```text
GMV
revenue
platform take rate
project requests
booking count
booking conversion
quote conversion
job completion
cancellation
repeat-customer rate
provider activation
provider retention
lead conversion
service-category demand
geographic demand
average order value
time-to-match
time-to-provider-response
time-to-booking
time-to-completion
refund rate
support rate
review score
```

## Klyrow KPIs

```text
sent
delivered
opened
clicked
bounced
complaints
unsubscribe
tenant usage
campaign performance
revenue
```

## Telnexa KPIs

```text
submitted
delivered
failed
DLR performance
carrier performance
tenant usage
cost
revenue
margin
```

---

# MILESTONE 24 — API GATEWAY AND EDGE

## Caddy

Own:

* TLS
* certificate automation
* host routing
* reverse proxy
* approved service exposure

## Kong

Own:

* API policies
* authentication enforcement
* consumer policies
* rate limiting
* quota
* API keys
* OIDC/JWT
* API version routing
* transformations
* upstream policy

Avoid duplicated policy between Caddy and Kong.

Canonical direction:

```text
Internet
↓
WAF/CDN
↓
Caddy
↓
Kong
↓
Application APIs
```

---

# MILESTONE 25 — PRIVACY AND DATA GOVERNANCE

Classify data:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Define retention for:

* customer data
* provider data
* worker data
* communications
* job evidence
* financial records
* logs
* traces
* metrics
* support cases
* reviews

Implement:

* data export
* deletion requests
* retention jobs
* audit
* legal hold where needed
* consent history
* communication preferences

PII should not be copied to telemetry unnecessarily.

---

# MILESTONE 26 — AI AND 2026 INTELLIGENCE FEATURES

AI is advisory.

AI is not marketplace authority.

## Allowed AI use

* project-description clarification
* service classification
* missing-information detection
* scope summarization
* quote comparison
* support copilot
* operations summarization
* matching explanation
* fraud/anomaly triage
* review moderation assistance
* demand forecasting
* provider capacity forecasting
* natural-language analytics query

## AI may not independently

* approve provider
* verify license
* verify insurance
* create coverage
* create capacity
* promise a price
* accept quote
* assign provider
* confirm booking
* approve change order
* authorize refund
* authorize payout
* expose private data
* activate feature flags

AI results must pass deterministic business validation.

Store only approved metadata under retention/redaction policy.

---

# MILESTONE 27 — SECURITY HARDENING

Required:

* dependency scanning
* secret scanning
* container scanning
* SAST
* RBAC negative tests
* tenant isolation tests
* CSRF protection where applicable
* CSP/security headers
* rate limiting
* abuse protections
* webhook verification
* idempotency
* SSRF controls
* file malware scanning
* MIME/type validation
* signed download URLs
* secure cookies
* PKCE
* MFA for privileged users
* session revocation
* immutable audit
* restricted Docker access
* private data-plane networking

No high/critical unresolved issue at release unless explicitly risk-accepted through governance.

---

# MILESTONE 28 — TESTING PROGRAM

## Backend

Run:

```text
ruff
mypy
compileall
pytest
PostgreSQL integration tests
PostGIS integration tests
migration tests
concurrency tests
idempotency tests
authorization tests
tenant isolation tests
outbox/inbox tests
provider-event tests
```

## Frontend

Run:

```text
lint
typecheck
unit tests
component tests
accessibility tests
production build
Playwright Chromium
Playwright Firefox
Playwright WebKit
responsive viewports
```

## Integration tests

Required scenarios:

```text
customer request
provider qualification
provider matching
provider opportunity
lead connection
quote
quote acceptance
capacity reservation
booking
manual assignment
job completion
email
SMS
payment
review
Odoo projection
```

## Failure tests

Required:

```text
zero providers
expired compliance
suspended provider
cross-tenant request
duplicate request
duplicate webhook
duplicate event
worker crash
lease expiry
Redis restart
database timeout
Klyrow outage
Telnexa outage
Middleware outage
Odoo outage
payment timeout
DLR timeout
expired hold
race for last slot
```

---

# MILESTONE 29 — PERFORMANCE AND SCALE

Create realistic load profiles.

Test:

* catalog
* address validation
* request submission
* availability
* matching
* booking
* provider dashboard
* dispatch board
* job commands
* customer history
* outbox
* inbound provider callbacks

Track:

```text
p50
p95
p99
throughput
DB query count
DB lock wait
Redis latency
worker queue delay
CPU
memory
connection pools
```

Optimize verified bottlenecks.

Do not prematurely split the modular monolith into microservices.

Extract services only when operational or scaling evidence justifies it.

---

# MILESTONE 30 — ISOLATED STAGING

Create staging completely separate from production.

Staging needs its own:

* PostgreSQL/PostGIS
* Redis
* API
* workers
* scheduler
* frontend
* Keycloak clients
* OpenBao paths
* DNS/TLS
* Klyrow safe account/recipients
* Telnexa sandbox routes
* Stripe test account
* Odoo test/sandbox projection
* synthetic users
* synthetic providers
* synthetic workers

## Personas

At minimum:

```text
customer
provider owner
provider admin
worker
dispatcher
support
trust
finance
platform admin
superadmin
```

## Staging proof

* clean database migration
* restored database migration
* backup/restore
* customer E2E
* provider E2E
* worker E2E
* ops E2E
* admin E2E
* role denial
* tenant denial
* integration failure recovery
* rollback
* load test
* observability

---

# MILESTONE 31 — PRODUCTION ACTIVATION

Production is the final milestone.

Not an implementation environment.

## Preflight

Require:

```text
FINAL_MAIN_SHA
REQUIRED_CHECKS=PASS
INDEPENDENT_REVIEW=PASS
UNRESOLVED_THREADS=0
BACKUP=VERIFIED
RESTORE_TEST=PASS
MIGRATION_REHEARSAL=PASS
STAGING_UAT=PASS
SECURITY_GATE=PASS
OBSERVABILITY_GATE=PASS
ROLLBACK=PROVEN
```

## Cutover

```text
1. Freeze target SHA.

2. Build immutable artifacts.

3. Record image digests.

4. Verify SBOM/provenance.

5. Capture pre-change infrastructure evidence.

6. Take verified database backup.

7. Confirm rollback artifacts.

8. Run one-shot migrations.

9. Verify Alembic current == expected head.

10. Start backend.

11. Verify readiness.

12. Start worker/scheduler.

13. Verify heartbeat and queue.

14. Start frontend.

15. Verify Caddy/Kong routing.

16. Verify Keycloak authentication.

17. Verify API authorization.

18. Run private synthetic transactions.

19. Run canary.

20. Monitor abort thresholds.

21. Route production traffic.

22. Continue enhanced monitoring.

23. Preserve previous release.

24. Record final release evidence.
```

---

# 7. CAPABILITY ACTIVATION MATRIX

Implementation and activation are different changes.

Keep these dark by default until individually certified:

```text
PAYMENTS_ENABLED=false
PAYOUTS_ENABLED=false
PAID_LEADS_ENABLED=false
FEATURED_PROVIDERS_ENABLED=false
AUTO_ASSIGN_PROVIDER=false
AUTO_CONFIRM_BOOKING=false
MESSAGING_ENABLED=false
REVIEWS_ENABLED=false
LIVE_EMAIL_DELIVERY=false
LIVE_SMS_DELIVERY=false
MARKETING_ENABLED=false
AI_AUTOMATION_ENABLED=false
```

Each activation requires:

* code already merged
* staging evidence
* tests
* monitoring
* rollback
* independent approval
* production change record

---

# 8. SLO PROGRAM

Initial targets should be documented and tuned from real usage.

Recommended starting objectives:

### API

```text
Availability: ≥99.9%
p95 read latency: <500 ms for normal API calls
p95 mutation latency: <1 s excluding external provider delay
5xx rate: <1%
```

### Marketplace workflow

```text
request persistence success: >99.95%
outbox event creation: same transaction as domain mutation
matching processing success: >99.9%
```

### Communications

```text
accepted notification retained durably: 100%
provider outage must not lose event
delivery state eventually reconciled
```

### Workers

```text
heartbeat continuously monitored
stale worker alert
oldest outbox age alert
queue backlog alert
```

---

# 9. BRANCH PROGRAM

Use these branch families.

```text
architecture/current-state-inventory

release/production-safety

be/identity-tenancy-rbac
be/api-v2-governance

be/project-requests
be/provider-network
be/provider-compliance
be/scheduling-capacity
be/provider-matching
be/opportunities-leads
be/conversations-quotes
be/booking-dispatch-jobs

integration/shared-event-envelope
integration/middleware-control-plane
integration/klyrow-email
integration/telnexa-sms
integration/odoo-projection

be/payments-ledger
be/provider-earnings-payouts
be/reviews-reputation
be/support-trust

fe/customer-marketplace
fe/provider-portal
fe/worker-portal
fe/operations-portal
fe/admin-portal

obs/breero-opentelemetry
obs/breero-prometheus
obs/breero-grafana
obs/breero-alerting

analytics/breero-superset

be/privacy-retention
be/ai-project-assistant

ci/security-performance
release/isolated-staging
release/production-candidate
```

Do not begin dependent phases before required foundations are accepted unless explicitly authorized.

---

# 10. DEFINITION OF DONE FOR EVERY FEATURE

A feature is not done because an endpoint exists.

Complete means:

```text
domain model
state machine
permissions
tenant policy
capability guard
idempotency
concurrency/versioning
audit
history
outbox effect
inbox effect when needed
failure states
retry behavior
reconciliation behavior
OpenAPI
typed client
frontend
positive tests
negative tests
observability
runbook
rollback/forward-fix boundary
```

---

# 11. PER-PR CODEX COMPLETION REPORT

After every PR, report exactly:

```text
REPOSITORY:
BRANCH:

STARTING_MAIN_SHA:
FINAL_HEAD_SHA:

COMMITS:

CHANGED_FILES:

DOMAIN:
STATE_MACHINE_CHANGE:

MIGRATIONS:
ALEMBIC_BEFORE:
ALEMBIC_AFTER:

API_CHANGE:
OPENAPI_CHANGE:
OPENAPI_DIGEST:

FRONTEND_CONTRACT_CHANGE:

AUTH_CHANGE:
TENANCY_CHANGE:
PERMISSIONS_CHANGE:

CAPABILITIES_CHANGED:

EVENTS_ADDED:
OUTBOX_CHANGE:
INBOX_CHANGE:

INTEGRATIONS_CHANGED:

OBSERVABILITY_CHANGE:
METRICS_ADDED:
LOGGING_CHANGE:
TRACING_CHANGE:
ALERTS_ADDED:

TESTS:
BACKEND_TESTS:
POSTGRES_TESTS:
POSTGIS_TESTS:
FRONTEND_TESTS:
E2E_TESTS:
SECURITY_TESTS:
CONCURRENCY_TESTS:

WORKFLOW_RUNS:

DEPENDENCY_SCAN:
SECRET_SCAN:
IMAGE_SCAN:

REVIEW_STATE:
UNRESOLVED_THREADS:

DEPLOYMENT_PERFORMED:

PRODUCTION_CAPABILITY_ACTIVATED:

ROLLBACK_PLAN:

BLOCKERS:

NEXT_DEPENDENCY:
NEXT_BRANCH:
```

---

# 12. CODEX STOP CONDITIONS

Codex must stop rather than bypass controls when any required condition is unavailable.

Examples:

```text
independent reviewer unavailable
branch protection failure
unresolved security finding
staging unavailable
backup not verified
database migration uncertain
OpenBao authority unavailable
production credential unavailable
required external sandbox unavailable
release checks failing
production authorization missing
```

Never disable governance controls merely to finish the mission.

Never describe partial implementation as live.

---

# 13. FINAL PLATFORM TARGET

The completed Codestra architecture should look conceptually like:

```text
                             CUSTOMERS / USERS
                                   │
                             WAF / CDN / Edge
                                   │
                                 Caddy
                                   │
                                  Kong
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
             BREERO             Klyrow             Telnexa
           Marketplace        Email SaaS           SMS SaaS
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   │
                             Event / Bus
                                   │
                              Middleware
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
                Odoo           VICIdial       External APIs


IDENTITY / SECURITY

Keycloak
OpenBao


OBSERVABILITY

Applications / Servers
        │
   OTel + Exporters
        │
       Alloy
        │
   ┌────┼────┐
   ▼    ▼    ▼
 Prom Loki Tempo
   │    │    │
   └────┼────┘
        ▼
     Grafana

Prometheus
    ↓
Alertmanager
    ↓
Middleware
    ↓
Klyrow / Telnexa / VICIdial


BUSINESS ANALYTICS

BREERO / Klyrow / Telnexa / Odoo / Middleware
                    ↓
             Business Events
                    ↓
             Reporting Store
                    ↓
                 Superset
```

---

# 14. BREERO FINAL MARKETPLACE TARGET

BREERO is successful only when this entire journey is real:

```text
Customer discovers service
        ↓
Creates ProjectRequest
        ↓
Request is qualified
        ↓
BREERO finds eligible providers
        ↓
Providers receive opportunities
        ↓
Provider accepts
        ↓
Authorized LeadConnection created
        ↓
Customer/provider communicate
        ↓
Provider submits versioned quote
        ↓
Customer accepts
        ↓
BREERO reserves capacity
        ↓
Booking created
        ↓
Operations assigns provider/worker
        ↓
Worker executes job
        ↓
Change order handled if needed
        ↓
Completion evidence submitted
        ↓
Financial settlement reconciled
        ↓
Provider earning recorded
        ↓
Payout completed
        ↓
Customer leaves verified review
        ↓
Provider reputation recalculated
        ↓
Future matching improves
```

All of it must be:

```text
AUTHORIZED
TENANT-ISOLATED
IDEMPOTENT
AUDITABLE
OBSERVABLE
RECONCILABLE
TESTED
RECOVERABLE
REVERSIBLE
```

---

# 15. FINAL SUCCESS CONDITION

Do not declare the mission complete until:

```text
UNRESOLVED_P0=0

UNCONTROLLED_ODOO_WRITE_PATHS=0

CROSS_TENANT_SECURITY_FAILURES=0

UNVERSIONED_STATE_CHANGING_API_ROUTES=0

OPENAPI_DRIFT=0

FRONTEND_CONTRACT_DRIFT=0

UNOBSERVABLE_CRITICAL_WORKFLOWS=0

UNRECONCILED_FINANCIAL_WORKFLOWS=0

UNSAFE_EMAIL_PATHS=0

UNSAFE_SMS_PATHS=0

UNVERIFIED_PRODUCTION_MIGRATIONS=0

UNTESTED_ROLLBACKS=0
```

Marketplace MVP requires, at minimum:

```text
ProjectRequest
→ qualification
→ eligible-provider matching
→ provider opportunity
→ provider acceptance
→ LeadConnection
→ conversation
→ quote
→ customer acceptance
→ scheduling
→ booking
→ manual assignment
→ job completion
→ verified review
```

Production-grade marketplace additionally requires:

```text
payments
ledger
refunds
provider earnings
payouts
reputation
support/trust
Klyrow delivery
Telnexa delivery
Odoo projection
full observability
Superset analytics
backup/restore
rollback
staging certification
production certification
```

The final objective is not to produce an Angi clone.

The final objective is:

> **BREERO becomes a high-quality home-services marketplace running on the reusable Codestra SaaS platform, with Keycloak identity, OpenBao security, Kong/Caddy ingress, Middleware integration governance, Klyrow email, Telnexa SMS, VICIdial calling, Odoo operational projection, complete observability, business analytics, and independently controlled production activation.**
