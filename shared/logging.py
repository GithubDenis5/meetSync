"""JSON logging to stdout with support for Grafana Loki."""

from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(service_name: str, level: str = "INFO") -> None:
    """Configure JSON logging to stdout."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.addHandler(handler)

    # Set service name in extra
    logger = logging.getLogger(service_name)
    logger = logging.LoggerAdapter(logger, {"service": service_name})
