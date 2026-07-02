"""Calendar Service — availability marking, recurring rules."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import setup_logging

from app.config import CalendarSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.calendar import Availability, AvailabilityStatus, RecurringRule
from shared.schemas.calendar import (
    AvailabilityRequest, AvailabilityResponse,
    GroupCalendarResponse,
    RecurringRuleRequest, RecurringRuleUpdateRequest, RecurringRuleResponse,
)
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("calendar-service")
logger = logging.getLogger("calendar-service")
settings = CalendarSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Calendar Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "calendar-service")
add_lifecycle(app, "calendar-service", db_manager=db_manager)


@app.get("/health")
async def health() -> dict:
    return {"service": "calendar-service", "status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()


@app.post("/api/v1/calendar/availability", response_model=AvailabilityResponse, status_code=201)
async def set_availability(
    body: AvailabilityRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Check if availability already exists for this date
    result = await db.execute(
        select(Availability).where(and_(
            Availability.user_id == user_id,
            Availability.group_id == body.group_id,
            Availability.date == body.date,
        ))
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.status = AvailabilityStatus(body.status)
        existing.start_time = body.start_time
        existing.end_time = body.end_time
        existing.recurring_rule = body.recurring_rule
        existing.updated_at = datetime.now(timezone.utc)
        av = existing
    else:
        av = Availability(
            user_id=user_id,
            group_id=body.group_id,
            date=body.date,
            status=AvailabilityStatus(body.status),
            start_time=body.start_time,
            end_time=body.end_time,
            recurring_rule=body.recurring_rule,
        )
        db.add(av)

    await db.flush()
    return AvailabilityResponse.model_validate(av)


@app.post("/api/v1/calendar/availability/batch", status_code=201)
async def set_availability_batch(
    body: list[AvailabilityRequest],
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    results = []
    for item in body:
        result = await db.execute(
            select(Availability).where(and_(
                Availability.user_id == user_id,
                Availability.group_id == item.group_id,
                Availability.date == item.date,
            ))
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.status = AvailabilityStatus(item.status)
            existing.start_time = item.start_time
            existing.end_time = item.end_time
            existing.recurring_rule = item.recurring_rule
            existing.updated_at = datetime.now(timezone.utc)
            results.append(existing)
        else:
            av = Availability(
                user_id=user_id, group_id=item.group_id, date=item.date,
                status=AvailabilityStatus(item.status), start_time=item.start_time,
                end_time=item.end_time, recurring_rule=item.recurring_rule,
            )
            db.add(av)
            results.append(av)
    return {"count": len(results)}


@app.get("/api/v1/calendar/availability/me", response_model=list[AvailabilityResponse])
async def get_my_availability(
    group_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Get explicit availability records
    result = await db.execute(
        select(Availability).where(and_(
            Availability.user_id == user_id,
            Availability.group_id == group_id,
            Availability.date >= start_date,
            Availability.date <= end_date,
        )).order_by(Availability.date)
    )
    explicit = result.scalars().all()

    # Get recurring rules
    rules_result = await db.execute(
        select(RecurringRule).where(and_(
            RecurringRule.user_id == user_id,
            RecurringRule.group_id == group_id,
        ))
    )
    rules = rules_result.scalars().all()

    # Expand recurring rules, merge with explicit (explicit overrides)
    expanded = _expand_recurring_rules(rules, start_date, end_date, explicit)

    # Combine: explicit first, then expanded
    combined = [AvailabilityResponse.model_validate(a) for a in explicit]
    combined.extend(
        AvailabilityResponse(
            id=0,
            user_id=user_id,
            group_id=group_id,
            date=e["date"],
            status=e["status"],
            start_time=e["start_time"],
            end_time=e["end_time"],
            recurring_rule=e["recurring_rule"],
        )
        for e in expanded
    )
    return combined


@app.get("/api/v1/calendar/availability/group", response_model=list[GroupCalendarResponse])
async def get_group_calendar(
    group_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(db_manager.get_session),
):
    from shared.models.user import User
    from shared.models.group import Membership

    # Get all members
    members = await db.execute(
        select(User).join(Membership).where(
            and_(Membership.group_id == group_id, User.is_active == True)
        )
    )
    users = members.scalars().all()

    result = []
    for user in users:
        # Get explicit availability
        avs = await db.execute(
            select(Availability).where(and_(
                Availability.user_id == user.id,
                Availability.group_id == group_id,
                Availability.date >= start_date,
                Availability.date <= end_date,
            )).order_by(Availability.date)
        )
        explicit = avs.scalars().all()

        # Get recurring rules for this user
        rules_result = await db.execute(
            select(RecurringRule).where(and_(
                RecurringRule.user_id == user.id,
                RecurringRule.group_id == group_id,
            ))
        )
        rules = rules_result.scalars().all()

        # Expand recurring rules
        expanded = _expand_recurring_rules(rules, start_date, end_date, explicit)

        combined = [AvailabilityResponse.model_validate(a) for a in explicit]
        combined.extend(
            AvailabilityResponse(
                id=0,
                user_id=user.id,
                group_id=group_id,
                date=e["date"],
                status=e["status"],
                start_time=e["start_time"],
                end_time=e["end_time"],
                recurring_rule=e["recurring_rule"],
            )
            for e in expanded
        )
        result.append(GroupCalendarResponse(
            user_id=user.id,
            user_name=user.name,
            availabilities=combined,
        ))
    return result


@app.get("/api/v1/calendar/availability/user/{user_id}", response_model=list[AvailabilityResponse])
async def get_user_availability(
    user_id: int,
    group_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(
        select(Availability).where(and_(
            Availability.user_id == user_id,
            Availability.group_id == group_id,
            Availability.date >= start_date,
            Availability.date <= end_date,
        )).order_by(Availability.date)
    )
    return [AvailabilityResponse.model_validate(a) for a in result.scalars().all()]


@app.delete("/api/v1/calendar/availability/{availability_id}", status_code=204)
async def delete_availability(
    availability_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(
        select(Availability).where(and_(
            Availability.id == availability_id, Availability.user_id == user_id
        ))
    )
    av = result.scalar_one_or_none()
    if not av:
        raise HTTPException(404, "Availability not found")
    await db.delete(av)


# ─── Recurring Rules ──────────────────────────────────────────────


def _expand_recurring_rules(
    rules: list[RecurringRule],
    start_date: date,
    end_date: date,
    explicit_availabilities: list[Availability],
) -> list[dict]:
    """Expand recurring rules into virtual availability records.

    Merges with explicit availability — explicit records override recurring ones
    for the same date.
    """
    # Track dates with explicit records
    explicit_dates: set[date] = set()
    for av in explicit_availabilities:
        explicit_dates.add(av.date)

    day_index = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    }

    results = []
    current = start_date
    while current <= end_date:
        for rule in rules:
            # Check if rule applies to this day of week
            rule_day_num = day_index.get(rule.day_of_week)
            if rule_day_num is None or current.weekday() != rule_day_num:
                continue
            # Check date range
            if rule.date_start and current < rule.date_start:
                continue
            if rule.date_end and current > rule.date_end:
                continue
            # Skip if there's an explicit record for this date
            if current in explicit_dates:
                continue
            results.append({
                "date": current,
                "status": rule.status,
                "start_time": rule.start_time,
                "end_time": rule.end_time,
                "recurring_rule": f"every {rule.day_of_week}",
                "_from_rule_id": rule.id,
            })
        current += timedelta(days=1)

    return results


@app.post("/api/v1/calendar/recurring-rules", response_model=RecurringRuleResponse, status_code=201)
async def create_recurring_rule(
    body: RecurringRuleRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    rule = RecurringRule(
        user_id=user_id,
        group_id=body.group_id,
        day_of_week=body.day_of_week,
        status=body.status,
        start_time=body.start_time,
        end_time=body.end_time,
        date_start=body.date_start or date.today(),
        date_end=body.date_end,
    )
    db.add(rule)
    await db.flush()
    logger.info("Recurring rule created: user=%d group=%d day=%s", user_id, body.group_id, body.day_of_week)
    return RecurringRuleResponse.model_validate(rule)


@app.get("/api/v1/calendar/recurring-rules", response_model=list[RecurringRuleResponse])
async def list_recurring_rules(
    group_id: int = Query(...),
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(
        select(RecurringRule).where(and_(
            RecurringRule.user_id == user_id,
            RecurringRule.group_id == group_id,
        )).order_by(RecurringRule.day_of_week)
    )
    return [RecurringRuleResponse.model_validate(r) for r in result.scalars().all()]


@app.put("/api/v1/calendar/recurring-rules/{rule_id}", response_model=RecurringRuleResponse)
async def update_recurring_rule(
    rule_id: int,
    body: RecurringRuleUpdateRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(
        select(RecurringRule).where(and_(
            RecurringRule.id == rule_id,
            RecurringRule.user_id == user_id,
        ))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Recurring rule not found")

    if body.day_of_week is not None:
        rule.day_of_week = body.day_of_week
    if body.status is not None:
        rule.status = body.status
    if body.start_time is not None:
        rule.start_time = body.start_time
    if body.end_time is not None:
        rule.end_time = body.end_time
    if body.date_start is not None:
        rule.date_start = body.date_start
    if body.date_end is not None:
        rule.date_end = body.date_end

    await db.flush()
    return RecurringRuleResponse.model_validate(rule)


@app.delete("/api/v1/calendar/recurring-rules/{rule_id}", status_code=204)
async def delete_recurring_rule(
    rule_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(
        select(RecurringRule).where(and_(
            RecurringRule.id == rule_id,
            RecurringRule.user_id == user_id,
        ))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Recurring rule not found")
    await db.delete(rule)
