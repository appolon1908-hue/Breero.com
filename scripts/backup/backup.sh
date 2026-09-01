#!/usr/bin/env bash
# Take a verified, checksummed PostgreSQL dump and prune old ones.
#
# Custom format (-Fc) rather than plain SQL: it is compressed, it allows selective
# restore of a single table during an incident, and pg_restore can list its contents
# without a running server, which is how the verification step below works.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
RETENTION_MIN_COPIES="${RETENTION_MIN_COPIES:-7}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/breero-${timestamp}.dump"
partial="${target}.partial"

mkdir -p "$BACKUP_DIR"

log() { printf '%s backup: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

# Write to .partial and rename only on success. A dump interrupted midway must never
# be left behind under a name that retention and restore treat as a real backup.
log "dumping to ${target}"
# spatial_ref_sys is excluded deliberately. PostGIS repopulates it from CREATE
# EXTENSION on restore, so including the dumped copy makes a strict restore fail
# on duplicate keys -- the standard PostGIS backup caveat. Custom SRIDs, if any
# are ever added, would need to be dumped separately.
if ! pg_dump --format=custom --compress=9 --no-owner --no-privileges \
      --exclude-table=public.spatial_ref_sys \
      --file="$partial" "$DATABASE_URL"; then
  rm -f "$partial"
  log "FAILED: pg_dump did not complete; no backup written"
  exit 1
fi

# A dump nobody has read back is not a backup. Listing the archive proves the file is
# a structurally intact pg_dump archive rather than a truncated or empty file.
if ! pg_restore --list "$partial" >/dev/null 2>&1; then
  rm -f "$partial"
  log "FAILED: dump did not verify as a readable archive; discarded"
  exit 1
fi

tables="$(pg_restore --list "$partial" | grep -c 'TABLE DATA' || true)"
if [[ "$tables" -eq 0 ]]; then
  rm -f "$partial"
  log "FAILED: dump contains no table data; discarded"
  exit 1
fi

mv "$partial" "$target"
sha256sum "$target" | awk '{print $1}' >"${target}.sha256"
log "wrote ${target} ($(du -h "$target" | cut -f1), ${tables} tables)"

# Retention runs only after a successful dump, and never below the floor. Otherwise a
# fortnight of failing backups would quietly delete every good copy on the way past.
mapfile -t existing < <(find "$BACKUP_DIR" -maxdepth 1 -name 'breero-*.dump' -printf '%T@ %p\n' \
  | sort -rn | awk '{print $2}')
if (( ${#existing[@]} > RETENTION_MIN_COPIES )); then
  for old in "${existing[@]:RETENTION_MIN_COPIES}"; do
    if [[ -n "$(find "$old" -mtime "+${RETENTION_DAYS}" -print -quit)" ]]; then
      log "pruning $(basename "$old")"
      rm -f "$old" "${old}.sha256"
    fi
  done
fi

# Off-host copy. A backup on the same disk as the database it protects survives a
# dropped table, not a lost host. Configure BACKUP_REMOTE to make this real.
if [[ -n "${BACKUP_REMOTE:-}" ]]; then
  log "replicating to ${BACKUP_REMOTE}"
  rclone copy "$target" "$BACKUP_REMOTE" && rclone copy "${target}.sha256" "$BACKUP_REMOTE"
else
  log "WARNING: BACKUP_REMOTE is not set; this copy lives only on this host"
fi

log "done"
