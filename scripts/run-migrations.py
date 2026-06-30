#!/usr/bin/env python3
"""
Auto-deploy database migrations.

First launch (no tables):  runs alembic upgrade head
Tables exist, no version: stamps alembic_version at head
Already at head:          skips (fast exit — no-op)
Off revision:             runs alembic upgrade head
"""
import os
import sys
import subprocess

db_url = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
)
env = {**os.environ, "SQLALCHEMY_URL": db_url}
base_cmd = ["alembic", "-c", "alembic.ini"]

# ── Step 1: Check current alembic head revision ──────────────────────
head_result = subprocess.run(
    [*base_cmd, "heads"], env=env, capture_output=True, text=True
)
head_revision = head_result.stdout.strip().split()[0] if head_result.stdout.strip() else ""
print(f"Current head revision: {head_revision or '(none)'}", flush=True)

# ── Step 2: Check current database state ─────────────────────────────
current_result = subprocess.run(
    [*base_cmd, "current"], env=env, capture_output=True, text=True
)
current_output = current_result.stdout.strip()

# If alembic_version table doesn't exist, "current" shows an error
alembic_missing = "does not exist" in current_result.stderr or "doesn't exist" in current_result.stderr

if alembic_missing:
    print("Alembic version table not found — checking for existing tables...", flush=True)

    # Quick check: is there any table in the public schema?
    check_result = subprocess.run(
        [
            "python3", "-c",
            "import sys;"
            "import psycopg2;"
            f"conn = psycopg2.connect('{db_url}');"
            "cur = conn.cursor();"
            "cur.execute(\"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name != 'alembic_version'\");"
            "count = cur.fetchone()[0];"
            "conn.close();"
            f"sys.exit(0 if count > 0 else 1)"
        ],
        env=env,
        capture_output=True,
        text=True,
    )

    if check_result.returncode == 0:
        # Tables exist but alembic_version is missing — stamp head
        print("Tables exist — stamping alembic_version at head revision...", flush=True)
        result = subprocess.run(
            [*base_cmd, "stamp", "head"], env=env, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(result.stdout)
            print("✅ Stamped head revision. Database ready.", flush=True)
            sys.exit(0)
        else:
            print("❌ Stamping failed:", result.stderr, flush=True)
            sys.exit(1)
    else:
        # No tables at all — first launch, run full migration
        print("No existing tables found — running full migration...", flush=True)

elif current_output.startswith(head_revision) and head_revision:
    # Already at head revision — no-op fast exit
    print(f"✅ Database already at head revision ({head_revision}). Skipping.", flush=True)
    sys.exit(0)

# ── Step 3: Run migrations ───────────────────────────────────────────
print("Running alembic upgrade head...", flush=True)
result = subprocess.run([*base_cmd, "upgrade", "head"], env=env, capture_output=True, text=True)

if result.returncode == 0:
    print(result.stdout)
    print("✅ Migrations complete!", flush=True)
    sys.exit(0)

# If failed because tables already exist, stamp head
if "DuplicateTable" in result.stderr or "already exists" in result.stderr:
    print("Tables already exist — stamping head revision...", flush=True)
    result = subprocess.run([*base_cmd, "stamp", "head"], env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
        print("✅ Stamped head revision.", flush=True)
        sys.exit(0)
    else:
        print("❌ Stamping failed:", result.stderr, flush=True)
        sys.exit(1)
else:
    print("❌ Migration failed:", result.stderr, flush=True)
    sys.exit(1)
