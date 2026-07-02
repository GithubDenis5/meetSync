"""Notification Service — WebSocket and event-driven notifications."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import setup_logging

from app.config import NotificationSettings
from shared.database import DatabaseManager
from shared.auth import AuthHandler
from shared.models.notification import Notification
from shared.rabbitmq.client import RabbitMQClient
from shared.rabbitmq.events import EventType
from shared.schemas.notification import NotificationResponse
from shared.app_health import add_lifecycle
from shared.metrics import add_prometheus_middleware, websocket_connections_active

PRESENCE_TTL = 60  # seconds before user is considered offline

setup_logging("notification-service")
logger = logging.getLogger("notification-service")
settings = NotificationSettings()
db_manager = DatabaseManager(settings)  # type: ignore[arg-type]
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Notification Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "notification-service")
add_lifecycle(app, "notification-service", db_manager=db_manager)


@app.on_event("shutdown")
async def shutdown():
    if rmq:
        await rmq.disconnect()
    if redis_client:
        await redis_client.close()
    await db_manager.close()


# WebSocket connections: user_id -> set of websockets
active_connections: dict[int, set[WebSocket]] = {}
rmq: Optional[RabbitMQClient] = None
redis_client: Optional[aioredis.Redis] = None


async def _set_presence(user_id: int) -> None:
    """Mark user as online in Redis with a TTL."""
    if redis_client:
        await redis_client.set(f"presence:user:{user_id}", "1", ex=PRESENCE_TTL)


async def _clear_presence(user_id: int) -> None:
    """Remove user presence from Redis."""
    if redis_client:
        await redis_client.delete(f"presence:user:{user_id}")


@app.get("/health")
async def health():
    return {"service": "notification-service", "status": "ok"}


@app.on_event("startup")
async def startup():
    global rmq, redis_client
    rmq = RabbitMQClient(settings)  # type: ignore[arg-type]
    redis_client = aioredis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )

    # Retry connecting to RabbitMQ with exponential backoff.
    # DNS / RabbitMQ may not be immediately resolvable at container start.
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            await rmq.connect()
            break
        except Exception as e:
            if attempt == max_attempts:
                logger.error("Failed to connect to RabbitMQ after %d attempts: %s", max_attempts, e)
                raise
            logger.warning("RabbitMQ connection attempt %d/%d failed: %s. Retrying...", attempt, max_attempts, e)
            await asyncio.sleep(attempt * 2)

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

    # Extract group_id from payload if present
    group_id = payload.get("group_id")

    # Save to database
    async with db_manager.session() as db:
        notification = Notification(
            user_id=user_id,
            group_id=group_id,
            type=event_type,
            title=title,
            message=message,
            data=json.dumps(data),
        )
        db.add(notification)
        await db.flush()

        notification_json = json.dumps({
            "type": "notification",
            "payload": {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "data": data,
                "created_at": notification.created_at.isoformat(),
            },
        })

        # Send to personal WebSocket
        if user_id in active_connections:
            dead_connections = set()
            for ws in list(active_connections[user_id]):
                try:
                    await ws.send_text(notification_json)
                except Exception:
                    dead_connections.add(ws)
            active_connections[user_id] -= dead_connections

        # Broadcast to group connections
        if group_id and group_id in group_connections:
            for uid, ws_set in group_connections[group_id].items():
                dead_ws = set()
                for ws in list(ws_set):
                    try:
                        await ws.send_text(notification_json)
                    except Exception:
                        dead_ws.add(ws)
                group_connections[group_id][uid] -= dead_ws


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
    websocket_connections_active.set(sum(len(ws_set) for ws_set in active_connections.values()))

    # Mark user as online
    await _set_presence(user_id)

    logger.info("WebSocket connected: user=%d", user_id)

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await _set_presence(user_id)
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.get(user_id, set()).discard(ws)
        if not active_connections.get(user_id):
            active_connections.pop(user_id, None)
        websocket_connections_active.set(sum(len(ws_set) for ws_set in active_connections.values()) if active_connections else 0)
        await _clear_presence(user_id)
        logger.info("WebSocket disconnected: user=%d", user_id)


# ─── Group WebSocket ──────────────────────────────────────────────

group_connections: dict[int, dict[int, set[WebSocket]]] = {}  # group_id -> user_id -> set[ws]


@app.websocket("/ws/group/{token}/{group_id}")
async def websocket_group_endpoint(ws: WebSocket, token: str, group_id: int):
    """WebSocket for group activity feed, authenticated via JWT token."""
    try:
        payload = auth.decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await ws.close(code=4001)
        return

    await ws.accept()

    if group_id not in group_connections:
        group_connections[group_id] = {}
    if user_id not in group_connections[group_id]:
        group_connections[group_id][user_id] = set()
    group_connections[group_id][user_id].add(ws)

    # Mark user as online
    await _set_presence(user_id)

    logger.info("Group WebSocket connected: user=%d group=%d", user_id, group_id)

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await _set_presence(user_id)
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        group_connections.get(group_id, {}).get(user_id, set()).discard(ws)
        if not group_connections.get(group_id, {}).get(user_id):
            group_connections[group_id].pop(user_id, None)
        if not group_connections.get(group_id):
            group_connections.pop(group_id, None)
        await _clear_presence(user_id)
        logger.info("Group WebSocket disconnected: user=%d group=%d", user_id, group_id)


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


@app.get("/api/v1/notifications/events", response_model=list[NotificationResponse])
async def list_group_events(
    group_id: int = Query(...),
    limit: int = Query(default=50, le=100),
    user_id: int = Depends(auth.get_current_user_id),
    db: AsyncSession = Depends(db_manager.get_session),
):
    """Get event history for a group."""
    query = (
        select(Notification)
        .where(Notification.group_id == group_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    return [NotificationResponse.model_validate(n) for n in result.scalars().all()]
