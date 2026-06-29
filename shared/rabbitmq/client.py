"""RabbitMQ async client for publishing and consuming events."""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Optional

import aio_pika
from aio_pika import Message, RobustChannel, RobustConnection, RobustExchange, RobustQueue
from aio_pika.abc import AbstractIncomingMessage

from shared.config import Settings
from shared.rabbitmq.events import DEAD_LETTER_EXCHANGE, EXCHANGE, EventType

logger = logging.getLogger("shared.rabbitmq")

HandlerType = Callable[[dict[str, Any]], Awaitable[None]]


class RabbitMQClient:
    """Async RabbitMQ client with auto-reconnect."""

    def __init__(self, settings: Settings) -> None:
        self._url = settings.rabbitmq_url
        self._connection: Optional[RobustConnection] = None
        self._channel: Optional[RobustChannel] = None
        self._exchange: Optional[RobustExchange] = None
        self._dlx: Optional[RobustExchange] = None
        self._handlers: dict[str, list[HandlerType]] = {}
        self._queues: list[RobustQueue] = []
        self._consuming = False

    async def connect(self) -> None:
        """Connect to RabbitMQ and declare exchanges."""
        self._connection = await aio_pika.connect_robust(
            self._url,
            client_properties={"app": "meetsync"},
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Main exchange (topic)
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Dead letter exchange
        self._dlx = await self._channel.declare_exchange(
            DEAD_LETTER_EXCHANGE,
            aio_pika.ExchangeType.FANOUT,
            durable=True,
        )

        logger.info("Connected to RabbitMQ, exchange declared")

    async def disconnect(self) -> None:
        """Close all connections."""
        self._consuming = False
        if self._connection:
            await self._connection.close()
        self._connection = None
        self._channel = None
        self._exchange = None
        logger.info("Disconnected from RabbitMQ")

    async def publish(self, event_type: EventType | str, payload: dict[str, Any]) -> None:
        """Publish an event to the main exchange."""
        if not self._exchange:
            raise RuntimeError("RabbitMQ not connected")

        routing_key = str(event_type)
        message = Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(message, routing_key=routing_key)
        logger.debug("Published event %s: %s", routing_key, payload)

    async def subscribe(
        self,
        event_types: list[EventType | str],
        handler: HandlerType,
        queue_name: Optional[str] = None,
    ) -> None:
        """Subscribe to one or more event types."""
        if not self._channel:
            raise RuntimeError("RabbitMQ not connected")

        queue_name = queue_name or f"{handler.__module__}.{handler.__name__}"

        # Create a queue bound to the exchange with the routing keys
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
            },
        )

        for et in event_types:
            routing_key = str(et)
            await queue.bind(self._exchange, routing_key=routing_key)
            logger.debug("Bound queue %s to %s", queue_name, routing_key)

        self._queues.append(queue)
        self._handlers.setdefault(queue_name, []).append(handler)

    async def start_consuming(self) -> None:
        """Start consuming from all subscribed queues."""
        if self._consuming:
            return
        self._consuming = True

        for queue in self._queues:
            await queue.consume(self._on_message)
            logger.info("Started consuming from %s", queue.name)

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        """Process a single message."""
        async with message.process(requeue=False):
            routing_key = message.routing_key
            try:
                payload = json.loads(message.body.decode())
                logger.debug("Received event %s", routing_key)

                # Find handlers for this queue
                queue_name = getattr(message, "queue_name", None) or getattr(
                    getattr(message, "queue", None), "name", ""
                )
                handlers = self._handlers.get(queue_name, [])

                for handler in handlers:
                    await handler(payload)

            except json.JSONDecodeError:
                logger.error("Failed to decode message body: %s", message.body)
            except Exception:
                logger.exception("Error processing event %s", routing_key)
                # Message is rejected and not requeued -> goes to DLX
                raise
