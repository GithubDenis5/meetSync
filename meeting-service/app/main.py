"""Meeting Service — create/manage events, RSVP attendance tracking."""

from __future__ import annotations

import logging
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import MeetingSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.meeting import Meeting, MeetingParticipant, RsvpStatus
from shared.models.user import User
from shared.models.group import Group, Membership
from shared.models.idea import Idea
from shared.schemas.meeting import (
    MeetingCreateRequest, MeetingResponse,
    RsvpRequest, ParticipantResponse,
)

logger = logging.getLogger("meeting-service")
settings = MeetingSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Meeting Service", version="0.1.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"service": "meeting-service", "status": "ok"}


async def _load_meeting_with_relations(
    db: AsyncSession,
    meeting_id: int,
) -> Meeting | None:
    """Load a meeting with all relationships eagerly."""
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.creator),
            selectinload(Meeting.idea),
            selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        )
        .where(Meeting.id == meeting_id)
    )
    return result.scalar_one_or_none()


async def _meeting_to_response(meeting: Meeting) -> MeetingResponse:
    """Convert a Meeting model to a response with participant info."""
    creator_name = meeting.creator.name if meeting.creator else None
    idea_title = meeting.idea.title if meeting.idea else None

    participants = []
    for mp in meeting.participants:
        user_name = mp.user.name if mp.user else "Unknown"
        participants.append(ParticipantResponse(
            user_id=mp.user_id,
            user_name=user_name,
            status=str(mp.status),
        ))

    return MeetingResponse(
        id=meeting.id,
        group_id=meeting.group_id,
        idea_id=meeting.idea_id,
        idea_title=idea_title,
        title=meeting.title,
        description=meeting.description,
        date=meeting.date,
        time=meeting.time,
        location=meeting.location,
        photo_url=meeting.photo_url,
        creator_id=meeting.creator_id,
        creator_name=creator_name,
        participants=participants,
        created_at=meeting.created_at,
    )


async def _verify_group_member(
    db: AsyncSession,
    group_id: int,
    user_id: int,
) -> None:
    """Raise 403 if user is not a member of the group."""
    result = await db.execute(
        select(Membership).where(and_(
            Membership.user_id == user_id,
            Membership.group_id == group_id,
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "You are not a member of this group")


# ─── List meetings for a group ──────────────────────────────────


@app.get("/api/v1/meetings", response_model=list[MeetingResponse])
async def list_meetings(
    group_id: int = Query(...),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    await _verify_group_member(db, group_id, user_id)

    query = (
        select(Meeting)
        .options(
            selectinload(Meeting.creator),
            selectinload(Meeting.idea),
            selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        )
        .where(Meeting.group_id == group_id)
    )

    if date_from:
        query = query.where(Meeting.date >= date_from)
    if date_to:
        query = query.where(Meeting.date <= date_to)

    query = query.order_by(Meeting.date, Meeting.time)

    result = await db.execute(query)
    meetings = result.scalars().all()
    return [await _meeting_to_response(m) for m in meetings]


# ─── Create a meeting ───────────────────────────────────────────


@app.post("/api/v1/meetings", response_model=MeetingResponse, status_code=201)
async def create_meeting(
    body: MeetingCreateRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    await _verify_group_member(db, body.group_id, user_id)

    # Get user name directly (don't rely on relationship lazy loading)
    user_result = await db.execute(select(User).where(User.id == user_id))
    user_obj = user_result.scalar_one_or_none()
    user_name = user_obj.name if user_obj else "Unknown"

    # If linked to an idea, resolve the idea title
    idea_title = None
    if body.idea_id:
        idea_result = await db.execute(
            select(Idea).where(Idea.id == body.idea_id, Idea.group_id == body.group_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea:
            idea_title = idea.title

    meeting = Meeting(
        group_id=body.group_id,
        idea_id=body.idea_id,
        title=body.title,
        description=body.description,
        date=body.date,
        time=body.time,
        location=body.location,
        creator_id=user_id,
    )
    db.add(meeting)
    await db.flush()

    # Creator automatically goes
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=user_id,
        status=RsvpStatus.GOING,
    )
    db.add(participant)

    logger.info("Meeting created: id=%d group=%d by user=%d", meeting.id, body.group_id, user_id)

    return MeetingResponse(
        id=meeting.id,
        group_id=meeting.group_id,
        idea_id=body.idea_id,
        idea_title=idea_title,
        title=meeting.title,
        description=meeting.description,
        date=meeting.date,
        time=meeting.time,
        location=meeting.location,
        photo_url=meeting.photo_url,
        creator_id=user_id,
        creator_name=user_name,
        participants=[
            ParticipantResponse(user_id=user_id, user_name=user_name, status=RsvpStatus.GOING.value),
        ],
        created_at=meeting.created_at,
    )


# ─── Get meeting details ────────────────────────────────────────


@app.get("/api/v1/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    meeting = await _load_meeting_with_relations(db, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    await _verify_group_member(db, meeting.group_id, user_id)
    return await _meeting_to_response(meeting)


# ─── Delete a meeting ────────────────────────────────────────────


@app.delete("/api/v1/meetings/{meeting_id}", status_code=204)
async def delete_meeting(
    meeting_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.creator_id != user_id:
        raise HTTPException(403, "Only the creator can delete this meeting")
    await db.delete(meeting)


# ─── RSVP ─────────────────────────────────────────────────────────


@app.post("/api/v1/meetings/{meeting_id}/rsvp", response_model=ParticipantResponse)
async def rsvp_meeting(
    meeting_id: int,
    body: RsvpRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Verify meeting exists
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    await _verify_group_member(db, meeting.group_id, user_id)

    # Check existing RSVP
    existing = await db.execute(
        select(MeetingParticipant).where(and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        ))
    )
    participant = existing.scalar_one_or_none()

    if participant:
        participant.status = RsvpStatus(body.status)
    else:
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            user_id=user_id,
            status=RsvpStatus(body.status),
        )
        db.add(participant)

    await db.flush()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    logger.info("RSVP: user=%d meeting=%d status=%s", user_id, meeting_id, body.status)
    return ParticipantResponse(
        user_id=user_id,
        user_name=user.name,
        status=str(body.status),
    )


# ─── List participants for a meeting ────────────────────────────


@app.get("/api/v1/meetings/{meeting_id}/participants", response_model=list[ParticipantResponse])
async def list_participants(
    meeting_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    await _verify_group_member(db, meeting.group_id, user_id)

    parts = await db.execute(
        select(MeetingParticipant, User)
        .join(User, MeetingParticipant.user_id == User.id)
        .where(MeetingParticipant.meeting_id == meeting_id)
    )
    rows = parts.all()
    return [
        ParticipantResponse(
            user_id=mp.user_id,
            user_name=u.name,
            status=str(mp.status),
        )
        for mp, u in rows
    ]
