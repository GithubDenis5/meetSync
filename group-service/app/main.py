"""Group Service — groups, memberships, roles, invites."""

from __future__ import annotations

import logging
import secrets

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import GroupSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.group import Group, Membership, GroupRole
from shared.models.user import User
from shared.schemas.group import (
    GroupCreateRequest, GroupUpdateRequest, GroupResponse,
    MemberResponse, JoinGroupRequest, MemberRoleUpdateRequest,
)

logger = logging.getLogger("group-service")
settings = GroupSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Group Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"service": "group-service", "status": "ok"}


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
