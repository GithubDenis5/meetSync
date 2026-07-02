"""Image upload handler — validate, process with Pillow, store to volume."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image

from app.config import GatewaySettings

logger = logging.getLogger("gateway.upload")

settings = GatewaySettings()
router = APIRouter(prefix="/api/v1/upload")

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

THUMB_SIZE = (150, 150)
MEDIUM_SIZE = (800, 800)


def _ensure_dirs() -> None:
    """Create upload directories if they don't exist."""
    base = Path(settings.upload_dir)
    for sub in ("original", "thumb", "medium"):
        (base / sub).mkdir(parents=True, exist_ok=True)


def _save_image(
    content: bytes,
    ext: str,
) -> dict[str, str]:
    """Save image in 3 sizes. Returns dict mapping size -> URL path."""
    base = Path(settings.upload_dir)
    file_id = f"{uuid.uuid4().hex}"
    filename = f"{file_id}{ext}"

    # Save original
    orig_path = base / "original" / filename
    orig_path.write_bytes(content)
    img = Image.open(orig_path)

    urls: dict[str, str] = {"original": f"/uploads/original/{filename}"}

    # Thumbnail
    thumb = img.copy()
    thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
    thumb_path = base / "thumb" / filename
    thumb.save(thumb_path)
    urls["thumb"] = f"/uploads/thumb/{filename}"

    # Medium
    medium = img.copy()
    medium.thumbnail(MEDIUM_SIZE, Image.LANCZOS)
    medium_path = base / "medium" / filename
    medium.save(medium_path)
    urls["medium"] = f"/uploads/medium/{filename}"

    logger.info("Saved image %s (%d bytes, %sx%s)", filename, len(content), img.width, img.height)
    return urls


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Upload an image. Returns URLs for original, thumb (150×150), and medium (800×800)."""
    # Validate mime type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    # Read content
    content = await file.read()
    if len(content) > settings.upload_max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content)} bytes. Max: {settings.upload_max_size} bytes",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    _ensure_dirs()
    ext = ALLOWED_MIME_TYPES[file.content_type]
    urls = _save_image(content, ext)

    return {
        "filename": file.filename or f"upload{ext}",
        "mimetype": file.content_type,
        "size": len(content),
        "urls": urls,
    }
