# Current BREERO system

Source baseline: protected `main` at `c8b5d31df80cd715ae189db9e16d6ff082c0d51f`, captured 2026-09-13. Executable accepted code takes precedence over prior plans and unmerged branches. This inventory advances Milestone 0; it does not certify any feature or production environment.

## Required initial record

| Field | Observed state |
|---|---|
| REPOSITORY | `appolon1908-hue/Breero.com` |
| DEFAULT_BRANCH | `main` |
| CURRENT_MAIN_SHA | `c8b5d31df80cd715ae189db9e16d6ff082c0d51f` |
| CURRENT_ALEMBIC_HEAD | `022_provider_services_skills`, one source head; deployed database revision unverified |
| CURRENT_OPENAPI_DIGEST | `93748567a1121ee3d8312d08e5d19ea4a81b14e0184e03d0f0eeaba957384ba4`; SHA-256 of checked-in bytes |
| CURRENT_FRONTEND_CONTRACT_STATE | Default runtime OpenAPI equals checked-in artifact; partial frontend checker passes 30 required paths; shared types/client remain handwritten; portal fetches bypass them |
| OPEN_PULL_REQUESTS | 42; full branch/base list below and in [GitHub snapshot](GITHUB_BASELINE.json) |
| OPEN_P0_ISSUES | #120, #119, #61, #53, #52, #51, #50, #49 |
| OPEN_P1_ISSUES | #83, #81, #78, #77, #76, #75, #74, #73, #19, #18, #17 |
| CURRENT_CAPABILITY_DEFAULTS | [Capability registry](CAPABILITY_REGISTRY.md); source defaults only; legacy delivery and payout task gaps are explicit |
| CURRENT_PRODUCTION_TOPOLOGY | Competing root and deploy/production Compose definitions; private data-plane definitions; actual host state unverified |
| CURRENT_STAGING_TOPOLOGY | Separate named networks/volumes in deploy/staging; actual isolation, sandbox bindings and certification unverified |
| CURRENT_KEYCLOAK_CONFIGURATION | Canonical issuer in production example; optional backend validation and web PKCE implementation; no live realm/client export inspected |
| CURRENT_KLYROW_INTEGRATION | No named Klyrow adapter/callback contract; legacy direct email exists |
| CURRENT_TELNEXA_INTEGRATION | SMS interface, fake/unconfigured gateways and templates; no implemented MT/DLR/MO integration |
| CURRENT_MIDDLEWARE_INTEGRATION | HMAC-V2 plus TLS client authentication, four allowlisted event types, disabled by default |
| CURRENT_ODOO_INTEGRATION | Startup rejects direct Odoo enablement/credentials in every environment; legacy adapter retained; mounted internal routes read/retry the BREERO outbox |
| CURRENT_OBSERVABILITY_STATE | Accepted Prometheus metrics, structured logs, optional OTel instrumentation and collector overlays; runtime pipeline and business coverage unverified |

Priority lists above use explicit `[P0]`/`[P1]` issue titles. Unlabelled mission issues are not silently assigned a priority. GitHub state is a timestamped snapshot, not a permanent assertion that those PRs/issues remain open.

## Inventory method and boundaries

[Source inventory](SOURCE_INVENTORY.json) contains every Python module under `apps/api/app`, model/table and enum declarations, migration graph, frontend page/handler, adapter, worker task, deployment-file digest, feature default, and API operation. [Inventory generator](../../scripts/architecture/inventory.py) reads source and imports runtime routes in clean test subprocesses with empty working directories. It does not start request handlers, workers, application lifespan, migrations, providers or exporters. Two profiles enumerate default routes and all currently conditionally mounted route families; this is not a capability activation.

The required directories exist except `infrastructure`, which is absent. There are four Next.js applications (`web`, `partner`, `ops`, `admin`) and one FastAPI application, plus shared `ui`, `types`, `api-client`, and `portal` packages. There is no separate worker frontend application. The architecture remains a FastAPI modular monolith with async SQLAlchemy, Psycopg, PostgreSQL/PostGIS, Alembic, Redis and Celery.

Classification: `COMPLETE` requires the mission's feature acceptance evidence; `PARTIAL` means executable foundations with unmet requirements; `STUB` means placeholder/interface only; `DARK` identifies an implemented path guarded from activation; `DEPRECATED` means retained legacy behavior; `NOT_IMPLEMENTED` means no executable domain found. A disabled flag alone does not establish that all underlying work is dark. No complete marketplace feature or live certification is asserted here.

