"""Auth service business logic."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, RefreshToken
from shared.exceptions import ConflictException, NotFoundException, UnauthorizedException

logger = logging.getLogger("auth-service.services")


class AuthService:
    """Authentication business logic."""

    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
        redis_client: aioredis.Redis,
    ) -> None:
        self._secret = jwt_secret
        self._algorithm = jwt_algorithm
        self._access_expire = access_expire_minutes
        self._refresh_expire = refresh_expire_days
        self._redis = redis_client

    # ─── Password ──────────────────────────────────────────────

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    # ─── JWT ───────────────────────────────────────────────────

    def _create_access_token(self, user_id: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def _create_refresh_token(self, user_id: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Invalid token")

    # ─── Registration ─────────────────────────────────────────

    async def register(
        self,
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictException("Email already registered")

        user = User(
            name=name,
            email=email,
            hashed_password=self._hash_password(password),
        )
        db.add(user)
        await db.flush()

        # Generate tokens
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        # Store refresh token
        payload = self.decode_token(refresh_token)
        db.add(RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        ))

        logger.info("User registered: id=%d email=%s", user.id, email)
        return user, access_token, refresh_token

    # ─── Login ────────────────────────────────────────────────

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password:
            raise UnauthorizedException("Invalid email or password")

        if not self._verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        payload = self.decode_token(refresh_token)
        db.add(RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        ))

        return user, access_token, refresh_token

    # ─── Refresh ──────────────────────────────────────────────

    async def refresh(self, db: AsyncSession, refresh_token: str) -> tuple[str, str]:
        payload = self.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        # Check if token exists and is not revoked
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,
            )
        )
        stored = result.scalar_one_or_none()
        if not stored:
            raise UnauthorizedException("Refresh token has been revoked")

        # Revoke old token
        stored.is_revoked = True

        user_id = int(payload["sub"])
        new_access = self._create_access_token(user_id)
        new_refresh = self._create_refresh_token(user_id)

        new_payload = self.decode_token(new_refresh)
        db.add(RefreshToken(
            user_id=user_id,
            token=new_refresh,
            expires_at=datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc),
        ))

        return new_access, new_refresh

    # ─── Telegram Auth ────────────────────────────────────────

    async def telegram_auth(
        self,
        db: AsyncSession,
        telegram_id: str,
        username: Optional[str] = None,
    ) -> tuple[User, str, str]:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                name=username or f"tg_{telegram_id}",
                telegram_id=telegram_id,
                username=username,
            )
            db.add(user)
            await db.flush()
            logger.info("User registered via Telegram: id=%d tg=%s", user.id, telegram_id)

        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        payload = self.decode_token(refresh_token)
        db.add(RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        ))

        return user, access_token, refresh_token

    # ─── Logout ────────────────────────────────────────────────

    async def logout(self, user_id: int, access_token: str) -> None:
        # Blacklist the access token in Redis until it expires
        payload = self.decode_token(access_token)
        exp = payload.get("exp", 0)
        ttl = max(0, exp - datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            await self._redis.setex(f"blacklist:{access_token}", int(ttl), "1")
        logger.info("User logged out: id=%d", user_id)
