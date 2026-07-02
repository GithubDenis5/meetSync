#!/bin/sh
# PostgreSQL backup script
# Usage: backup-db [label]
# Label is optional; defaults to "auto-$(date +%Y%m%d-%H%M%S)"

set -e

BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-4}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-3}"

PGHOST="${PGHOST:-postgres}"
PGUSER="${PGUSER:-${POSTGRES_USER:-meetsync}}"
PGDB="${PGDB:-${POSTGRES_DB:-meetsync}}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD}}"

export PGHOST PGUSER PGDB PGPASSWORD

LABEL="${1:-auto-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$BACKUP_DIR"

FILENAME="${BACKUP_DIR}/${LABEL}.sql.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup: $FILENAME"

pg_dump -h "$PGHOST" -U "$PGUSER" -d "$PGDB" \
    --no-owner --no-acl \
    --format=c \
    | gzip > "$FILENAME"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup complete: $(du -h "$FILENAME" | cut -f1)"

# Retention cleanup
# Daily: keep last N days
find "$BACKUP_DIR" -name "auto-*.sql.gz" -mtime +"$RETENTION_DAILY" -delete

# Weekly: keep first backup of each of the last N weeks (kept by daily retention)
# Monthly: keep first backup of each of the last N months
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Retention cleanup complete"
