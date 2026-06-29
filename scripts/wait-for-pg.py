#!/usr/bin/env python3
"""Wait for PostgreSQL to be ready, then exit."""
import os
import socket
import sys
import time

host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", 5432))
timeout = int(os.environ.get("WAIT_TIMEOUT", 60))

print(f"Waiting for PostgreSQL at {host}:{port} (timeout: {timeout}s)...", flush=True)
for i in range(timeout):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print("PostgreSQL is ready!", flush=True)
        sys.exit(0)
    except OSError:
        if i == timeout - 1:
            print(f"Timeout: PostgreSQL not available after {timeout}s", flush=True)
            sys.exit(1)
        time.sleep(1)