## Backend domain inventory

| Directory under apps/api/app/domains | State | Executable foundation and remaining scope |
|---|---|---|
| `auth` | PARTIAL | Users, sessions, external identity links, tenants, memberships and access assignments; optional Keycloak; full server principal, machine boundary and required negative matrix not certified |
| `booking` | PARTIAL | Booking records, state transitions, availability and locking; request-first manual-scheduling behavior exists; complete capacity policy, evidence and performance certification remain |
| `booking_intents` | PARTIAL | Draft/update/abandon/submit with ownership and optimistic versioning; submit delegates to BookingService; not the separate ProjectRequest lifecycle |
| `capabilities` | PARTIAL | V1/V2 public projections of effective flags; mission naming and universal delivery/task enforcement incomplete |
| `catalog` | PARTIAL | Active service/detail/questions, administrative service writes; full product-mode and service qualification closure not certified |
| `common` | PARTIAL | Command context, state helpers, audit, immutable event value object, transactional outbox, claims, leases, retries and replay; uniform adoption and durable inbox missing |
| `compliance` | PARTIAL | Privacy requests, consent events, suppressions and preferences; no completed retention/export/deletion/legal-hold pipeline; provider credentials live in workforce |
| `dispatch` | PARTIAL | Worker candidates, dispatch offers, assignments and decisions; not separate MatchingRun/Opportunity/LeadConnection objects |
| `finance` | PARTIAL | Earnings, ledger, payouts and batch state; scheduled release/batch work is not protected by payout flag; balance reconstruction and settlement certification remain |
| `geography` | PARTIAL | Postal and zone models, PostGIS queries, address/timezone/coverage APIs; public geocoding routes default dark; full address-failure and DST/performance certification remain |
| `jobs` | PARTIAL | Jobs, job events and work requests; customer work-request decisions plus worker/operations commands; full immutable quote/evidence/change-order loop absent |
| `payments` | PARTIAL | Stripe intent, verified webhook/refund foundations; public payment routes dark; settlement, dispute and timeout certification remain |
| `professional_leads` | PARTIAL | ProfessionalLead, purchase and dispute models; paid routes dark; neither an Opportunity nor an authorized LeadConnection replacement |
| `provider_catalog` | PARTIAL | Provider services/skills and approval records, permissions, ownership and version checks; qualification-to-matching integration remains |
| `public_submissions` | PARTIAL | Durable service/contact/provider-interest submissions and downstream state; no separate ProjectRequest qualification state machine |
| `workforce` | PARTIAL | Vendors, workers, working rules, credentials, applications and onboarding; complete membership/compliance/capacity acceptance remains |

Required concepts outside these directories:

| Capability | State | Evidence/gap |
|---|---|---|
| ProjectRequest qualification | NOT_IMPLEMENTED | PublicSubmission and BookingIntent exist with different semantics |
| Explainable MatchingRun | NOT_IMPLEMENTED | Existing dispatch candidate selection is a foundation |
| Opportunity and LeadConnection | NOT_IMPLEMENTED | Must remain distinct from DispatchOffer and paid ProfessionalLead |
| Authorized conversations | NOT_IMPLEMENTED | Messaging flag/projection only |
| Immutable quote versions and full change orders | PARTIAL | Customer quote views use work requests; no complete immutable quote-version domain |
| Verified reviews/reputation | NOT_IMPLEMENTED | Review flag/projection only |
| Support/trust cases | PARTIAL | LeadDispute is a limited paid-lead slice; general case/evidence/visibility/escalation domain absent |
| Analytics/Superset | NOT_IMPLEMENTED | No reporting store or certified ingestion pipeline |
| Advisory AI | NOT_IMPLEMENTED | No advisory AI domain found |
| Secure document pipeline | NOT_IMPLEMENTED | Credential/evidence references do not establish malware scanning or signed-download authority |

## Workers and stores

