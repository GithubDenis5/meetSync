"""Prometheus metrics utilities."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest

# HTTP metrics
http_request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Business metrics
active_users = Gauge("active_users_total", "Total active users")
active_groups = Gauge("active_groups_total", "Total active groups")
votes_active = Gauge("votes_active_total", "Currently active votes")
notifications_sent = Counter("notifications_sent_total", "Total notifications sent")
events_published = Counter("events_published_total", "Total events published", ["event_type"])


def get_metrics():
    """Return latest metrics."""
    return generate_latest()
