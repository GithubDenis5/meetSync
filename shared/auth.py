"""Authentication utilities: JWT, password hashing, and dependency injection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Request, HTTPException, status

from shared.config import Settings


class AuthHandler:
    """Handles JWT tokens and password hashing."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire = getattr(settings, "jwt_access_token_expire_minutes", 30)
        self._refresh_expire = getattr(settings, "jwt_refresh_token_expire_days", 7)

    # ─── Password ───────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    # ─── JWT Access Token ────────────────────────────────────────

    def create_access_token(self, user_id: int, extra: Optional[dict] = None) -> str:
        """Create a short-lived JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire),
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """Create a long-lived JWT refresh token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token. Raises on expiry/invalid signature."""
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    def get_current_user_id(self, request: Request) -> int:
        """Extract user_id from the JWT in the Authorization header."""
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )
        token = auth.removeprefix("Bearer ")
        payload = self.decode_token(token)
        return int(payload["sub"])
