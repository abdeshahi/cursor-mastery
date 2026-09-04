"""Application-specific exceptions."""


class AppError(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(AppError):
    """Raised when application configuration is invalid."""


class DatabaseError(AppError):
    """Raised when a database operation fails."""
