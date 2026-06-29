"""Auth service REST API routes."""

from __future__ import annotations

import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AuthSettings
from app.services import AuthService
from shared.database import DatabaseManager
from shared.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TelegramAuthRequest,
    TokenResponse,
)

logger = logging.getLogger("auth-service.routes")

settings = AuthSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
auth_service = AuthService(
    jwt_secret=settings.jwt_secret_key,
    jwt_algorithm=settings.jwt_algorithm,
    access_expire_minutes=settings.jwt_access_token_expire_minutes,
    refresh_expire_days=settings.jwt_refresh_token_expire_days,
    redis_client=redis_client,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(db_manager.get_session)):
    user, access, refresh = await auth_service.register(db, body.name, body.email, body.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(db_manager.get_session)):
    user, access, refresh = await auth_service.login(db, body.email, body.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(db_manager.get_session)):
    access, refresh = await auth_service.refresh(db, body.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(db_manager.get_session)):
    user, access, refresh = await auth_service.telegram_auth(db, body.telegram_id, body.username)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout")
async def logout(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ")
    # Get user_id from token
    payload = auth_service.decode_token(token)
    user_id = int(payload["sub"])
    await auth_service.logout(user_id, token)
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=AuthUserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(db_manager.get_session)):
    from sqlalchemy import select
    from app.models import User

    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ")
    payload = auth_service.decode_token(token)
    user_id = int(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from shared.exceptions import NotFoundException
        raise NotFoundException("User not found")

    return AuthUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        telegram_id=user.telegram_id,
        username=user.username,
        avatar=user.avatar,
        timezone=user.timezone,
    )
