#!/usr/bin/env python3
"""Admin CLI for MeetSync — utility operations.

Usage:
    python scripts/admin.py <command> [options]

Commands:
    create-user           Register a new user
    list-services         Check /health on all services
    purge-notifications   Delete old notifications
    migrate-check         Check Alembic migration status
    rabbitmq-status       Check RabbitMQ queues
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# ─── Config ──────────────────────────────────────────────────────

BASE_URL = os.environ.get("MEETSYNC_BASE_URL", "http://localhost:8000")

SERVICES = {
    "auth-service": 8001,
    "user-service": 8002,
    "group-service": 8003,
    "calendar-service": 8004,
    "ideas-service": 8005,
    "voting-service": 8006,
    "recommendation-service": 8007,
    "notification-service": 8008,
    "telegram-service": 8009,
    "scheduler-service": 8010,
    "meeting-service": 8011,
}


# ─── Helpers ─────────────────────────────────────────────────────

def _get_service_url(name: str) -> str:
    port = SERVICES[name]
    return f"http://localhost:{port}"


def _print_table(rows: list[list[str]], headers: list[str]) -> None:
    """Print a simple aligned table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def fmt_row(row: list[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(row, col_widths))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt_row(row))


# ─── Commands ────────────────────────────────────────────────────


async def cmd_create_user(args: argparse.Namespace) -> None:
    """Register a new user via auth service API."""
    payload: dict[str, Any] = {"name": args.name, "email": args.email, "password": args.password}
    if args.username:
        payload["username"] = args.username
    if args.telegram:
        payload["telegram_id"] = args.telegram

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/api/v1/auth/register", json=payload)

    if resp.status_code == 201:
        data = resp.json()
        print(f"✅ User created: id={data['id']} email={data['email']}")
        print(f"   Access token: {data.get('access_token', 'N/A')[:40]}...")
    else:
        detail = resp.json().get("detail", resp.text)
        print(f"❌ Failed: {detail}")
        sys.exit(1)


async def cmd_list_services(_args: argparse.Namespace) -> None:
    """Check /health on all services."""
    rows: list[list[str]] = []
    all_ok = True

    for name in sorted(SERVICES):
        url = _get_service_url(name)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "?")
                    rows.append([name, f"✅ {status}", str(resp.status_code)])
                else:
                    rows.append([name, "❌ Bad status", str(resp.status_code)])
                    all_ok = False
        except httpx.RequestError as e:
            rows.append([name, f"❌ Unreachable", str(e)])
            all_ok = False

    if all_ok:
        print(f"\n✅ All {len(SERVICES)} services healthy\n")
    else:
        print(f"\n⚠️  Some services have issues\n")

    _print_table(rows, ["Service", "Status", "Response"])


async def cmd_purge_notifications(args: argparse.Namespace) -> None:
    """Delete notifications older than N days.

    Requires direct DB access (SQLAlchemy URL env var).
    """
    days = args.days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    db_url = os.environ.get("SQLALCHEMY_URL")
    if not db_url:
        print("❌ SQLALCHEMY_URL environment variable is required for DB operations.")
        print("   Example: SQLALCHEMY_URL=postgresql+asyncpg://user:pass@host/db")
        sys.exit(1)

    # Use synchronous psycopg2 for simplicity in CLI
    try:
        import psycopg2
        conn = psycopg2.connect(db_url.replace("+asyncpg", ""))
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM notifications WHERE created_at < %s",
            (cutoff.isoformat(),),
        )
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Deleted {deleted} notifications older than {days} days.")
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)


async def cmd_migrate_check(_args: argparse.Namespace) -> None:
    """Check Alembic migration status."""
    import subprocess

    db_url = os.environ.get("SQLALCHEMY_URL")
    env = {**os.environ}
    if db_url:
        env["SQLALCHEMY_URL"] = db_url

    # Check current revision
    result = subprocess.run(
        ["alembic", "-c", "alembic.ini", "current"],
        env=env, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)) + "/..",
    )
    current = result.stdout.strip() or result.stderr.strip()
    print(f"Current: {current}")

    # Check head
    result = subprocess.run(
        ["alembic", "-c", "alembic.ini", "heads"],
        env=env, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)) + "/..",
    )
    head = result.stdout.strip() or result.stderr.strip()
    print(f"Head:    {head}")

    if current and head and current.split()[0] == head.split()[0]:
        print("✅ Database is up to date.")
    else:
        print("⚠️  Database needs migration. Run: alembic upgrade head")


async def cmd_rabbitmq_status(_args: argparse.Namespace) -> None:
    """Check RabbitMQ queues via management API."""
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = os.environ.get("RABBITMQ_MANAGEMENT_PORT", "15672")
    user = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"http://{host}:{port}/api/queues",
                auth=(user, password),
            )
            if resp.status_code != 200:
                print(f"❌ Management API returned {resp.status_code}: {resp.text[:200]}")
                sys.exit(1)

            queues = resp.json()
            if not queues:
                print("No queues found.")
                return

            rows: list[list[str]] = []
            total_messages = 0
            for q in queues:
                name = q["name"]
                messages = q.get("messages_ready", 0) + q.get("messages_unacknowledged", 0)
                consumers = q.get("consumers", 0)
                state = "✅" if consumers > 0 else "⚠️"
                rows.append([name, f"{state}", str(messages), str(consumers)])
                total_messages += messages

            print(f"\nRabbitMQ Queues ({len(queues)} total, {total_messages} messages)\n")
            _print_table(rows, ["Queue", " ", "Messages", "Consumers"])
    except httpx.RequestError as e:
        print(f"❌ Cannot connect to RabbitMQ management API: {e}")
        sys.exit(1)


# ─── Main ────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="MeetSync Admin CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # create-user
    p = sub.add_parser("create-user", help="Register a new user")
    p.add_argument("--name", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--username")
    p.add_argument("--telegram")

    # list-services
    sub.add_parser("list-services", help="Check /health on all services")

    # purge-notifications
    p = sub.add_parser("purge-notifications", help="Delete old notifications")
    p.add_argument("--days", type=int, default=30)

    # migrate-check
    sub.add_parser("migrate-check", help="Check Alembic migration status")

    # rabbitmq-status
    sub.add_parser("rabbitmq-status", help="Check RabbitMQ queues")

    args = parser.parse_args()

    import asyncio

    cmd_map = {
        "create-user": cmd_create_user,
        "list-services": cmd_list_services,
        "purge-notifications": cmd_purge_notifications,
        "migrate-check": cmd_migrate_check,
        "rabbitmq-status": cmd_rabbitmq_status,
    }

    asyncio.run(cmd_map[args.command](args))


if __name__ == "__main__":
    main()
