"""Scheduler Service — daily checks, availability confirmation workflow."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SchedulerSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.metrics import add_prometheus_middleware
from shared.rabbitmq.client import RabbitMQClient
from shared.rabbitmq.events import EventType
from shared.logging import setup_logging
from shared.app_health import add_lifecycle

setup_logging("scheduler-service")
logger = logging.getLogger("scheduler-service")
settings = SchedulerSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Scheduler Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "scheduler-service")
add_lifecycle(app, "scheduler-service", db_manager=db_manager)

rmq: Optional[RabbitMQClient] = None
_scheduler_task: Optional[asyncio.Task] = None


@app.get("/health")
async def health():
    return {"service": "scheduler-service", "status": "ok"}


@app.on_event("startup")
async def startup():
    global rmq, _scheduler_task
    rmq = RabbitMQClient(settings)  # type: ignore[arg-type]
    await rmq.connect()

    # Subscribe to events
    await rmq.subscribe(
        [EventType.AVAILABILITY_UPDATED, EventType.AVAILABILITY_CONFIRMED],
        handle_availability_event,
        "scheduler.availability",
    )
    await rmq.start_consuming()

    # Start daily check background task
    _scheduler_task = asyncio.create_task(run_daily_checks())


@app.on_event("shutdown")
async def shutdown():
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    if rmq:
        await rmq.disconnect()
    await db_manager.close()


async def handle_availability_event(payload: dict) -> None:
    """Handle availability updated/confirmed events."""
    logger.info("Availability event received: %s", payload)
    # Trigger a recalculation of available dates
    group_id = payload.get("group_id")
    if group_id:
        await recalculate_available_dates(group_id)


async def run_daily_checks() -> None:
    """Background loop that runs daily checks."""
    while True:
        try:
            await daily_check()
        except Exception as e:
            logger.error("Daily check error: %s", e)

        # Sleep until next day (check every hour during development)
        await asyncio.sleep(3600)


async def daily_check() -> None:
    """Check upcoming dates and request availability confirmations."""
    logger.info("Running daily availability check")

    async with db_manager.session() as db:
        from shared.models.group import Group, Membership
        from shared.models.calendar import Availability

        # Get all active groups
        groups_result = await db.execute(select(Group))
        groups = groups_result.scalars().all()

        for group in groups:
            # Check dates 7 days from now
            check_date = date.today() + timedelta(days=7)

            # Check how many members have marked this date
            members_result = await db.execute(
                select(Membership).where(Membership.group_id == group.id)
            )
            members = members_result.scalars().all()
            total_members = len(members)

            availabilities = await db.execute(
                select(Availability).where(and_(
                    Availability.group_id == group.id,
                    Availability.date == check_date,
                ))
            )
            marked_count = len(availabilities.scalars().all())

            # If not enough people have marked, send reminder
            if marked_count < total_members and rmq:
                await rmq.publish(EventType.REMINDER_NEEDED, {
                    "group_id": group.id,
                    "date": check_date.isoformat(),
                    "total_members": total_members,
                    "marked_count": marked_count,
                    "message": f"Please mark your availability for {check_date.isoformat()}",
                })
                logger.info("Reminder sent for group %d, date %s", group.id, check_date)


async def recalculate_available_dates(group_id: int) -> None:
    """Check if enough people are free on any upcoming dates."""
    async with db_manager.session() as db:
        from shared.models.group import Group, Membership
        from shared.models.calendar import Availability, AvailabilityStatus

        # Get group info
        group_result = await db.execute(select(Group).where(Group.id == group_id))
        group = group_result.scalar_one_or_none()
        if not group:
            return

        # Get total members
        members_result = await db.execute(
            select(Membership).where(Membership.group_id == group_id)
        )
        total_members = len(members_result.scalars().all())

        min_people = group.min_people_for_meeting

        # Check next 14 days
        for i in range(1, 15):
            check_date = date.today() + timedelta(days=i)

            # Count free/maybe for this date
            free_result = await db.execute(
                select(func.count()).select_from(Availability).where(and_(
                    Availability.group_id == group_id,
                    Availability.date == check_date,
                    Availability.status.in_([AvailabilityStatus.FREE, AvailabilityStatus.MAYBE]),
                ))
            )
            free_count = free_result.scalar() or 0

            if free_count >= min_people and rmq:
                await rmq.publish(EventType.MEETING_POSSIBLE, {
                    "group_id": group_id,
                    "date": check_date.isoformat(),
                    "free_count": free_count,
                    "total_members": total_members,
                    "title": f"Meeting possible on {check_date.isoformat()}",
                    "message": f"{free_count}/{total_members} people are available on {check_date.isoformat()}",
                })
                logger.info("Meeting possible: group %d, date %s (%d/%d)",
                           group_id, check_date, free_count, total_members)
                break


# ─── REST API ───────────────────────────────────────────────────


@app.post("/api/v1/scheduler/trigger-check")
async def trigger_check(user_id: int = Depends(auth.get_current_user_id)):
    """Manually trigger a daily check."""
    asyncio.create_task(daily_check())
    return {"detail": "Check triggered"}


@app.post("/api/v1/scheduler/recalculate/{group_id}")
async def trigger_recalculate(group_id: int, user_id: int = Depends(auth.get_current_user_id)):
    """Manually trigger recalculation for a group."""
    asyncio.create_task(recalculate_available_dates(group_id))
    return {"detail": "Recalculation triggered"}
