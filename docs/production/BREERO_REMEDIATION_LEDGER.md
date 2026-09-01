# BREERO remediation ledger

Every row was verified against exact branch heads on `origin`, not against PR
descriptions or prior reports.

`INITIAL_MAIN_SHA=a5fc9921cbd6b71f83f1660fc505f02316572256`

Fix branch: `feat/observability-and-dr`, stacked on `chore/architecture-medium-findings`.

CI run IDs read `UNAVAILABLE` throughout. The GitHub API is unauthenticated in this
environment, so no workflow run can be read or attributed. That is a real gap in this
ledger, not a formatting choice.

## Fixed

| ID | Sev | Category | Component | Root cause | Remediation | Regression test | Fixing SHA | CI run | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE-01 | HIGH | Security / availability | `app/domains/auth/security.py` | PBKDF2 at 600k iterations ran inline in async handlers: 180 ms of GIL-held CPU per login, stalling every other request on that worker | Argon2id (43 ms) via the already-declared `pwdlib`, run through `run_in_threadpool`; legacy hashes upgraded in place on next successful login | Argon2id output, coroutine helpers, AST check that no app code calls the blocking variants, legacy verify | `f466bb7` | UNAVAILABLE | FIXED |
| BE-02 | HIGH | Availability | `app/domains/auth/security.py` | A `PyJWKClient` was built per request, so every authenticated call made a blocking HTTPS round trip to Keycloak with no timeout | One cached client per issuer, `cache_jwk_set` with a 300 s lifespan and 5 s timeout; verification moved off the event loop | client reuse, issuer change | `f466bb7` | UNAVAILABLE | FIXED |
| BE-03 | HIGH | Security | `app/domains/auth/security.py` | Hand-rolled HS256 verifier checked no issuer, audience or nbf | PyJWT with pinned algorithm, `iss`, `aud`, required claims | foreign issuer, foreign audience, `alg:none`, expiry | `f466bb7` | UNAVAILABLE | FIXED |
| BE-04 | HIGH | Correctness | `app/db/session.py`, `app/workers/tasks.py` | Celery tasks run under `asyncio.run`; pooled asyncio connections were handed to a dead event loop on the next run. Intermittent, so invisible in CI | Dedicated `NullPool` worker engine and sessionmaker | NullPool assertion; tasks never use the request-scoped sessionmaker | `f466bb7` | UNAVAILABLE | FIXED |
| OPS-01 | HIGH | Deployment | `deploy/production/docker-compose.backend.yml` | The CI-validated topology had no `beat` service while the root compose file did. Without it the outbox never drains and holds are never released, silently | `scheduler` added to production and staging | Any compose file running a Celery worker must also run beat | `f466bb7` | UNAVAILABLE | FIXED |
| OPS-02 | HIGH | Security | `apps/api/Dockerfile` | Default `CMD` omitted `--proxy-headers`, so any launch path not overriding it gave every caller the proxy address, collapsing the rate limiter into one bucket and poisoning audit IPs | Flags baked into the image default | Dockerfile `CMD` assertion | `f466bb7` | UNAVAILABLE | FIXED |
| QA-02 | MEDIUM | Test integrity | `tests/test_auth_lifecycle.py` | `assert verify_password(...)` was never awaited. An un-awaited coroutine is truthy, so the assertion passed regardless of the password | Switched to the explicit blocking helper | AST guard failing any un-awaited call to the async security helpers from a test | `f466bb7` | UNAVAILABLE | FIXED |
| BE-08 | MEDIUM | Architecture | `docs/architecture/system.md`, `app/api/*` | Documented layering was not the implemented layering: 13 routers build their own queries | Four Import Linter contracts plus a router-purity ratchet frozen at 36 violations that can only shrink; `tenant_email` migrated as the worked example | `test_layering_ratchet.py`, `.importlinter` | `14d26e9` | UNAVAILABLE | FIXED |
| BE-09 | MEDIUM | Architecture | `app/domains/common/` | `CommandContext`, `Money`, `DomainEvent` and `commands.py` were referenced only by their own test | Adopted the first three through the payments vertical; deleted `commands.py` | payments provenance, idempotency-key requirement, actor requirement | `14d26e9` | UNAVAILABLE | FIXED |
| BE-10 | MEDIUM | Operability | `app/main.py` | `EXPECTED_SCHEMA_REVISION` was a hand-edited literal; forgetting to bump it makes readiness 503 permanently | Derived from the Alembic script directory, failing loudly on a missing directory or split heads | `test_readiness_revision.py` | `14d26e9` | UNAVAILABLE | FIXED |
| QA-01 | MEDIUM | Quality gate | `pyproject.toml`, workflows | No coverage gate, no downgrade test, no first-party static analysis | `--cov-fail-under=60` against a measured 64.5; per-package frontend floors; a `head → -1 → head` migration drill; CodeQL for Python and TypeScript | coverage floors enforced in the gate | `14d26e9`, `d116a6f` | UNAVAILABLE | FIXED |
| FE-02 | MEDIUM | Maintainability | `apps/web`, `packages/*` | Single-line JSX, worst line 4,532 characters, no Prettier anywhere in the repository | Prettier at `printWidth: 100`; isolated reformat commit recorded in `.git-blame-ignore-revs`; `prettier --check` in `pnpm lint` | format check in the lint gate | `9028298` | UNAVAILABLE | FIXED |
| OPS-03 | MEDIUM | Disaster recovery | `scripts/backup/` | Production data lived in one Docker volume with no dump job, no off-host copy and no restore drill | Verified dumps: write-to-partial, read back with `pg_restore --list`, checksum, floor-protected retention; restore drill and a corrupt-dump rejection step in CI | CI restore drill, **not yet executed** | `21fee3f` | UNAVAILABLE | FIXED IN CODE, UNVERIFIED IN RUNTIME |
| OBS-01 | MEDIUM | Observability | `app/core/metrics.py` | `METRICS_ENABLED` defaulted true and gated nothing: no `/metrics`, no client, no tracing | Prometheus endpoint with route-template labels and multiprocess aggregation, domain gauges, scheduler heartbeat, OTel, nine promtool-validated alert rules | `test_observability.py`, 15 tests | `0bfc5c0` | UNAVAILABLE | FIXED, NOT RECONCILED — see OBS-02 |

