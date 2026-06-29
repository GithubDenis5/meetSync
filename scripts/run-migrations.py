#!/usr/bin/env python3
"""Run alembic migrations. If tables already exist, stamp head instead."""
import os
import sys
import subprocess

db_url = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
)
env = {**os.environ, "SQLALCHEMY_URL": db_url}
base_cmd = ["alembic", "-c", "alembic.ini"]

print("Attempting migrations...", flush=True)
result = subprocess.run([*base_cmd, "upgrade", "head"], env=env, capture_output=True, text=True)

if result.returncode == 0:
    print(result.stdout)
    print("Migrations complete!", flush=True)
    sys.exit(0)

# If failed because tables already exist, stamp head
if "DuplicateTable" in result.stderr or "already exists" in result.stderr:
    print("Tables already exist — stamping head revision...", flush=True)
    result = subprocess.run([*base_cmd, "stamp", "head"], env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
        print("Stamped head revision.", flush=True)
        sys.exit(0)
    else:
        print("Stamping failed:", result.stderr, flush=True)
        sys.exit(1)
else:
    print("Migration failed:", result.stderr, flush=True)
    sys.exit(1)
