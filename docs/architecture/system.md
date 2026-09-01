# BREERO System Architecture

## Surfaces

- `breero.com` — public marketplace + customer account
- `partners.breero.com` — vendor/technician portal
- `ops.breero.com` — dispatch and operations
- `admin.breero.com` — admin and finance
- `api.breero.com/api/v1` — FastAPI backend

## Backend stack

FastAPI + PostgreSQL/PostGIS + SQLAlchemy async + Psycopg 3 + Alembic + Redis + Celery.

## Required layering

`router -> service -> repository -> SQLAlchemy -> PostgreSQL`

Pydantic API contracts are separate from SQLAlchemy persistence models.

A router resolves the caller, validates the request, and delegates. It does not build
queries and does not import ORM models to query them. Persistence belongs to a
domain's repository; orchestration belongs to its service.

### How this is enforced

Two checks run in the backend quality gate. Neither is advisory.

`apps/api/.importlinter` holds the structural contracts, verified by `lint-imports`:
the HTTP layer sits above domains, which sit above persistence; workers, integration
adapters, and configuration must not import the HTTP layer. All four contracts are
currently kept, so a failure means a genuinely new dependency direction.

`apps/api/scripts/check_layering.py` holds the router rule. Import Linter cannot
express it, because it squashes external packages and so cannot tell
`sqlalchemy.ext.asyncio` -- the `AsyncSession` annotation every router needs for
`Depends(get_db)` -- apart from the query constructors that belong in a repository.
The checker draws that line and freezes today's violations into
`scripts/layering_baseline.txt`.

That baseline may only shrink. Adding a violation fails the gate; so does leaving a
baseline entry in place after its violation is fixed. Migrating a domain therefore
means moving its queries into a repository and running:

```bash
python scripts/check_layering.py --update
```

Two exceptions are deliberate and encoded in the checker:

- `sqlalchemy.ext.asyncio` and `sqlalchemy.exc` are allowed in routers. Neither builds
  a query; the first annotates the injected session, the second lets a router turn an
  integrity error into an HTTP response.
- `app.domains.auth.models` is exempt. `current_user` resolves to a `User` entity, so
  every guarded router must import it to annotate the dependency. That is forced by the
  auth design rather than by a router reaching into persistence, and changing it is a
  separate refactor.

Domains still carrying router-level persistence are listed in the baseline. `catalog`,
`booking_intents`, `geography`, `provider_catalog`, and `tenant_email` are migrated.

## Core domains

Auth, users, customers, addresses, legal entities, service areas, services/questions, scheduling, bookings, vendors/workers, jobs, matching, dispatch, pricing, quotes, payments, earnings, payouts, notifications, audit and integrations.

## Transactional source of truth

BREERO PostgreSQL is the operational source of truth. Odoo is synchronized asynchronously through integration events/outbox processing.

## Payment truth

Stripe webhook events, after signature and idempotency verification, are authoritative for payment completion. Browser redirects are never authoritative.

## State control

Bookings and jobs use explicit domain transitions. Partner users receive command endpoints such as `/jobs/{id}/complete`, never unrestricted status patching.

## Security

Server-side RBAC/permissions, audit logging, webhook verification, idempotency, secret isolation, secure headers, CORS policy and rate limiting are required.

## Production

Backend deployment target: `49.12.145.107`.

Production topology: reverse proxy/TLS -> API -> PostgreSQL/PostGIS + Redis + workers/scheduler. Frontends remain independently deployable.
