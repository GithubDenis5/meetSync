"""Notification Service — WebSocket and event-driven notifications."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import NotificationSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.notification import Notification
from shared.rabbitmq.client import RabbitMQClient
from shared.rabbitmq.events import EventType
from shared.schemas.notification import NotificationResponse

logger = logging.getLogger("notification-service")
settings = NotificationSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Notification Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# WebSocket connections: user_id -> set of websockets
active_connections: dict[int, set[WebSocket]] = {}
rmq: Optional[RabbitMQClient] = None


@app.get("/health")
async def health():
    return {"service": "notification-service", "status": "ok"}


@app.on_event("startup")
async def startup():
    global rmq
    rmq = RabbitMQClient(settings)  # type: ignore[arg-type]
    await rmq.connect()

    # Subscribe to all events that need notification delivery
    notification_events = [
        EventType.USER_REGISTERED,
        EventType.USER_JOINED_GROUP,
        EventType.USER_LEFT_GROUP,
        EventType.IDEA_CREATED,
        EventType.VOTING_STARTED,
        EventType.VOTING_FINISHED,
        EventType.MEETING_POSSIBLE,
        EventType.MEETING_CANCELLED,
        EventType.REMINDER_NEEDED,
        EventType.AVAILABILITY_CONFIRMED,
    ]
    await rmq.subscribe(notification_events, handle_notification_event, "notifications.handler")
    await rmq.start_consuming()


async def handle_notification_event(payload: dict) -> None:
    """Process an incoming event and send notifications."""
    event_type = payload.get("event_type", "unknown")
    user_id = payload.get("user_id")
    title = payload.get("title", "New notification")
    message = payload.get("message", "")
    data = payload.get("data", {})

    logger.info("Processing notification event: %s for user %s", event_type, user_id)

    if not user_id:
        return

    # Save to database
    async with db_manager.session() as db:
        notification = Notification(
            user_id=user_id,
            type=event_type,
            title=title,
            message=message,
            data=json.dumps(data),
        )
        db.add(notification)
        await db.flush()

        # Send via WebSocket if connected
        if user_id in active_connections:
            ws_message = json.dumps({
                "type": "notification",
                "payload": {
                    "id": notification.id,
                    "type": notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                },
            })
            dead_connections = set()
            for ws in active_connections[user_id]:
                try:
                    await ws.send_text(ws_message)
                except Exception:
                    dead_connections.add(ws)
            active_connections[user_id] -= dead_connections


# ─── WebSocket ──────────────────────────────────────────────────


@app.websocket("/ws/{token}")
async def websocket_endpoint(ws: WebSocket, token: str):
    """WebSocket connection authenticated via JWT token."""
    try:
        payload = auth.decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await ws.close(code=4001)
        return

    await ws.accept()

    if user_id not in active_connections:
        active_connections[user_id] = set()
    active_connections[user_id].add(ws)

    logger.info("WebSocket connected: user=%d", user_id)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.get(user_id, set()).discard(ws)
        if not active_connections.get(user_id):
            active_connections.pop(user_id, None)
        logger.info("WebSocket disconnected: user=%d", user_id)


# ─── REST API ───────────────────────────────────────────────────


@app.get("/api/v1/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return [NotificationResponse.model_validate(n) for n in result.scalars().all()]


@app.post("/api/v1/notifications/{notification_id}/read")
async def mark_read(
    notification_id: int,
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    await db.execute(
        update(Notification).where(and_(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )).values(is_read=True)
    )
    return {"detail": "Marked as read"}


@app.post("/api/v1/notifications/read-all")
async def mark_all_read(
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    await db.execute(
        update(Notification).where(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        ).values(is_read=True)
    )
    return {"detail": "All marked as read"}


@app.get("/api/v1/notifications/unread-count")
async def unread_count(
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).select_from(Notification)
        .where(and_(Notification.user_id == user_id, Notification.is_read == False))
    )
    return {"count": result.scalar() or 0}
