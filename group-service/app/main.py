"""Group Service — groups, memberships, roles, invites."""

from __future__ import annotations

import logging
import secrets

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import setup_logging

from app.config import GroupSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.group import Group, Membership, GroupRole
from shared.models.user import User
from shared.schemas.group import (
    GroupCreateRequest, GroupUpdateRequest, GroupResponse,
    MemberResponse, GroupDashboardResponse, MemberAvailabilityStats,
    JoinGroupRequest, MemberRoleUpdateRequest,
)
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("group-service")
logger = logging.getLogger("group-service")
settings = GroupSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Group Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "group-service")
add_lifecycle(app, "group-service", db_manager=db_manager)


@app.get("/health")
async def health() -> dict:
    return {"service": "group-service", "status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()


def _generate_invite_code() -> str:
    return secrets.token_hex(6).upper()


# ─── Groups ───────────────────────────────────────────────────


@app.get("/api/v1/groups", response_model=list[GroupResponse])
async def list_groups(user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(
        select(Group).join(Membership).where(Membership.user_id == user_id)
    )
    groups = result.scalars().all()
    return [GroupResponse.model_validate(g) for g in groups]


@app.post("/api/v1/groups", response_model=GroupResponse, status_code=201)
async def create_group(body: GroupCreateRequest, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    group = Group(
        name=body.name,
        description=body.description,
        invite_code=_generate_invite_code(),
        owner_id=user_id,
        min_people_for_meeting=body.min_people_for_meeting,
    )
    db.add(group)
    await db.flush()

    # Add creator as OWNER
    membership = Membership(user_id=user_id, group_id=group.id, role=GroupRole.OWNER)
    db.add(membership)

    logger.info("Group created: id=%d name=%s owner=%d", group.id, group.name, user_id)
    return GroupResponse.model_validate(group)


@app.get("/api/v1/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Group not found")
    return GroupResponse.model_validate(group)


@app.patch("/api/v1/groups/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, body: GroupUpdateRequest, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Group not found")

    # Check ownership
    if group.owner_id != user_id:
        raise HTTPException(403, "Only owner can update group")

    if body.name is not None:
        group.name = body.name
    if body.description is not None:
        group.description = body.description
    if body.min_people_for_meeting is not None:
        group.min_people_for_meeting = body.min_people_for_meeting

    return GroupResponse.model_validate(group)


@app.delete("/api/v1/groups/{group_id}", status_code=204)
async def delete_group(group_id: int, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Group not found")
    if group.owner_id != user_id:
        raise HTTPException(403, "Only owner can delete group")
    await db.delete(group)


# ─── Invite Code ───────────────────────────────────────────────


@app.post("/api/v1/groups/{group_id}/refresh-invite", response_model=dict)
async def refresh_invite_code(group_id: int, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Group not found")
    # Only owner/admin can refresh
    membership = await db.execute(
        select(Membership).where(and_(Membership.user_id == user_id, Membership.group_id == group_id))
    )
    member = membership.scalar_one_or_none()
    if not member or member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(403, "Only owner/admin can refresh invite code")
    group.invite_code = _generate_invite_code()
    return {"invite_code": group.invite_code}


# ─── Memberships ────────────────────────────────────────────────


@app.get("/api/v1/groups/{group_id}/members", response_model=list[MemberResponse])
async def list_members(group_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(
        select(Membership, User).join(User, Membership.user_id == User.id).where(Membership.group_id == group_id)
    )
    rows = result.all()
    members = []
    for membership, user in rows:
        members.append(MemberResponse(
            id=membership.id,
            user_id=user.id,
            name=user.name,
            username=user.username,
            telegram_id=user.telegram_id,
            avatar=user.avatar,
            role=membership.role,
        ))
    return members


@app.post("/api/v1/groups/join", response_model=GroupResponse)
async def join_group(body: JoinGroupRequest, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Group).where(Group.invite_code == body.invite_code))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Invalid invite code")

    # Check if already a member
    existing = await db.execute(
        select(Membership).where(and_(Membership.user_id == user_id, Membership.group_id == group.id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Already a member")

    membership = Membership(user_id=user_id, group_id=group.id, role=GroupRole.MEMBER)
    db.add(membership)
    logger.info("User %d joined group %d", user_id, group.id)
    return GroupResponse.model_validate(group)


@app.patch("/api/v1/groups/{group_id}/members/{member_id}/role")
async def update_member_role(group_id: int, member_id: int, body: MemberRoleUpdateRequest, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    # Verify requester is owner/admin
    requester = await db.execute(
        select(Membership).where(and_(Membership.user_id == user_id, Membership.group_id == group_id))
    )
    req_member = requester.scalar_one_or_none()
    if not req_member or req_member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(403, "Only owner/admin can change roles")

    target = await db.execute(
        select(Membership).where(and_(Membership.id == member_id, Membership.group_id == group_id))
    )
    target_member = target.scalar_one_or_none()
    if not target_member:
        raise HTTPException(404, "Member not found")
    if target_member.role == GroupRole.OWNER:
        raise HTTPException(400, "Cannot change owner's role")

    target_member.role = GroupRole(body.role)
    return {"detail": "Role updated"}


@app.delete("/api/v1/groups/{group_id}/members/{member_id}", status_code=204)
async def remove_member(group_id: int, member_id: int, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(
        select(Membership).where(and_(Membership.id == member_id, Membership.group_id == group_id))
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(404, "Member not found")

    # Allow self-leave or owner/admin removal
    if membership.user_id != user_id:
        requester = await db.execute(
            select(Membership).where(and_(Membership.user_id == user_id, Membership.group_id == group_id))
        )
        req_member = requester.scalar_one_or_none()
        if not req_member or req_member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
            raise HTTPException(403, "Not authorized to remove this member")

    if membership.role == GroupRole.OWNER:
        raise HTTPException(400, "Cannot remove owner")

    await db.delete(membership)


# ─── Dashboard ────────────────────────────────────────────────────


@app.get("/api/v1/groups/{group_id}/dashboard", response_model=GroupDashboardResponse)
async def get_group_dashboard(
    group_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Verify membership
    result = await db.execute(
        select(Membership).where(and_(
            Membership.user_id == user_id,
            Membership.group_id == group_id,
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "You are not a member of this group")

    # Total members
    members_result = await db.execute(
        select(func.count()).select_from(Membership)
        .where(Membership.group_id == group_id)
    )
    total_members = members_result.scalar() or 0

    # Meeting stats
    from shared.models.meeting import Meeting, MeetingParticipant

    meetings_result = await db.execute(
        select(func.count()).select_from(Meeting)
        .where(Meeting.group_id == group_id)
    )
    total_meetings = meetings_result.scalar() or 0

    # Average attendance (participants per meeting)
    att_result = await db.execute(
        select(func.avg(
            select(func.count())
            .select_from(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == Meeting.id)
            .correlate(Meeting)
            .scalar_subquery()
        )).select_from(Meeting).where(Meeting.group_id == group_id)
    )
    avg_att = float(att_result.scalar() or 0.0)

    # Upcoming meetings
    from datetime import date
    upcoming_result = await db.execute(
        select(func.count()).select_from(Meeting)
        .where(and_(
            Meeting.group_id == group_id,
            Meeting.date >= date.today(),
        ))
    )
    upcoming_meetings = upcoming_result.scalar() or 0

    # Top 5 ideas by reactions
    from shared.models.idea import Idea, IdeaReaction
    ideas_result = await db.execute(
        select(
            Idea.id, Idea.title,
            func.count(IdeaReaction.id).label("reaction_count")
        )
        .outerjoin(IdeaReaction, IdeaReaction.idea_id == Idea.id)
        .where(Idea.group_id == group_id)
        .group_by(Idea.id, Idea.title)
        .order_by(func.count(IdeaReaction.id).desc())
        .limit(5)
    )
    top_ideas = [
        {"id": row.id, "title": row.title, "reactions": row.reaction_count}
        for row in ideas_result.all()
    ]

    # Availability percentage for next 14 days
    from shared.models.calendar import Availability
    from shared.models.calendar import AvailabilityStatus
    from datetime import timedelta

    avail_result = await db.execute(
        select(func.count()).select_from(Availability)
        .where(and_(
            Availability.group_id == group_id,
            Availability.date >= date.today(),
            Availability.date <= date.today() + timedelta(days=14),
            Availability.status.in_([AvailabilityStatus.FREE, AvailabilityStatus.MAYBE]),
        ))
    )
    marked_free = avail_result.scalar() or 0

    total_possible = total_members * 14
    availability_pct = round((marked_free / total_possible * 100) if total_possible > 0 else 0, 1)

    # Per-member availability stats
    from shared.models.user import User
    member_stats = await db.execute(
        select(
            User.id, User.name,
            func.count(Availability.id).label("marked_days"),
            func.count(Availability.id).filter(
                Availability.status.in_([AvailabilityStatus.FREE, AvailabilityStatus.MAYBE])
            ).label("free_days"),
        )
        .select_from(User)
        .join(Membership, and_(
            Membership.user_id == User.id,
            Membership.group_id == group_id,
        ))
        .outerjoin(Availability, and_(
            Availability.user_id == User.id,
            Availability.group_id == group_id,
            Availability.date >= date.today(),
            Availability.date <= date.today() + timedelta(days=14),
        ))
        .group_by(User.id, User.name)
    )
    rows = member_stats.all()

    member_avail = [
        MemberAvailabilityStats(
            user_id=row.id,
            user_name=row.name,
            marked_days=row.marked_days,
            free_days=row.free_days,
        )
        for row in rows
    ]

    return GroupDashboardResponse(
        total_members=total_members,
        total_meetings=total_meetings,
        average_attendance=round(avg_att, 1),
        upcoming_meetings=upcoming_meetings,
        top_ideas=top_ideas,
        availability_pct=availability_pct,
        member_availability=member_avail,
    )


# ─── Online Members ─────────────────────────────────────────────────


redis_client: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
    return redis_client


@app.get("/api/v1/groups/{group_id}/online")
async def get_online_members(
    group_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    """Return list of online member user IDs in this group."""
    # Verify membership
    result = await db.execute(
        select(Membership).where(and_(
            Membership.user_id == user_id,
            Membership.group_id == group_id,
        ))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "You are not a member of this group")

    # Get all member IDs
    members_result = await db.execute(
        select(Membership.user_id).where(Membership.group_id == group_id)
    )
    member_ids = [row[0] for row in members_result.all()]

    # Check presence in Redis
    online_ids: list[int] = []
    try:
        r = await _get_redis()
        for mid in member_ids:
            exists = await r.exists(f"presence:user:{mid}")
            if exists:
                online_ids.append(mid)
    except Exception:
        # If Redis is down, return empty list
        pass

    return {"online_user_ids": online_ids}
