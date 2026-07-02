"""User Service — user profiles and settings."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import setup_logging

from app.config import UserSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.schemas.user import UserResponse, UserUpdateRequest
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware

setup_logging("user-service")
logger = logging.getLogger("user-service")
settings = UserSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - User Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "user-service")
add_lifecycle(app, "user-service", db_manager=db_manager)


@app.get("/health")
async def health() -> dict:
    return {"service": "user-service", "status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()


@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_me(user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    from shared.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse.model_validate(user)


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(db_manager.get_session)):
    from shared.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse.model_validate(user)


@app.patch("/api/v1/users/me", response_model=UserResponse)
async def update_me(body: UserUpdateRequest, user_id: int = Depends(auth.get_current_user_id), db: AsyncSession = Depends(db_manager.get_session)):
    from shared.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if body.name is not None:
        user.name = body.name
    if body.avatar is not None:
        user.avatar = body.avatar
    if body.timezone is not None:
        user.timezone = body.timezone
    return UserResponse.model_validate(user)


@app.get("/api/v1/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_by_telegram(telegram_id: str, db: AsyncSession = Depends(db_manager.get_session)):
    from shared.models.user import User
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse.model_validate(user)
