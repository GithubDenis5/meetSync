#!/bin/sh
# PostgreSQL restore script
# Usage: restore-db <backup-file>
# Example: restore-db /backups/postgres/auto-20240101-030000.sql.gz

set -e

if [ -z "$1" ]; then
    echo "Usage: restore-db <backup-file>"
    echo "Example: restore-db /backups/postgres/auto-20240101-030000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

PGHOST="${PGHOST:-postgres}"
PGUSER="${PGUSER:-${POSTGRES_USER:-meetsync}}"
PGDB="${PGDB:-${POSTGRES_DB:-meetsync}}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD}}"

export PGHOST PGUSER PGDB PGPASSWORD

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting restore from: $BACKUP_FILE"
echo "WARNING: This will overwrite the current database!"
echo "Database: $PGDB on $PGHOST"
echo ""
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring..."

gunzip -c "$BACKUP_FILE" | pg_restore -h "$PGHOST" -U "$PGUSER" -d "$PGDB" \
    --no-owner --no-acl \
    --clean --if-exists

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore complete"