| Celery task | Beat interval | Behavior and remaining requirement |
|---|---:|---|
| `app.workers.tasks.publish_outbox` | 10 s | Claims/leases/retry exist; only public-submission CRM events are parked/reactivated by Middleware switch; notification and unknown-event semantics need repair |
| `app.workers.tasks.expire_bookings` | 60 s | Locks and expires eligible booking holds; existing integration test; full mission capacity lifecycle remains |
| `app.workers.tasks.release_earnings` | 3600 s | Scheduled unconditionally; mutates earning eligibility without checking PAYOUT_ENABLED |
| `app.workers.tasks.generate_weekly_payout_candidates` | 604800 s | Scheduled unconditionally; create_batch changes earnings to BATCHED without checking PAYOUT_ENABLED |

[Worker configuration](../../apps/api/app/workers/celery_app.py) sends heartbeat/task events and writes a shared Redis worker timestamp. [Tasks](../../apps/api/app/workers/tasks.py) use `asyncio.run` over the shared session factory; PR #105 proposes loop isolation. Heartbeat is aggregate worker liveness, not proof that each worker or beat is healthy. No scheduler heartbeat exists in this baseline.

| Store | Current purpose | Boundary |
|---|---|---|
| PostgreSQL/PostGIS | All marketplace records, audit, outbox, spatial data | Transactional authority; source migration head is not deployed revision |
| Redis | Rate limiting, Celery broker/results and worker heartbeat | Operational state; no dedicated approved business-event broker established |
| Odoo database | External CRM projection/add-on models | No BREERO-owned database deployment; Middleware owns production writes |
| OpenBao | External secrets authority with local file consumer contract | Workload identity/rotation runtime unverified |
| Object/reporting/inbox stores | No authoritative implementation found | Central documents, analytics and durable inbox remain required |

## Production and staging topology

| Definition | Source evidence | Gap |
|---|---|---|
| `docker-compose.yml` | Development builds; publishes API/Postgres/Redis ports; runs migration inside API startup | Development only; cannot serve as production authority |
| `docker-compose.production.yml` | API, worker, scheduler, migration job, PostGIS, Redis; read-only services, limits, log rotation, private network and external Caddy network | Competes with deploy/production stack; API image variable requests digest but does not validate it here |
| `deploy/production/docker-compose.backend.yml` | API, worker, migration job, private PostGIS/Redis, separate edge/private networks, injected secrets | No scheduler service; worker health disabled; lacks root stack limits and API Compose healthcheck |
| `deploy/staging/docker-compose.backend.yml` | Separate environment references, names, networks and volumes | No scheduler service; worker health disabled; deployed isolation/sandboxes unverified |
| `deploy/frontend`, `deploy/portals` | Public app and portal container definitions | End-to-end routing/auth/release certification unverified |
| `deploy/observability` | API metrics scrape, Alloy and OTLP collector overlay | Configuration is not proof of live Prometheus/Loki/Tempo ingestion |

All deployment definition digests are in SOURCE_INVENTORY.json. Production/staging data services have no published host ports in their reviewed definitions; actual host bindings, disk capacity, backups, restore rehearsal and Caddy/Kong/WAF routing were not inspected or asserted. Reconcile authority through PR #101 before release. Source ports in the development stack must not be mistaken for production evidence.

Accepted `.github/workflows/release-images.yml` builds only exact current main candidates, emits digests and enables SBOM/provenance/attestation. Release intent and orchestrator contract workflows exist. No candidate was built or deployed for this inventory. Full config/capability/migration/rollback manifests and restored-database rehearsal require release evidence, not assumptions based on workflow names.

## Identity, integration and observability

[Ownership](SYSTEM_OWNERSHIP.md), [integration](INTEGRATION_REGISTRY.md), [capabilities](CAPABILITY_REGISTRY.md), [API](API_REGISTRY.md) and [data handling](DATA_CLASSIFICATION.md) records describe the verified source boundaries. Current telemetry code is executable, not a placeholder: six custom metric families, safe route labels, structured logs with trace/span context, optional OTel FastAPI/SQLAlchemy/Redis/Celery instrumentation, outbox gauges and shared worker heartbeat exist. Tracing defaults off. No independent scheduler metric, full business metric matrix, certified alerts/dashboards, full Odoo/Klyrow/Telnexa trace or Superset pipeline is established here.

## Execution dependency and acceptance boundary

Milestone 0 acceptance is pending independent review of PR #128 at its final head and passing required checks. Branch rules require one approving review, approval of the last push, resolved threads, up-to-date required `quality` and `orchestrator-contract` checks, and squash merge. Do not claim acceptance before merge.

