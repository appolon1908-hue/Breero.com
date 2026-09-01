# BREERO HIGH / MEDIUM zero report

**Result: NOT ACHIEVED.** HIGH and MEDIUM findings remain open.

Counts are as at `origin/main` `a5fc9921cbd6b71f83f1660fc505f02316572256`, with fixes
staged on `feat/observability-and-dr` and unmerged.

## Counts

| Category | HIGH found | HIGH fixed | HIGH open | MEDIUM found | MEDIUM fixed | MEDIUM open |
| --- | --- | --- | --- | --- | --- | --- |
| Security | 3 | 3 | 0 | 1 | 1 | 0 |
| Availability | 3 | 1 | 2 | 0 | 0 | 0 |
| Correctness | 1 | 1 | 0 | 1 | 1 | 0 |
| Deployment | 1 | 1 | 0 | 1 | 1 | 0 |
| Performance | 1 | 0 | 1 | 0 | 0 | 0 |
| Architecture | 1 | 0 | 1 | 3 | 2 | 1 |
| Frontend | 1 | 0 | 1 | 2 | 1 | 1 |
| Observability | 0 | 0 | 0 | 2 | 1 | 1 |
| Dependencies | — | — | — | — | — | — |
| **Total** | **11** | **6** | **5** | **10** | **7** | **3** |

`HIGH_FOUND_INITIAL=11`, `HIGH_FIXED=6`, `HIGH_OPEN=5`
`MEDIUM_FOUND_INITIAL=10`, `MEDIUM_FIXED=7`, `MEDIUM_OPEN=3`

**Correction.** A previous revision of this report gave `HIGH_OPEN=2`. BE-05, BE-06
and BE-07 were rated HIGH in the original architecture review and remain unfixed;
omitting them was an accounting error, not a re-rating. Verified against
`feat/observability-and-dr`: `rate_limit.py` still calls `redis.from_url` per request,
`main.py` contains no lifespan, and `dependencies.py` still resolves the access
context three separate times.

These counts cover findings discovered by direct source review. They are **not**
complete, and must not be read as a clean bill of health:

- **Code-scanning results are unreadable.** CodeQL was added to the workflows in this
  work but has never run, and results cannot be fetched without an authenticated
  GitHub API. First-party SAST findings are therefore unknown, not zero.
- **Dependabot results are unenumerated.** A `git push` response reported 9
  vulnerabilities on the default branch, 8 of them critical. They are tracked as
  SEC-01 at CRITICAL severity and are excluded from the table above because their
  categories cannot be determined.
- Secret scanning, dependency audit and container scanning are CI-only steps that did
  not execute.

## Open HIGH

**FE-01 — browser-readable session token on the private portals.**
`packages/portal/src/index.tsx` on `main` stores the session, including the access
token, in `sessionStorage`. Any script running on an operations or administration
origin can read it. Fixed by `fe/ops-portal-production`, which replaces it with a
same-origin BFF using `__Host-` HttpOnly SameSite cookies, PKCE, state, nonce,
AES-encrypted session envelopes and a per-session CSRF token. Blocked on merge
authority.

**ARCH-01 — the release stack does not carry the critical API fixes.**
Verified by grep against all eight exact branch heads: none of `main`,
`be/analytics-observability-v1`, `be/portal-read-models`,
`fe/portal-runtime-foundation`, `fe/partner-portal-production`,
`fe/ops-portal-production`, `fe/admin-portal-production` or
`ops/portal-production-release` contains Argon2id, a cached JWKS client, a NullPool
worker engine, a `beat` service in the production compose file, or `--proxy-headers`
in the image default. Activating `ops/portal-production-release` would ship all six
critical findings into production. Blocked on merge order and merge authority.

**BE-05 — the rate limiter opens a Redis connection per request.**
A full TCP connect and AUTH handshake on every limited call, on the hottest paths,
and a 503 on any transient Redis error turns a blip into an outage on login and the
Stripe webhook. Fix: one pooled client on `app.state`, created in a lifespan.

**BE-06 — no connection pool sizing and no lifespan.**
SQLAlchemy defaults give a hard ceiling of 30 connections across two workers, with no
`pool_recycle`, so connections outlive a Postgres restart or a proxy idle timeout. The
app declares no lifespan at all, so the engine is never disposed on shutdown.

**BE-07 — RBAC costs two or more database round trips per request.**
`current_user` loads the user, then each permission guard rebuilds the effective
access context from scratch. A route with two guards pays twice, on every request.

## Open MEDIUM

**OBS-02 — two competing observability implementations.**
`be/analytics-observability-v1` provides `app/observability.py`, an OTel collector
config and Alloy log shipping. `feat/observability-and-dr` provides
`app/core/metrics.py`, domain gauges, the scheduler heartbeat, nine alert rules and a
promtool CI gate. Neither is a superset. Merging both unreconciled would produce two
metric registries and two runbooks.

**API-01 — canonical portal read models unmerged.**
`be/portal-read-models` adds `app/api/v1/portal.py` and `app/domains/portal/`, plus
finance-safe provider directory contracts. This is the backend contract layer the
portal stack should consume, and it is first in the corrected dependency order.

**FE-04 — the frontend contract is structurally unverified.**
`@breero/types` is hand-maintained and `scripts/check-frontend-openapi.mjs` asserts
only that paths and methods exist. No field name, type, nullability or enum value is
compared, so a backend rename ships green and fails at runtime.

## Fixed in this work

Six HIGH: BE-01 password hashing on the event loop, BE-02 per-request JWKS client,
BE-03 hand-rolled JWT, BE-04 pooled connections across event loops, OPS-01 missing
scheduler, OPS-02 missing proxy-header defaults.

Seven MEDIUM: BE-08 unenforced layering, BE-09 unused abstractions, BE-10 hand-edited
readiness revision, QA-01 missing quality gates, QA-02 vacuously-passing test,
FE-02 unreviewable single-line JSX, OPS-03 absent backup and restore drill.

One HIGH withdrawn: FE-03, a portal runtime authored in this session that stored
tokens in `sessionStorage`. It duplicated and was less secure than the existing BFF
stack, and was reverted rather than left merge-eligible.

Full detail, including reproduction and regression tests, is in
`BREERO_REMEDIATION_LEDGER.md`.
