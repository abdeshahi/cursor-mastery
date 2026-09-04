"""Tests for application startup and logging."""

import logging

from app.core.config import Settings
from app.core.logging import setup_logging
from app.main import create_app


def test_create_app_imports_successfully() -> None:
    application = create_app()
    assert application.title == "CTTEL Dollar Intelligence Bot"
    assert application.version == "0.1.0"


def test_setup_logging_configures_json_handler() -> None:
    setup_logging(Settings(log_level="DEBUG"))
    root_logger = logging.getLogger()
    assert root_logger.handlers
    assert root_logger.level == logging.DEBUG