After acceptance, review P0 work in existing branches first: configuration validation (#99), readiness/dependency repair (#126; reconcile overlapping #124/#100), Compose authority (#101), identity authority (#102/#104/#108), worker lifecycle (#105/#107), public submissions (#55/#54) and API registry (#62/#63). Re-evaluate their current heads and dependency bases before adopting changes. PR #123 is a competing runtime reconciliation proposal, not accepted architecture. Add a focused release safety workstream for ungated email, unknown-event delivery, stale outbox finalization, finance task guards and scheduler heartbeat where existing PRs do not cover them.

Marketplace domain phases follow accepted identity/API/release foundations. Finance, live communication, messaging/reviews and automated assignment remain separate activation decisions. No deployment, external transport call, capability change, migration or Odoo write was performed by this baseline.

## All frontend routes

These are filesystem route entries, not acceptance claims about loading/error/accessibility or real-data completeness. Dynamic segments use Next.js notation. Portal apps each have one page and one health handler; customer/worker sections inside shared portal code are not separate Next.js routes.

| App | Kind | Route | Source |
|---|---|---|---|
| web | page | `/forgot-password` | [apps/web/app/(auth)/forgot-password/page.tsx](../../apps/web/app/(auth)/forgot-password/page.tsx) |
| web | page | `/login` | [apps/web/app/(auth)/login/page.tsx](../../apps/web/app/(auth)/login/page.tsx) |
| web | page | `/register` | [apps/web/app/(auth)/register/page.tsx](../../apps/web/app/(auth)/register/page.tsx) |
| web | page | `/reset-password` | [apps/web/app/(auth)/reset-password/page.tsx](../../apps/web/app/(auth)/reset-password/page.tsx) |
| web | page | `/verify-email` | [apps/web/app/(auth)/verify-email/page.tsx](../../apps/web/app/(auth)/verify-email/page.tsx) |
| web | page | `/about` | [apps/web/app/about/page.tsx](../../apps/web/app/about/page.tsx) |
| web | page | `/accessibility` | [apps/web/app/accessibility/page.tsx](../../apps/web/app/accessibility/page.tsx) |
| web | page | `/account/addresses` | [apps/web/app/account/addresses/page.tsx](../../apps/web/app/account/addresses/page.tsx) |
| web | page | `/account/bookings/[id]` | [apps/web/app/account/bookings/[id]/page.tsx](../../apps/web/app/account/bookings/[id]/page.tsx) |
| web | page | `/account/bookings` | [apps/web/app/account/bookings/page.tsx](../../apps/web/app/account/bookings/page.tsx) |
| web | page | `/account/callback` | [apps/web/app/account/callback/page.tsx](../../apps/web/app/account/callback/page.tsx) |
| web | page | `/account/forbidden` | [apps/web/app/account/forbidden/page.tsx](../../apps/web/app/account/forbidden/page.tsx) |
| web | page | `/account/forgot-password` | [apps/web/app/account/forgot-password/page.tsx](../../apps/web/app/account/forgot-password/page.tsx) |
| web | page | `/account/login` | [apps/web/app/account/login/page.tsx](../../apps/web/app/account/login/page.tsx) |
| web | page | `/account` | [apps/web/app/account/page.tsx](../../apps/web/app/account/page.tsx) |
| web | page | `/account/payments/[id]` | [apps/web/app/account/payments/[id]/page.tsx](../../apps/web/app/account/payments/[id]/page.tsx) |
| web | page | `/account/payments` | [apps/web/app/account/payments/page.tsx](../../apps/web/app/account/payments/page.tsx) |
| web | page | `/account/profile` | [apps/web/app/account/profile/page.tsx](../../apps/web/app/account/profile/page.tsx) |
| web | page | `/account/quotes/[id]` | [apps/web/app/account/quotes/[id]/page.tsx](../../apps/web/app/account/quotes/[id]/page.tsx) |
| web | page | `/account/quotes` | [apps/web/app/account/quotes/page.tsx](../../apps/web/app/account/quotes/page.tsx) |
| web | page | `/account/register` | [apps/web/app/account/register/page.tsx](../../apps/web/app/account/register/page.tsx) |
| web | page | `/account/reset-password` | [apps/web/app/account/reset-password/page.tsx](../../apps/web/app/account/reset-password/page.tsx) |
| web | page | `/account/session-expired` | [apps/web/app/account/session-expired/page.tsx](../../apps/web/app/account/session-expired/page.tsx) |
| web | page | `/account/unauthorized` | [apps/web/app/account/unauthorized/page.tsx](../../apps/web/app/account/unauthorized/page.tsx) |
| web | page | `/account/verify` | [apps/web/app/account/verify/page.tsx](../../apps/web/app/account/verify/page.tsx) |
| web | handler | `/api/addresses/validate` | [apps/web/app/api/addresses/validate/route.ts](../../apps/web/app/api/addresses/validate/route.ts) |
| web | handler | `/api/capabilities` | [apps/web/app/api/capabilities/route.ts](../../apps/web/app/api/capabilities/route.ts) |
| web | handler | `/api/communications/preferences` | [apps/web/app/api/communications/preferences/route.ts](../../apps/web/app/api/communications/preferences/route.ts) |
| web | handler | `/api/privacy-requests` | [apps/web/app/api/privacy-requests/route.ts](../../apps/web/app/api/privacy-requests/route.ts) |
| web | handler | `/api/public-submissions/[kind]` | [apps/web/app/api/public-submissions/[kind]/route.ts](../../apps/web/app/api/public-submissions/[kind]/route.ts) |
| web | handler | `/api/services` | [apps/web/app/api/services/route.ts](../../apps/web/app/api/services/route.ts) |
| web | page | `/availability` | [apps/web/app/availability/page.tsx](../../apps/web/app/availability/page.tsx) |
| web | page | `/blog` | [apps/web/app/blog/page.tsx](../../apps/web/app/blog/page.tsx) |
| web | page | `/book` | [apps/web/app/book/page.tsx](../../apps/web/app/book/page.tsx) |
| web | page | `/booking` | [apps/web/app/booking/page.tsx](../../apps/web/app/booking/page.tsx) |
| web | page | `/brand-preview` | [apps/web/app/brand-preview/page.tsx](../../apps/web/app/brand-preview/page.tsx) |
| web | page | `/cancellation-policy` | [apps/web/app/cancellation-policy/page.tsx](../../apps/web/app/cancellation-policy/page.tsx) |
| web | page | `/careers` | [apps/web/app/careers/page.tsx](../../apps/web/app/careers/page.tsx) |
| web | page | `/communications-preferences` | [apps/web/app/communications-preferences/page.tsx](../../apps/web/app/communications-preferences/page.tsx) |
| web | page | `/contact` | [apps/web/app/contact/page.tsx](../../apps/web/app/contact/page.tsx) |
| web | page | `/cookie-preferences` | [apps/web/app/cookie-preferences/page.tsx](../../apps/web/app/cookie-preferences/page.tsx) |
| web | page | `/cookies` | [apps/web/app/cookies/page.tsx](../../apps/web/app/cookies/page.tsx) |
| web | page | `/emergency` | [apps/web/app/emergency/page.tsx](../../apps/web/app/emergency/page.tsx) |
| web | page | `/faq` | [apps/web/app/faq/page.tsx](../../apps/web/app/faq/page.tsx) |
| web | handler | `/health` | [apps/web/app/health/route.ts](../../apps/web/app/health/route.ts) |
| web | page | `/help` | [apps/web/app/help/page.tsx](../../apps/web/app/help/page.tsx) |
| web | page | `/home-care` | [apps/web/app/home-care/page.tsx](../../apps/web/app/home-care/page.tsx) |
| web | page | `/how-it-works` | [apps/web/app/how-it-works/page.tsx](../../apps/web/app/how-it-works/page.tsx) |
| web | page | `/landing/[slug]` | [apps/web/app/landing/[slug]/page.tsx](../../apps/web/app/landing/[slug]/page.tsx) |
| web | page | `/lead-terms` | [apps/web/app/lead-terms/page.tsx](../../apps/web/app/lead-terms/page.tsx) |
| web | page | `/locations/[slug]` | [apps/web/app/locations/[slug]/page.tsx](../../apps/web/app/locations/[slug]/page.tsx) |
| web | page | `/locations` | [apps/web/app/locations/page.tsx](../../apps/web/app/locations/page.tsx) |
| web | page | `/` | [apps/web/app/page.tsx](../../apps/web/app/page.tsx) |
| web | page | `/partners` | [apps/web/app/partners/page.tsx](../../apps/web/app/partners/page.tsx) |
| web | page | `/press` | [apps/web/app/press/page.tsx](../../apps/web/app/press/page.tsx) |
| web | page | `/pricing` | [apps/web/app/pricing/page.tsx](../../apps/web/app/pricing/page.tsx) |
| web | page | `/privacy` | [apps/web/app/privacy/page.tsx](../../apps/web/app/privacy/page.tsx) |
| web | page | `/privacy-choices` | [apps/web/app/privacy-choices/page.tsx](../../apps/web/app/privacy-choices/page.tsx) |
| web | page | `/professional-lead-policy` | [apps/web/app/professional-lead-policy/page.tsx](../../apps/web/app/professional-lead-policy/page.tsx) |
| web | page | `/provider-terms` | [apps/web/app/provider-terms/page.tsx](../../apps/web/app/provider-terms/page.tsx) |
| web | page | `/refund-cancellation` | [apps/web/app/refund-cancellation/page.tsx](../../apps/web/app/refund-cancellation/page.tsx) |
| web | page | `/refund-policy` | [apps/web/app/refund-policy/page.tsx](../../apps/web/app/refund-policy/page.tsx) |
| web | page | `/request-service` | [apps/web/app/request-service/page.tsx](../../apps/web/app/request-service/page.tsx) |
| web | page | `/reviews` | [apps/web/app/reviews/page.tsx](../../apps/web/app/reviews/page.tsx) |
| web | page | `/service-fulfillment` | [apps/web/app/service-fulfillment/page.tsx](../../apps/web/app/service-fulfillment/page.tsx) |
| web | page | `/service-fulfillment-policy` | [apps/web/app/service-fulfillment-policy/page.tsx](../../apps/web/app/service-fulfillment-policy/page.tsx) |
| web | page | `/service-guarantee` | [apps/web/app/service-guarantee/page.tsx](../../apps/web/app/service-guarantee/page.tsx) |
| web | page | `/services/[slug]` | [apps/web/app/services/[slug]/page.tsx](../../apps/web/app/services/[slug]/page.tsx) |
| web | page | `/services` | [apps/web/app/services/page.tsx](../../apps/web/app/services/page.tsx) |
| web | page | `/sms-terms` | [apps/web/app/sms-terms/page.tsx](../../apps/web/app/sms-terms/page.tsx) |
| web | page | `/terms` | [apps/web/app/terms/page.tsx](../../apps/web/app/terms/page.tsx) |
| web | page | `/trust` | [apps/web/app/trust/page.tsx](../../apps/web/app/trust/page.tsx) |
| web | page | `/why-breero` | [apps/web/app/why-breero/page.tsx](../../apps/web/app/why-breero/page.tsx) |
| partner | handler | `/health` | [apps/partner/app/health/route.ts](../../apps/partner/app/health/route.ts) |
| partner | page | `/` | [apps/partner/app/page.tsx](../../apps/partner/app/page.tsx) |
| ops | handler | `/health` | [apps/ops/app/health/route.ts](../../apps/ops/app/health/route.ts) |
| ops | page | `/` | [apps/ops/app/page.tsx](../../apps/ops/app/page.tsx) |
| admin | handler | `/health` | [apps/admin/app/health/route.ts](../../apps/admin/app/health/route.ts) |
| admin | page | `/` | [apps/admin/app/page.tsx](../../apps/admin/app/page.tsx) |

## Open PR snapshot

| PR | Branch | Base | Workstream |
|---|---|---|---|
| [#128](https://github.com/appolon1908-hue/Breero.com/pull/128) | `architecture/current-state-inventory` | `main` | docs(architecture): establish current-system baseline |
| [#126](https://github.com/appolon1908-hue/Breero.com/pull/126) | `fix/api-cleanup-validation` | `main` | fix(api): bound readiness and repair dependency audit blockers |
| [#124](https://github.com/appolon1908-hue/Breero.com/pull/124) | `fix/documented-ready-endpoint-20260910` | `main` | fix(api): restore documented /ready endpoint |
| [#123](https://github.com/appolon1908-hue/Breero.com/pull/123) | `reconcile/live-runtime-v2-20260909` | `main` | reconcile: promote live Breero runtime into canonical repository |
| [#121](https://github.com/appolon1908-hue/Breero.com/pull/121) | `ops/manual-production-orchestrator-20260903` | `main` | release: add exact-head manual production intent contract |
| [#118](https://github.com/appolon1908-hue/Breero.com/pull/118) | `codex/codestra-orbit-v2-breero-com` | `main` | chore(orbit): register all Breero applications under one shell |
| [#117](https://github.com/appolon1908-hue/Breero.com/pull/117) | `feature/horizon-portfolio-shell-v1` | `main` | feat(ui): adopt Horizon portfolio shell |
| [#116](https://github.com/appolon1908-hue/Breero.com/pull/116) | `fe/ops-portal-production` | `fe/portal-runtime-foundation` | feat(ops): replace shell with governed operations workspace |
| [#115](https://github.com/appolon1908-hue/Breero.com/pull/115) | `fe/generated-openapi-contract` | `be/portal-read-models` | build(types): generate frontend contracts from canonical OpenAPI |
| [#114](https://github.com/appolon1908-hue/Breero.com/pull/114) | `ops/portal-production-release` | `fe/portal-runtime-foundation` | ops(portals): immutable release, certification, and rollback layer |
| [#113](https://github.com/appolon1908-hue/Breero.com/pull/113) | `fe/admin-portal-production` | `fe/portal-runtime-foundation` | feat(admin): production governance, finance, and platform control plane |
| [#112](https://github.com/appolon1908-hue/Breero.com/pull/112) | `fe/partner-portal-production` | `fe/portal-runtime-foundation` | feat(partner): production provider workspace for partners.breero.com |
| [#110](https://github.com/appolon1908-hue/Breero.com/pull/110) | `fe/portal-runtime-foundation` | `main` | feat(portals): secure Keycloak BFF runtime for partner, ops, and admin |
| [#109](https://github.com/appolon1908-hue/Breero.com/pull/109) | `be/portal-read-models` | `main` | feat(portals): scoped provider, operations, and admin read models |
| [#108](https://github.com/appolon1908-hue/Breero.com/pull/108) | `be/auth-rbac-request-context` | `be/auth-crypto-jwks-argon2` | fix(auth): resolve effective RBAC context once per request |
| [#107](https://github.com/appolon1908-hue/Breero.com/pull/107) | `be/runtime-resource-lifecycle` | `be/auth-crypto-jwks-argon2` | fix(runtime): own database and Redis pools through application lifespan |
| [#105](https://github.com/appolon1908-hue/Breero.com/pull/105) | `be/worker-async-engine-isolation` | `main` | fix(worker): isolate async database connections across Celery event loops |
| [#104](https://github.com/appolon1908-hue/Breero.com/pull/104) | `be/auth-crypto-jwks-argon2` | `main` | fix(auth): remove blocking password and JWKS work from request loop |
| [#102](https://github.com/appolon1908-hue/Breero.com/pull/102) | `security/keycloak-registration-recovery-20260829` | `main` | security(auth): lock Breero registration and recovery to Keycloak |
| [#101](https://github.com/appolon1908-hue/Breero.com/pull/101) | `infra/consolidate-production-compose` | `main` | infra(deploy): consolidate the two divergent production compose stacks |
| [#100](https://github.com/appolon1908-hue/Breero.com/pull/100) | `fix/dependabot-critical-vitest-postcss` | `main` | fix(deps): resolve all 9 open Dependabot alerts (8 critical, 1 medium) |
| [#99](https://github.com/appolon1908-hue/Breero.com/pull/99) | `fix/app-env-strict-validation-v2` | `main` | fix(config): reject any APP_ENV value outside a known, fixed set |
| [#89](https://github.com/appolon1908-hue/Breero.com/pull/89) | `docs/api-audit-repo-memory` | `main` | docs(api): add repository memory and prioritized API audit |
| [#72](https://github.com/appolon1908-hue/Breero.com/pull/72) | `integration/n8n-marketplace-automation-v2-20260827` | `main` | docs(integration): define governed marketplace automation |
| [#71](https://github.com/appolon1908-hue/Breero.com/pull/71) | `fe/tenant-email-compose-e2e` | `be/tenant-email-provisioning-outbox` | feat(email-ui): add tenant email provisioning and compose workspace |
| [#70](https://github.com/appolon1908-hue/Breero.com/pull/70) | `be/tenant-email-provisioning-outbox` | `main` | feat(email): add tenant provisioning, compose and durable outbox |
| [#69](https://github.com/appolon1908-hue/Breero.com/pull/69) | `fe/portal-login-department-dashboards` | `main` | feat(portal): complete role-aware dashboard interactions and access administration |
| [#67](https://github.com/appolon1908-hue/Breero.com/pull/67) | `fe/enterprise-design-governance` | `main` | feat(ui): enforce complete BREERO enterprise marketplace design system |
| [#65](https://github.com/appolon1908-hue/Breero.com/pull/65) | `ci/secure-deployment-preflight` | `main` | ci(deploy): add read-only secure deployment preflight |
| [#63](https://github.com/appolon1908-hue/Breero.com/pull/63) | `refactor/integration-adapter-boundaries` | `refactor/api-router-registry` | refactor(integrations): centralize provider-neutral adapter contracts |
| [#62](https://github.com/appolon1908-hue/Breero.com/pull/62) | `refactor/api-router-registry` | `main` | refactor(api): add fail-closed runtime endpoint policy registry |
| [#60](https://github.com/appolon1908-hue/Breero.com/pull/60) | `refactor/backend-configuration` | `main` | refactor(config): split settings validation into explicit modules |
| [#59](https://github.com/appolon1908-hue/Breero.com/pull/59) | `refactor/jobs-api-boundaries` | `main` | refactor(api): split jobs and work requests into clean modules |
| [#58](https://github.com/appolon1908-hue/Breero.com/pull/58) | `refactor/operations-api-boundaries` | `main` | refactor(api): split operations routes into clean resource modules |
| [#55](https://github.com/appolon1908-hue/Breero.com/pull/55) | `be/public-submissions-hardening` | `main` | fix(api): harden public submissions, consent and idempotency |
| [#54](https://github.com/appolon1908-hue/Breero.com/pull/54) | `fe/public-forms-cta-hardening` | `be/public-submissions-hardening` | feat(forms): harden public submissions and request-first CTAs |
| [#47](https://github.com/appolon1908-hue/Breero.com/pull/47) | `planning/breero-feature-api-forms-docker-program` | `main` | docs(codex): define complete branch-safe BREERO marketplace program |
| [#46](https://github.com/appolon1908-hue/Breero.com/pull/46) | `ci/docker-production-identity-hardening` | `main` | fix(docker): enforce canonical Keycloak issuer for frontend production |
| [#42](https://github.com/appolon1908-hue/Breero.com/pull/42) | `bootstrap/frontend-production-foundation` | `main` | docs(frontend): define target-state Marketplace V2 routes and safety |
| [#41](https://github.com/appolon1908-hue/Breero.com/pull/41) | `bootstrap/backend-production-foundation` | `main` | fix(tooling): make BREERO backend bootstrap fail closed and tested |
| [#40](https://github.com/appolon1908-hue/Breero.com/pull/40) | `docs/odoo-campaign-crm-authority` | `main` | docs(odoo): define Odoo 19 campaign CRM authority and safety gates |
| [#39](https://github.com/appolon1908-hue/Breero.com/pull/39) | `docs/marketplace-v2-p0-and-core-authority` | `main` | docs(marketplace-v2): harden production implementation authority |

## Reproduce

From the repository root, using Python 3.12 with `apps/api` development dependencies installed:

```sh
python scripts/architecture/inventory.py --check
python -m unittest discover -s scripts/architecture -p 'test_*.py' -v
node scripts/check-frontend-openapi.mjs
```

To refresh after an accepted source change, run `python scripts/architecture/inventory.py --source-sha <accepted-main-sha>` and review/update the six narrative registries and GitHub snapshot together. The Architecture baseline evidence workflow runs these inventory acceptance checks when baseline docs/tooling change. It validates an explicit checkpoint; it is not the later Milestone 3 permanent API policy/typed-client gate. Source collection does not automatically certify narrative claims or fetch GitHub. The baseline SHA identifies the inspected accepted source; the inventory PR itself changes only docs/tooling. Dependency versions are not locked by this inventory; a changed runtime contract must be investigated rather than silently accepted.
