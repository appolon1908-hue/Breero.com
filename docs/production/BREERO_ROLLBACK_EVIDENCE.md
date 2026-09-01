# BREERO rollback evidence

**Status: NOT PROVEN. Rollback has never been executed.**

The mission is explicit that rollback PASS may not be claimed from a written script
alone. It has not been claimed. Every field below that would constitute evidence is
recorded as `NOT EXECUTED`, and the reason is recorded with it.

## Why it was not executed

Rollback proof requires an isolated release runtime with PostgreSQL, Redis, Keycloak
and a container orchestrator. None was reachable from this environment:

- no container runtime (`docker ps` cannot connect to the Docker API)
- no PostgreSQL client or server (`psql`, `pg_dump` absent)
- no staging environment
- no authenticated GitHub API, so the rollback workflow cannot be dispatched

None of these gaps is SSH-related, and none may be worked around with SSH.

## Evidence fields

| Field | Value |
| --- | --- |
| Previous production source SHA | `a5fc9921cbd6b71f83f1660fc505f02316572256` (current `origin/main`) |
| Previous API image digest | NOT RECORDED — no release manifest exists in the repository |
| Previous partner image digest | NOT RECORDED |
| Previous operations image digest | NOT RECORDED |
| Previous administration image digest | NOT RECORDED |
| Candidate source SHA | `feat/observability-and-dr` head — not a release candidate; unmerged and unreviewed |
| Candidate image digests | NOT BUILT — no container runtime |
| Schema revision before migration | `023_tenant_email_provisioning`, derived statically from the Alembic script directory, **not** read from a running database |
| Schema revision after migration | NOT EXECUTED |
| Backup identifier | NOT EXECUTED |
| Backup checksum | NOT EXECUTED |
| Restore-test identifier | NOT EXECUTED |
| Restore-test result | NOT EXECUTED |
| Rollback workflow run ID | NOT EXECUTED |
| Forced failure used to trigger rollback | NOT EXECUTED |
| Time rollback began | NOT EXECUTED |
| Time previous release became healthy | NOT EXECUTED |
| Data-integrity check result | NOT EXECUTED |
| Authentication after rollback | NOT EXECUTED |
| API health after rollback | NOT EXECUTED |
| Portal health after rollback | NOT EXECUTED |
| Telemetry after rollback | NOT EXECUTED |
| Operator or environment approval evidence | NOT EXECUTED |

## What exists in the repository

These are implemented and unit-reviewed, but none has run against a live database.

**Application rollback.** `docs/backend-rollback.md` rolls the application back one
image at a time and deliberately does not touch the schema. It records a completed
application-only rehearsal from a prior release, and warns that migration 009 must
never be downgraded automatically.

**Migration reversibility.** The backend workflow round-trips `head → -1 → head` on an
isolated database. Migration 023 drops four tables with no enums and no seed rows, so
the round trip should be clean, but that is a code reading, not a result.

**Backup and restore.** `scripts/backup/backup.sh` writes to `.partial` and renames
only on success, reads the archive back with `pg_restore --list`, discards anything
unreadable or empty, checksums it, and prunes only after a success and never below a
floor. `scripts/backup/restore-drill.sh` verifies checksum, then `alembic_version`,
then the money-carrying tables, then the PostGIS extension, then row counts against
the source. CI takes a real dump, restores it, and separately feeds the drill a
corrupt file and fails if it is *accepted*.

`spatial_ref_sys` is excluded from the dump: PostGIS repopulates it from
`CREATE EXTENSION`, so including it makes a strict restore fail on duplicate keys.

## Known limits, stated rather than implied

- **Recovery point objective is 24 hours.** These are nightly snapshots. Point-in-time
  recovery needs WAL archiving, which is not implemented.
- **`BACKUP_REMOTE` is unset by default.** Until it is configured, backups live on the
  same host as the database they protect: they survive a dropped table, not a lost
  host.
- Stripe remains authoritative for payment completion, so payments captured inside a
  lost window are recoverable by replaying webhook events. Bookings made in that
  window are not.

## To convert this to PASS

1. A reachable isolated release environment with PostgreSQL/PostGIS, Redis and Keycloak.
2. A container runtime, or CI jobs performing build, scan and deploy.
3. An authenticated GitHub API able to dispatch the rollback workflow and record its
   run ID.
4. Execute: deploy candidate, force a canary failure, observe automatic rollback,
   record every field above from the run.
