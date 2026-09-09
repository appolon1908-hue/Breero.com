#!/usr/bin/env bash
# Restore a dump into a scratch database and prove it is actually usable.
#
# An untested backup is a hypothesis. This is the test, and it runs in CI against a
# dump taken moments earlier so the procedure itself cannot rot.
#
#   scripts/backup/restore-drill.sh <dump-file> <scratch-database-url>
set -euo pipefail

dump="${1:?usage: restore-drill.sh <dump-file> <scratch-database-url>}"
scratch_url="${2:?usage: restore-drill.sh <dump-file> <scratch-database-url>}"
source_url="${SOURCE_DATABASE_URL:-}"

log() { printf '%s restore-drill: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
fail() { log "FAILED: $*"; exit 1; }

[[ -f "$dump" ]] || fail "dump file ${dump} does not exist"

if [[ -f "${dump}.sha256" ]]; then
  log "verifying checksum"
  actual="$(sha256sum "$dump" | awk '{print $1}')"
  expected="$(cat "${dump}.sha256")"
  [[ "$actual" == "$expected" ]] || fail "checksum mismatch: backup is corrupt"
fi

log "restoring into scratch database"
# --no-owner/--no-privileges: the scratch role differs from production's, and a role
# mismatch must not be reported as a failed restore.
pg_restore --dbname="$scratch_url" --no-owner --no-privileges --exit-on-error "$dump" \
  || fail "pg_restore reported errors"

query() { psql --dbname="$scratch_url" --tuples-only --no-align --command="$1"; }

# 1. The schema is at a known migration, not an arbitrary point in history.
revision="$(query 'SELECT version_num FROM alembic_version' | tr -d '[:space:]')"
[[ -n "$revision" ]] || fail "restored database has no alembic_version row"
log "schema revision: ${revision}"

# 2. The tables that carry money and commitments are present. A restore that silently
#    produced an empty schema would otherwise pass every structural check.
for table in bookings payments jobs users integration_events; do
  exists="$(query "SELECT to_regclass('public.${table}') IS NOT NULL" | tr -d '[:space:]')"
  [[ "$exists" == "t" ]] || fail "table ${table} is missing from the restore"
done

# 3. PostGIS is back. Geography is the one thing an extension-less restore loses
#    quietly, and coverage checks fail closed, so the symptom would be "no
#    appointments available" rather than an error.
postgis="$(query "SELECT count(*) FROM pg_extension WHERE extname = 'postgis'" | tr -d '[:space:]')"
[[ "$postgis" == "1" ]] || fail "the postgis extension did not survive the restore"

# 4. Row counts match the source, when we can see it.
if [[ -n "$source_url" ]]; then
  for table in bookings payments jobs users; do
    restored="$(query "SELECT count(*) FROM ${table}" | tr -d '[:space:]')"
    original="$(psql --dbname="$source_url" --tuples-only --no-align \
      --command="SELECT count(*) FROM ${table}" | tr -d '[:space:]')"
    [[ "$restored" == "$original" ]] \
      || fail "${table}: restored ${restored} rows, source has ${original}"
    log "${table}: ${restored} rows match"
  done
fi

log "PASS: restore verified at revision ${revision}"
