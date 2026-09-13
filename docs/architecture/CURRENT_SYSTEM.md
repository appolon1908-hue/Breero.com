# Current BREERO system

Baseline captured from `main` at `a5fc9921cbd6b71f83f1660fc505f02316572256` on 2026-09-12. Executable code overrides older planning documents.

## Repository baseline

| Item | Observed state |
|---|---|
| Repository | `appolon1908-hue/Breero.com` |
| Default branch | `main` |
| Main SHA | `a5fc9921cbd6b71f83f1660fc505f02316572256` |
| Alembic source head | `022_provider_services_skills` (single head) |
| OpenAPI artifact | `apps/api/openapi.json`: 96 paths, 116 HTTP operations |
| OpenAPI SHA-256 | `93748567a1121ee3d8312d08e5d19ea4a81b14e0184e03d0f0eeaba957384ba4` |
| Frontend contract | Shared handwritten `packages/types` and `packages/api-client`; CI contract checker exists; no generated client is authoritative |
| Open P0 issues | #120, #119, #61, #53, #52, #51, #50, #49, #48, #37 |
| Open P1 issues | #83, #81, #78, #77, #76, #75, #74, #73, #19, #18, #17 |

Open pull requests existed at capture time, including #127, #126, #125, #124, #123 and #122. They are not part of this baseline until merged. PR #123 had a failing required backend check. Issue #119 records that protected merges are blocked without exact-head independent approval.

## Runtime topology in source

The repository is a modular monolith with five Next.js applications (`web`, `partner`, `ops`, `admin`, plus the FastAPI application), shared TypeScript packages, PostgreSQL/PostGIS, Redis, Celery worker/beat, and Alembic. Production and staging have separate Compose files under `deploy/production` and `deploy/staging`; they are definitions, not proof of deployed isolation. Production Caddy/Kong authority is external to this repository.

The production compose digest is `990f2401b9f96732bbe70fe7d401bbb5f160d9c54d060c8ec1931c884cc44c31`; staging is `f6ba973df764b4678aa309b6618ae976395c8980e3630ac19833ee60c19f2d38`. Both must be reconciled during Milestones 1 and 30.

## Backend domain inventory

`COMPLETE` means the repository contains a coherent executable slice, not that production certification has occurred.

| Domain | State | Evidence / principal gap |
|---|---|---|
| Common command context, state machine, audit base, outbox | PARTIAL | Reusable primitives exist; not every mutation proves use of every primitive |
| Authentication and local sessions | PARTIAL | Local auth is substantial; Keycloak is optional, not yet production-authoritative |
| Identity, tenancy and RBAC | PARTIAL | Models/services and migration 018 exist; required negative-test matrix is incomplete |
| Catalog and service questions | COMPLETE | Models, repository, service and V1 API exist |
| Geography and service zones | PARTIAL | PostGIS/service-zone code exists; address routes are conditional on geocoding |
| Booking intents | COMPLETE | Draft/submit API, persistence and migration 020 exist |
| Booking and scheduling | PARTIAL | Booking, availability and holds exist; comprehensive capacity/race certification remains |
| Workforce/provider organizations | PARTIAL | Vendor/worker base plus onboarding exist; full marketplace membership/compliance lifecycle remains |
| Provider catalog, services and skills | PARTIAL | Executable slice and migration 022 exist; qualification-to-matching closure remains |
| Compliance | PARTIAL | Credentials/compliance records exist; central secure document pipeline is incomplete |
| Dispatch and matching | PARTIAL | Manual operations and offer/assignment foundations exist; explainable MatchingRun model is absent |
| Jobs | PARTIAL | Explicit commands and job state exist; full evidence/change-order flow is absent |
| Professional leads | PARTIAL | Paid-lead domain exists behind flags; Opportunity and LeadConnection are not distinct complete domains |
| Conversations | NOT_IMPLEMENTED | No conversation domain/API |
| Quotes and change orders | PARTIAL | Customer quote reads/foundations exist; versioned quote and change-order lifecycles are incomplete |
| Payments | PARTIAL | Stripe intent/webhook/refund foundations exist and are dark by default |
| Finance, earnings and payouts | PARTIAL | Ledger/earnings/payout foundations exist; certification and complete reconciliation are absent |
| Reviews and reputation | NOT_IMPLEMENTED | Capability placeholder only |
| Support/trust and safety | NOT_IMPLEMENTED | No complete support/dispute/trust domain |
| Privacy/consent | PARTIAL | Consent/privacy request foundations exist; retention/export/deletion execution is incomplete |
| Analytics | STUB | Metrics/analytics concepts exist; no certified reporting-store/Superset pipeline here |
| AI assistance | NOT_IMPLEMENTED | No advisory AI domain |

## Frontend route inventory

The public/customer app includes `/`, auth and account flows, service discovery (`/services`, `/services/[slug]`), locations, booking/request flows, availability, customer bookings/quotes/payments/profile/addresses, communications preferences, privacy/cookie pages, help/trust/legal/marketing pages, and BFF routes for services, capabilities, address validation, public submissions, privacy requests, and communication preferences.

Each of `partner`, `ops`, and `admin` currently exposes a root portal route plus `/health`; their root pages use the shared `packages/portal` implementation. They are PARTIAL product surfaces rather than the complete route sets required by Milestone 19.

## Workers

| Task | Schedule | State |
|---|---:|---|
| `publish_outbox` | 10 seconds | PARTIAL; retries exist, durable inbox/DLQ/reconciliation are incomplete |
| `expire_bookings` | 60 seconds | COMPLETE for existing booking expiry semantics |
| `release_earnings` | hourly | PARTIAL; finance remains disabled/uncertified |
| `generate_weekly_payout_candidates` | weekly | PARTIAL/UNSAFE; it is scheduled unconditionally and mutates earning batch state without checking `PAYOUT_ENABLED` |

Celery uses Redis as broker and result backend. No explicit worker or scheduler heartbeat endpoint is present. The payout candidate task must be guarded or removed from the schedule before operators can rely on the payout kill switch.

## Data stores

PostgreSQL/PostGIS is transactional authority. Redis supplies rate limiting, Celery broker and result backend. The transactional outbox is stored in PostgreSQL. No warehouse/reporting database, durable integration inbox, object-storage authority, or dedicated broker is defined as an authoritative deployed component in this repository.

## Current identity and integration posture

The canonical desired issuer is `https://auth.codestra.co/realms/codestra`, but source defaults to `KEYCLOAK_ENABLED=false`; local JWT authentication therefore remains executable. OpenBao is represented only through file-based secret bindings; no proof of workload identity or live OpenBao policy is in this repository.

Middleware is optional and disabled by default. Direct Odoo is explicitly rejected for staging/production configuration, but a direct Odoo adapter and internal Odoo route remain in source for legacy/controlled use and require removal or strict proof of non-production reachability. Email and SMS adapters are local abstractions, with legacy SMTP/provider settings still present; they are not certified Klyrow/Telnexa end-to-end integrations.

## Observability posture

Structured request logs carry request and correlation IDs. Health/live/ready endpoints exist; readiness checks PostgreSQL schema and Redis. Application-level Prometheus exposition, OpenTelemetry traces, Alloy/Loki/Tempo wiring, marketplace metrics, alert rules, dashboards, and Superset ingestion are not complete in this repository. External Codestra observability repositories are dependencies and were not treated as merged BREERO code.

## Baseline conclusion

BREERO contains meaningful marketplace foundations, but the complete closed loop is not implemented or certified. No production deployment or capability activation is asserted by this document.
