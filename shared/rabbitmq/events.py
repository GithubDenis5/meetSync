"""RabbitMQ event type definitions."""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """All RabbitMQ event types in the system."""

    USER_REGISTERED = "UserRegistered"
    USER_JOINED_GROUP = "UserJoinedGroup"
    USER_LEFT_GROUP = "UserLeftGroup"
    IDEA_CREATED = "IdeaCreated"
    IDEA_ARCHIVED = "IdeaArchived"
    AVAILABILITY_UPDATED = "AvailabilityUpdated"
    AVAILABILITY_CONFIRMED = "AvailabilityConfirmed"
    MEETING_POSSIBLE = "MeetingPossible"
    MEETING_CANCELLED = "MeetingCancelled"
    VOTING_STARTED = "VotingStarted"
    VOTING_FINISHED = "VotingFinished"
    REMINDER_NEEDED = "ReminderNeeded"
    NOTIFICATION_SENT = "NotificationSent"


# Exchange and queue naming
EXCHANGE = "meetsync.events"
DEAD_LETTER_EXCHANGE = "meetsync.dlx"
