"""Voting Service — create/manage votes, random/popular/category selection, auto-winner."""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import setup_logging

from app.config import VotingSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.vote import Vote, VoteOption, VoteResponse, VoteType, VoteStatus
from shared.models.idea import Idea
from shared.models.user import User
from shared.schemas.vote import (
    VoteCreateRequest, VoteResponseRequest,
    VoteOptionResponse, VoteResponse as VoteResponseSchema,
    VoteResultResponse,
)
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("voting-service")
logger = logging.getLogger("voting-service")
settings = VotingSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Voting Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "voting-service")
add_lifecycle(app, "voting-service", db_manager=db_manager)


@app.get("/health")
async def health() -> dict:
    return {"service": "voting-service", "status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()


@app.post("/api/v1/voting", response_model=VoteResponseSchema, status_code=201)
async def create_vote(
    body: VoteCreateRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Build options from ideas
    idea_ids = body.idea_ids or []

    if not idea_ids:
        # Auto-select ideas based on vote type
        query = select(Idea).where(and_(
            Idea.group_id == body.group_id,
            Idea.is_archived == False,
        ))
        if body.vote_type == VoteType.POPULAR:
            query = query.order_by(Idea.created_at.desc()).limit(5)
        elif body.vote_type == VoteType.CATEGORY and body.category:
            query = query.where(Idea.category == body.category).limit(5)
        else:  # RANDOM
            result = await db.execute(query)
            all_ideas = result.scalars().all()
            idea_ids = [i.id for i in random.sample(all_ideas, min(5, len(all_ideas)))] if all_ideas else []

    if not idea_ids:
        raise HTTPException(400, "No ideas available for voting")

    ends_at = datetime.now(timezone.utc) + timedelta(hours=body.duration_hours)

    vote = Vote(
        group_id=body.group_id,
        title=body.title,
        vote_type=VoteType(body.vote_type),
        category=body.category,
        ends_at=ends_at,
    )
    db.add(vote)
    await db.flush()

    for iid in idea_ids:
        db.add(VoteOption(vote_id=vote.id, idea_id=iid))

    return await _vote_to_response(vote, db)


async def _vote_to_response(vote, db):
    # Get options with vote counts
    options_result = await db.execute(
        select(VoteOption).where(VoteOption.vote_id == vote.id)
    )
    options = options_result.scalars().all()

    option_responses = []
    for opt in options:
        idea_result = await db.execute(select(Idea).where(Idea.id == opt.idea_id))
        idea = idea_result.scalar_one_or_none()
        count_result = await db.execute(
            select(func.count()).select_from(VoteResponse)
            .where(VoteResponse.option_id == opt.id)
        )
        count = count_result.scalar()

        option_responses.append(VoteOptionResponse(
            id=opt.id, idea_id=opt.idea_id,
            idea_title=idea.title if idea else "Unknown",
            votes_count=count or 0,
        ))

    return VoteResponseSchema(
        id=vote.id, group_id=vote.group_id, title=vote.title,
        vote_type=str(vote.vote_type), status=str(vote.status),
        category=vote.category, options=option_responses,
        ends_at=vote.ends_at, created_at=vote.created_at,
    )


@app.get("/api/v1/voting", response_model=list[VoteResponseSchema])
async def list_votes(
    group_id: int = Query(...),
    active_only: bool = False,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    query = select(Vote).where(Vote.group_id == group_id)
    if active_only:
        query = query.where(Vote.status == VoteStatus.ACTIVE)
    query = query.order_by(Vote.created_at.desc())

    result = await db.execute(query)
    votes = result.scalars().all()
    return [await _vote_to_response(v, db) for v in votes]


@app.get("/api/v1/voting/{vote_id}", response_model=VoteResponseSchema)
async def get_vote(vote_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Vote).where(Vote.id == vote_id))
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(404, "Vote not found")
    return await _vote_to_response(vote, db)


@app.post("/api/v1/voting/{vote_id}/vote")
async def cast_vote(
    vote_id: int,
    body: VoteResponseRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Check vote exists and is active
    result = await db.execute(select(Vote).where(Vote.id == vote_id))
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(404, "Vote not found")
    if vote.status != VoteStatus.ACTIVE:
        raise HTTPException(400, "Vote is not active")
    if datetime.now(timezone.utc) > vote.ends_at:
        vote.status = VoteStatus.FINISHED
        raise HTTPException(400, "Vote has ended")

    # Check if user already voted
    existing = await db.execute(
        select(VoteResponse).where(and_(
            VoteResponse.vote_id == vote_id,
            VoteResponse.user_id == user_id,
        ))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Already voted")

    # Verify option belongs to this vote
    opt_result = await db.execute(
        select(VoteOption).where(and_(
            VoteOption.id == body.option_id,
            VoteOption.vote_id == vote_id,
        ))
    )
    if not opt_result.scalar_one_or_none():
        raise HTTPException(400, "Invalid option")

    response = VoteResponse(vote_id=vote_id, user_id=user_id, option_id=body.option_id)
    db.add(response)
    logger.info("User %d voted in vote %d", user_id, vote_id)
    return {"detail": "Vote cast"}


@app.get("/api/v1/voting/{vote_id}/result", response_model=VoteResultResponse)
async def get_vote_result(vote_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Vote).where(Vote.id == vote_id))
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(404, "Vote not found")

    options_result = await db.execute(
        select(VoteOption).where(VoteOption.vote_id == vote.id)
    )
    options = options_result.scalars().all()

    winner = None
    total_votes = 0
    max_votes = 0

    for opt in options:
        count_result = await db.execute(
            select(func.count()).select_from(VoteResponse)
            .where(VoteResponse.option_id == opt.id)
        )
        count = count_result.scalar() or 0
        total_votes += count

        if count > max_votes:
            max_votes = count
            idea_result = await db.execute(select(Idea).where(Idea.id == opt.idea_id))
            idea = idea_result.scalar_one_or_none()
            if max_votes > 0:
                winner = VoteOptionResponse(
                    id=opt.id, idea_id=opt.idea_id,
                    idea_title=idea.title if idea else "Unknown",
                    votes_count=count,
                )

    return VoteResultResponse(
        vote_id=vote.id, title=vote.title, winner=winner,
        total_votes=total_votes, finished_at=vote.finished_at,
    )
