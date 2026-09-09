# BREERO backup and recovery

Before this existed, production data lived in one Docker volume on one host
(`49.12.145.107`) with no dump job, no off-host copy, and no restore drill. The
documented rollback path covered the *application*; there was nothing for the data.

Read this alongside [`backend-rollback.md`](backend-rollback.md), which rolls the
application back and deliberately does **not** touch the schema.

## What runs

`deploy/backup/docker-compose.backup.yml` adds a `backup` service to the production
stack:

```bash
docker compose \
  -f deploy/production/docker-compose.backend.yml \
  -f deploy/backup/docker-compose.backup.yml up -d
```

Every 24 hours it runs `scripts/backup/backup.sh`, which:

1. dumps to `<name>.partial` and renames only on success — an interrupted dump must
   never be left under a name that retention and restore treat as a real backup;
2. reads the archive back with `pg_restore --list` and rejects it if it is unreadable
   or contains no table data. **A dump nobody has read back is not a backup;**
3. writes a SHA-256 alongside it;
4. prunes older copies, but only after a success and never below
   `RETENTION_MIN_COPIES` — otherwise a fortnight of failing backups would quietly
   delete every good copy on the way past;
5. replicates off-host if `BACKUP_REMOTE` is set, and warns loudly if it is not.

The backup image is pinned to the same PostgreSQL major as the server. `pg_dump`
refuses to dump a server newer than itself, so a mismatched client is a silent backup
outage.

### Set `BACKUP_REMOTE`

A backup on the same disk as the database it protects survives a dropped table, not a
lost host. Until `BACKUP_REMOTE` is configured, this protects against operator error
only — not against losing `49.12.145.107`.

### `spatial_ref_sys` is excluded

PostGIS repopulates it from `CREATE EXTENSION` during restore, so including the dumped
copy makes a strict restore fail on duplicate keys. This is the standard PostGIS
caveat. If custom SRIDs are ever added, they need to be dumped separately.

## Restoring

```bash
scripts/backup/restore-drill.sh <dump-file> <scratch-database-url>
```

**Always restore into a new, isolated database first** — the same rule
`backend-rollback.md` already states for staging. Never restore over a live database
to "see if it works".

The drill verifies four things, in order:

1. the checksum matches, so a corrupt file is caught before it is trusted;
2. `alembic_version` holds a revision — a restore that produced an empty schema would
   otherwise pass every structural check;
3. `bookings`, `payments`, `jobs`, `users` and `integration_events` exist, and the
   PostGIS extension is present. Geography is the thing an extension-less restore
   loses quietly: coverage checks fail closed, so the symptom is "no appointments
   available" rather than an error;
4. row counts match the source, when `SOURCE_DATABASE_URL` is set.

## The drill runs in CI

An untested backup is a hypothesis. The backend workflow takes a real dump of the
schema the migrations just built, restores it into a scratch database, and asserts the
result is usable. A second step feeds the drill a deliberately corrupt file and fails
if it is *accepted* — a check that never fails is not a check.

This means the procedure on this page cannot rot unnoticed between incidents.

## Recovering the host

Order matters. Restoring data before the schema is at the right revision produces a
database the application refuses to start against.

1. Stand up PostgreSQL from `deploy/production/docker-compose.backend.yml` on the
   replacement host. Do not start `api`, `worker` or `scheduler` yet.
2. Restore the most recent verified dump into a **new** database and run the drill
   against it.
3. Compare `alembic_version` with the `EXPECTED_SCHEMA_REVISION` the target image
   derives from its own migration scripts. If the dump is older than the image, run
   `alembic upgrade head` — never the reverse.
4. Start `api` alone and confirm `/health/ready` returns 200. It checks Postgres,
   Redis, and that the schema revision matches, so this is the real gate.
5. Start `worker`, then `scheduler`. Confirm
   `breero_scheduled_task_last_success_age_seconds` starts falling — see
   [`observability.md`](observability.md). A restored host with no scheduler drains
   nothing.
6. Only then route traffic back at the edge.

## What is still missing

**Point-in-time recovery.** These are nightly snapshots, so the worst case is up to 24
hours of lost bookings and payments. Closing that needs WAL archiving to off-host
storage (pgBackRest or WAL-G), which is a larger change to the PostgreSQL service
itself and is deliberately not attempted here.

Until then, the recovery point objective is **24 hours** and should be stated as such
to anyone depending on it. Stripe remains authoritative for payment completion, so
payments captured inside the lost window are recoverable by replaying webhook events;
bookings made in that window are not.
