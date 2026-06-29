"""Custom exceptions for MeetSync services."""

from __future__ import annotations

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ForbiddenException(AppException):
    """Access denied."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    """Resource conflict."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class UnauthorizedException(AppException):
    """Authentication required."""

    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)
