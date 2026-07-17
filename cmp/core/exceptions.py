"""Custom exception hierarchy for business logic errors."""


class ServiceError(Exception):
    """Base exception for service-layer errors."""
    def __init__(self, message: str, details: list | None = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class ValidationError(ServiceError):
    """Raised when input validation fails in a service."""


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""


class ConflictError(ServiceError):
    """Raised when an operation conflicts with current state."""


class ForbiddenError(ServiceError):
    """Raised when user lacks permission for an operation."""
