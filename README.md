# BREERO

Home services. One booking.

BREERO is a multi-surface home-services marketplace and field-service orchestration platform.

## Repository layout

- `apps/api` — FastAPI backend (PostgreSQL/PostGIS, SQLAlchemy async, Psycopg 3, Alembic, Redis)
- `apps/web` — public marketplace and customer portal
- `apps/partner` — vendor and technician portal
- `apps/ops` — BREERO operations and dispatch portal
- `apps/admin` — administration and finance portal
- `packages/ui` — shared frontend design system
- `packages/types` — shared frontend contracts
- `packages/api-client` — typed frontend API client
- `infrastructure` — deployment, proxy, backups and monitoring
- `docs` — architecture, API, security, operations and Codex workstream documentation

## Backend architecture

`API router -> domain service -> repository/query -> SQLAlchemy -> PostgreSQL`

The first production vertical slice is:

`address validation -> services/questions -> availability -> guest booking -> pricing snapshot`

The second vertical slice is:

`Stripe webhook -> payment captured -> booking confirmed -> job -> vendor matching -> ops`

## Development

Copy `.env.example` to `.env`, then run:

```bash
docker compose up --build
```

API health: `http://localhost:8000/health`

API docs: `http://localhost:8000/docs`

## Production target

Backend host: `49.12.145.107`

Production secrets are never committed to this repository.

## Observability and analytics

The [observability stack contract](docs/observability-stack.md) defines the shared Codestra
collectors, telemetry stores, Alertmanager, Grafana, Superset and OpenBao responsibilities.
Middleware is the controlled bridge for all Odoo business writes. Architecture checks run
in CI; production telemetry coverage requires separate runtime evidence.
