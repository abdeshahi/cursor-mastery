"""Structured JSON logging configuration."""

import logging
import sys
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from app.core.config import Settings


class AppJsonFormatter(JsonFormatter):
    """JSON log formatter with standard application fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("service", "cttel-dollar-intelligence-bot")


def setup_logging(settings: Settings | None = None) -> None:
    """Configure root logger with structured JSON output."""
    from app.core.config import get_settings

    resolved_settings = settings or get_settings()
    log_level = getattr(logging, resolved_settings.log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        AppJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    )
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