## Withdrawn

| ID | Sev | Component | Reason | SHA |
| --- | --- | --- | --- | --- |
| FE-03 | HIGH | `packages/portal` | A portal runtime authored in this session held the access token in `sessionStorage` (11 occurrences, no HttpOnly, no PKCE, no CSRF). It duplicated, and was materially less secure than, the existing BFF stack on `fe/ops-portal-production`. Withdrawn so it cannot be merged. `findContractProblems` is worth re-proposing on top of the BFF runtime. | `65a8dd6` reverts `aaf9ef5` |

## Open

| ID | Sev | Component | Finding | Required action | Blocked by |
| --- | --- | --- | --- | --- | --- |
| SEC-01 | CRITICAL | dependencies | 9 Dependabot alerts on `main`, 8 of them critical, surfaced in a `git push` response and never enumerated | Triage and patch | Unauthenticated GitHub API |
| FE-01 | HIGH | `packages/portal/src/index.tsx` on `main` | The portal shell on `main` keeps the session in `sessionStorage`: a browser-readable bearer token on an operations console | Merge `fe/ops-portal-production`, which replaces it with a BFF using `__Host-` HttpOnly cookies, PKCE and CSRF | Merge authority |
| ARCH-01 | HIGH | branch topology | None of the eight branches on `origin`, including `ops/portal-production-release`, fixes any of BE-01..BE-04, OPS-01 or OPS-02. The release stack as it stands would ship password hashing on the event loop and a topology with no scheduler | Merge the critical fixes **before** the release layer | Merge authority |
| OBS-02 | MEDIUM | observability | Two competing implementations. `be/analytics-observability-v1` has `app/observability.py`, an OTel collector and Alloy log shipping. `feat/observability-and-dr` has `app/core/metrics.py`, the scheduler heartbeat, alert rules and a promtool CI gate. Neither is a superset of the other | Reconcile into one: keep collector and Alloy from the former, heartbeat, alerts and promtool from the latter | Requires running both suites |
| API-01 | MEDIUM | portal contracts | `be/portal-read-models` adds `app/api/v1/portal.py` and `domains/portal/`, the canonical portal read models the mission requires. Unmerged and unreconciled with the layering ratchet | Review, rebase onto the critical fixes, merge first in dependency order | Merge authority |
| BE-05 | HIGH | Availability | `app/core/rate_limit.py` | The rate limiter opens and closes a Redis connection per request, on the login, webhook and public-form paths, and fails closed with 503 on any transient Redis error | Pool one client in a FastAPI lifespan on `app.state`; consider a sliding window once pooled | Not started |
| BE-06 | HIGH | Availability | `app/db/session.py`, `app/main.py` | `create_async_engine` takes SQLAlchemy defaults (`pool_size=5`, `max_overflow=10`): a hard ceiling of 30 connections across two workers, with no `pool_recycle`, no `pool_timeout` and no lifespan, so the engine is never disposed | Explicit pool parameters from settings plus a lifespan that warms the pool, holds the shared Redis client and disposes the engine | Not started |
| BE-07 | HIGH | Performance | `app/domains/auth/dependencies.py` | The effective access context is rebuilt from the database on every guarded request; a route with two guards pays for it twice | Resolve once per request and memoise on `request.state`; short-TTL Redis cache keyed by user and `credential_version` if still hot | Not started |
| FE-04 | MEDIUM | frontend contract | `@breero/types` is hand-written and `contract:check` verifies only path and method presence, never field names, types or nullability | Generate types from `openapi.json`, fail CI on diff | Not started |

## Count correction

An earlier revision of this ledger reported `HIGH_OPEN=2`. That was wrong. BE-05,
BE-06 and BE-07 were classified HIGH in the original architecture review and were
never fixed; they were omitted from the Open table by mistake, not by a severity
judgement. The corrected figure is `HIGH_OPEN=5`. Verified against
`feat/observability-and-dr`: the rate limiter still calls `redis.from_url` per
request, `app/main.py` contains no lifespan, and `dependencies.py` still resolves the
access context three separate times.

## Corrected dependency order

The mission's stated order needs one amendment: the six critical API findings must
land ahead of everything, because every portal in the stack authenticates against the
API that carries them.

1. Critical API fixes — `feat/observability-and-dr` (BE-01..BE-04, OPS-01, OPS-02)
2. Backend contracts — `be/portal-read-models`
3. Observability — reconciled `be/analytics-observability-v1` + `feat/observability-and-dr`
4. Secure portal runtime and BFF — `fe/ops-portal-production` (base of the stack despite its name)
5. `fe/portal-runtime-foundation`
6. `fe/partner-portal-production`
7. `fe/admin-portal-production`
8. Release layer — `ops/portal-production-release`

Branch containment was verified with `git merge-base --is-ancestor`: `fe/ops-portal-production`
is an ancestor of `fe/portal-runtime-foundation`, `fe/partner-portal-production`,
`fe/admin-portal-production` and `ops/portal-production-release`. The two `be/*`
branches are independent of that stack and of each other.
