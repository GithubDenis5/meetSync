"""Calendar Service — availability marking, recurring rules."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import CalendarSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.calendar import Availability, AvailabilityStatus
from shared.schemas.calendar import (
    AvailabilityRequest, AvailabilityResponse,
    GroupCalendarResponse,
)

logger = logging.getLogger("calendar-service")
settings = CalendarSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Calendar Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"service": "calendar-service", "status": "ok"}


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
    result = await db.execute(
        select(Availability).where(and_(
            Availability.user_id == user_id,
            Availability.group_id == group_id,
            Availability.date >= start_date,
            Availability.date <= end_date,
        )).order_by(Availability.date)
    )
    return [AvailabilityResponse.model_validate(a) for a in result.scalars().all()]


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
        avs = await db.execute(
            select(Availability).where(and_(
                Availability.user_id == user.id,
                Availability.group_id == group_id,
                Availability.date >= start_date,
                Availability.date <= end_date,
            )).order_by(Availability.date)
        )
        result.append(GroupCalendarResponse(
            user_id=user.id,
            user_name=user.name,
            availabilities=[AvailabilityResponse.model_validate(a) for a in avs.scalars().all()],
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
