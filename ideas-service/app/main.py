"""Ideas Service — idea bank with reactions and comments."""

from __future__ import annotations

import json
import logging
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_, func, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from shared.logging import setup_logging

from app.config import IdeasSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.idea import Idea, IdeaReaction, ReactionType, IdeaComment
from shared.models.user import User
from shared.schemas.idea import (
    IdeaCreateRequest, IdeaUpdateRequest, IdeaResponse,
    ReactionRequest, CommentRequest, CommentResponse,
)
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("ideas-service")
logger = logging.getLogger("ideas-service")
settings = IdeasSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Ideas Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "ideas-service")
add_lifecycle(app, "ideas-service", db_manager=db_manager)


@app.get("/health")
async def health() -> dict:
    return {"service": "ideas-service", "status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()


def _get_reaction_counts(idea) -> dict[str, int]:
    """Build reaction count dict from an idea's reactions."""
    counts = Counter(r.reaction for r in idea.reactions)
    return {str(k): v for k, v in counts.items()}


async def _idea_to_response(idea) -> IdeaResponse:
    resp = IdeaResponse(
        id=idea.id,
        group_id=idea.group_id,
        title=idea.title,
        description=idea.description,
        cost=idea.cost,
        category=idea.category,
        photo_url=idea.photo_url,
        links=idea.links,
        tags=idea.tags,
        location=idea.location,
        suggestor_id=idea.suggestor_id,
        suggestor_name=idea.suggestor.name if idea.suggestor else None,
        is_archived=idea.is_archived,
        reactions=_get_reaction_counts(idea),
        created_at=idea.created_at,
    )
    return resp


@app.get("/api/v1/ideas", response_model=list[IdeaResponse])
async def list_ideas(
    group_id: int = Query(...),
    category: str | None = None,
    archived: bool = False,
    db: AsyncSession = Depends(db_manager.get_session),
):
    query = select(Idea).where(and_(
        Idea.group_id == group_id,
        Idea.is_archived == archived,
    ))
    if category:
        query = query.where(Idea.category == category)
    query = query.order_by(Idea.created_at.desc())

    result = await db.execute(query)
    ideas = result.scalars().all()

    # Load reactions for all ideas
    responses = []
    for idea in ideas:
        resp = await _idea_to_response(idea)
        responses.append(resp)
    return responses


# ─── Search ────────────────────────────────────────────────────────


@app.get("/api/v1/ideas/search", response_model=list[IdeaResponse])
async def search_ideas(
    q: str = Query(..., min_length=1),
    group_id: int = Query(...),
    category: str | None = None,
    archived: bool = False,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    """Full-text search across ideas using PostgreSQL tsvector."""
    conditions = [
        text("search_vector @@ plainto_tsquery('english', :q)").bindparams(q=q),
        Idea.group_id == group_id,
        Idea.is_archived == archived,
    ]
    if category:
        conditions.append(Idea.category == category)

    query = (
        select(Idea)
        .options(selectinload(Idea.reactions), selectinload(Idea.suggestor))
        .where(and_(*conditions))
        .order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").bindparams(q=q))
    )

    result = await db.execute(query)
    ideas = result.scalars().all()
    return [await _idea_to_response(i) for i in ideas]


@app.post("/api/v1/ideas", response_model=IdeaResponse, status_code=201)
async def create_idea(
    body: IdeaCreateRequest,
    group_id: int = Query(...),
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    idea = Idea(
        group_id=group_id,
        title=body.title,
        description=body.description,
        cost=body.cost,
        category=body.category,
        photo_url=body.photo_url,
        links=body.links,
        tags=body.tags,
        location=body.location,
        suggestor_id=user_id,
    )
    db.add(idea)
    await db.flush()
    await db.refresh(idea, ["suggestor", "reactions"])
    return await _idea_to_response(idea)


@app.get("/api/v1/ideas/{idea_id}", response_model=IdeaResponse)
async def get_idea(idea_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    return await _idea_to_response(idea)


@app.patch("/api/v1/ideas/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: int,
    body: IdeaUpdateRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    if idea.suggestor_id != user_id:
        raise HTTPException(403, "Only the author can edit")

    if body.title is not None: idea.title = body.title
    if body.description is not None: idea.description = body.description
    if body.cost is not None: idea.cost = body.cost
    if body.category is not None: idea.category = body.category
    if body.photo_url is not None: idea.photo_url = body.photo_url
    if body.links is not None: idea.links = body.links
    if body.tags is not None: idea.tags = body.tags
    if body.location is not None: idea.location = body.location

    return await _idea_to_response(idea)


@app.delete("/api/v1/ideas/{idea_id}", status_code=204)
async def delete_idea(
    idea_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    if idea.suggestor_id != user_id:
        raise HTTPException(403, "Only the author can delete")
    await db.delete(idea)


@app.post("/api/v1/ideas/{idea_id}/archive", response_model=IdeaResponse)
async def archive_idea(
    idea_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    idea.is_archived = True
    return await _idea_to_response(idea)


@app.post("/api/v1/ideas/{idea_id}/unarchive", response_model=IdeaResponse)
async def unarchive_idea(
    idea_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    idea.is_archived = False
    return await _idea_to_response(idea)


# ─── Reactions ──────────────────────────────────────────────────


@app.post("/api/v1/ideas/{idea_id}/reactions")
async def add_reaction(
    idea_id: int,
    body: ReactionRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    # Check idea exists
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Idea not found")

    # Remove existing reaction from this user (toggle)
    await db.execute(
        delete(IdeaReaction).where(and_(
            IdeaReaction.idea_id == idea_id,
            IdeaReaction.user_id == user_id,
        ))
    )

    reaction = IdeaReaction(idea_id=idea_id, user_id=user_id, reaction=ReactionType(body.reaction))
    db.add(reaction)
    return {"detail": "Reaction added"}


@app.get("/api/v1/ideas/{idea_id}/reactions")
async def get_reactions(idea_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(
        select(IdeaReaction, User).join(User, IdeaReaction.user_id == User.id)
        .where(IdeaReaction.idea_id == idea_id)
    )
    rows = result.all()
    return [
        {"user_id": r.IdeaReaction.user_id, "user_name": r.User.name, "reaction": r.IdeaReaction.reaction}
        for r in rows
    ]


# ─── Comments ────────────────────────────────────────────────────


@app.get("/api/v1/ideas/{idea_id}/comments", response_model=list[CommentResponse])
async def list_comments(idea_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    result = await db.execute(
        select(IdeaComment, User).join(User, IdeaComment.user_id == User.id)
        .where(IdeaComment.idea_id == idea_id)
        .order_by(IdeaComment.created_at)
    )
    rows = result.all()
    return [
        CommentResponse(id=r.IdeaComment.id, idea_id=r.IdeaComment.idea_id,
                         user_id=r.IdeaComment.user_id, user_name=r.User.name,
                         text=r.IdeaComment.text, created_at=r.IdeaComment.created_at)
        for r in rows
    ]


@app.post("/api/v1/ideas/{idea_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    idea_id: int,
    body: CommentRequest,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Idea not found")

    comment = IdeaComment(idea_id=idea_id, user_id=user_id, text=body.text)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    # Get user name
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    return CommentResponse(
        id=comment.id, idea_id=comment.idea_id, user_id=comment.user_id,
        user_name=user.name, text=comment.text, created_at=comment.created_at,
    )
