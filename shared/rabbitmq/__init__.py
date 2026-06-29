"""RabbitMQ async client for publishing and consuming events."""

from shared.rabbitmq.client import RabbitMQClient
from shared.rabbitmq.events import EventType, DEAD_LETTER_EXCHANGE, EXCHANGE

__all__ = [
    "RabbitMQClient",
    "EventType",
    "DEAD_LETTER_EXCHANGE",
    "EXCHANGE",
]
