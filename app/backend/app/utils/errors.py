"""Domain exceptions used across backend services and API layers."""


class AppError(Exception):
    """Base class for application-level errors."""


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""


class BadRequestError(AppError):
    """Raised when user input is invalid for business logic."""
