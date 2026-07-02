"""Telegram Service — Telegram API integration, messages, inline buttons, polling + webhook."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import setup_logging

from app.config import TelegramSettings
from shared.rabbitmq.client import RabbitMQClient
from shared.rabbitmq.events import EventType
from shared.auth import AuthHandler
from shared.metrics import add_prometheus_middleware
from shared.app_health import add_lifecycle

setup_logging("telegram-service")
logger = logging.getLogger("telegram-service")
settings = TelegramSettings()
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Telegram Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

add_prometheus_middleware(app, "telegram-service")
add_lifecycle(app, "telegram-service")

rmq: Optional[RabbitMQClient] = None
telegram_api = httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{settings.telegram_bot_token or ''}", timeout=httpx.Timeout(35.0, connect=10.0))

_polling_task: Optional[asyncio.Task] = None
_last_update_id: int = 0


def _bot_enabled() -> bool:
    return bool(settings.telegram_bot_token)


# ─── Lifecycle ──────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    global rmq, _polling_task
    rmq = RabbitMQClient(settings)  # type: ignore[arg-type]
    await rmq.connect()

    if _bot_enabled():
        # Try webhook first (for production deployments), fall back to polling
        ok = await _try_set_webhook()
        if not ok:
            logger.info("Webhook setup failed — starting long-polling instead")
            _polling_task = asyncio.create_task(_poll_loop())
        else:
            logger.info("Webhook set successfully")

        await rmq.subscribe(
            [EventType.VOTING_FINISHED, EventType.MEETING_POSSIBLE,
             EventType.REMINDER_NEEDED, EventType.NOTIFICATION_SENT],
            handle_telegram_event,
            "telegram.notifications",
        )
        await rmq.start_consuming()


@app.on_event("shutdown")
async def shutdown():
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        _polling_task = None
    await telegram_api.aclose()
    if rmq:
        await rmq.disconnect()


# ─── Webhook (production) ────────────────────────────────────────


async def _try_set_webhook() -> bool:
    """Try to set the Telegram webhook. Returns True on success."""
    webhook_url = settings.telegram_webhook_url
    if not webhook_url:
        return False
    try:
        resp = await telegram_api.post(
            "/setWebhook",
            json={"url": f"{webhook_url}/webhook"},
        )
        data = resp.json()
        logger.info("Telegram webhook response: %s", data)
        return data.get("ok", False)
    except Exception as e:
        logger.warning("Failed to set webhook: %s", e)
        return False


# ─── Polling (local dev) ─────────────────────────────────────────


async def _poll_loop() -> None:
    """Long-poll Telegram API for updates (fallback when no public webhook URL)."""
    global _last_update_id
    logger.info("Telegram polling started")

    while True:
        try:
            resp = await telegram_api.get(
                "/getUpdates",
                params={
                    "offset": _last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": json.dumps(["message", "callback_query"]),
                },
            )
            data = resp.json()
            if not data.get("ok"):
                await asyncio.sleep(5)
                continue

            for update in data.get("result", []):
                _last_update_id = update["update_id"]
                await _process_update(update)

        except asyncio.CancelledError:
            logger.info("Telegram polling cancelled")
            break
        except Exception as e:
            logger.error("Telegram polling error: %s", repr(e))
            await asyncio.sleep(5)


async def _process_update(update: dict) -> None:
    """Process a single Telegram update (message or callback query)."""
    try:
        # Callback query (inline button press)
        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq.get("data", "")
            chat_id = cq.get("message", {}).get("chat", {}).get("id")
            user_id = cq.get("from", {}).get("id")
            logger.info("Callback query: user=%s chat=%s data=%s", user_id, chat_id, data)
            await send_message(chat_id, f"You pressed: {data}")

        # Text message
        if "message" in update and "text" in update["message"]:
            msg = update["message"]
            text = msg["text"]
            chat_id = msg["chat"]["id"]
            user_name = msg["from"].get("first_name", "User")

            if text.startswith("/start"):
                parts = text.split()
                if len(parts) > 1:
                    invite_code = parts[1]
                    if rmq:
                        await rmq.publish(EventType.USER_JOINED_GROUP, {
                            "telegram_id": str(chat_id),
                            "invite_code": invite_code,
                        })
                    await send_message(chat_id, "Processing your invite link...")
                else:
                    await send_message(
                        chat_id,
                        f"Hey {user_name}! 👋\n\n"
                        "I'm MeetSync bot. Use an invite link from your group to join, "
                        "or log in at the web app to get started."
                    )
            else:
                # Default reply for unrecognized commands
                await send_message(
                    chat_id,
                    "Welcome! Use /start to see available options."
                )

    except Exception as e:
        logger.error("Error processing Telegram update: %s", e)


# ─── Event handlers ──────────────────────────────────────────────


async def handle_telegram_event(payload: dict) -> None:
    """Send Telegram notifications for events."""
    if not _bot_enabled():
        logger.debug("Telegram bot not configured, skipping message")
        return

    chat_id = payload.get("telegram_id") or payload.get("chat_id")
    message = payload.get("message") or payload.get("title", "")
    buttons = payload.get("buttons")

    if not chat_id:
        logger.warning("No chat_id in payload: %s", payload)
        return

    await send_message(chat_id, message, buttons)


async def send_message(chat_id: str | int, text: str, buttons: Optional[list[list[dict]]] = None) -> dict:
    """Send a Telegram message with optional inline buttons."""
    if not _bot_enabled():
        return {"ok": False, "error": "Bot not configured"}

    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    if buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})

    try:
        resp = await telegram_api.post("/sendMessage", json=payload)
        result = resp.json()
        logger.debug("Telegram sendMessage: %s", result)
        return result
    except Exception as e:
        logger.error("Telegram sendMessage failed: %s", e)
        return {"ok": False, "error": str(e)}


# ─── REST API ───────────────────────────────────────────────────


@app.post("/api/v1/telegram/send")
async def api_send_message(
    chat_id: str, text: str,
    user_id: int = Depends(auth.get_current_user_id),
):
    return await send_message(chat_id, text)


@app.post("/api/v1/telegram/send-buttons")
async def api_send_buttons(
    chat_id: str, text: str, buttons: list[list[dict]],
    user_id: int = Depends(auth.get_current_user_id),
):
    return await send_message(chat_id, text, buttons)


@app.get("/api/v1/telegram/me")
async def get_bot_info():
    if not _bot_enabled():
        raise HTTPException(400, "Bot not configured")
    resp = await telegram_api.get("/getMe")
    return resp.json()


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive webhook updates from Telegram (used in production)."""
    body = await request.json()
    logger.info("Telegram webhook received: %s", json.dumps(body, ensure_ascii=False)[:500])
    await _process_update(body)
    return {"ok": True}
