"""XCROP API exception classes."""

from typing import Optional


class ErrorCode:
    """Machine-readable ``code`` values the API puts in error bodies.

    Compare against ``XCropError.code`` (alias of ``error_code``).
    """

    NOT_FOUND = "NOT_FOUND"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_UNAVAILABLE = "USER_UNAVAILABLE"
    BAD_COMMUNITY_ID = "BAD_COMMUNITY_ID"
    BAD_TIME_WINDOW = "BAD_TIME_WINDOW"
    BAD_USER_ID = "BAD_USER_ID"
    BAD_SORT = "BAD_SORT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class XCropError(Exception):
    """Base exception for all XCROP API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
        reason: Optional[str] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response = response
        # Extra detail on some 404s (e.g. "suspended", "deactivated", "not_found").
        self.reason = reason
        super().__init__(message)

    @property
    def code(self) -> Optional[str]:
        """Alias of ``error_code``."""
        return self.error_code

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


class AuthError(XCropError):
    """Raised on 401 Unauthorized or 403 Forbidden responses."""

    def __init__(
        self,
        message: str,
        status_code: int = 401,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message, status_code=status_code, error_code=error_code,
            response=response, reason=reason,
        )


class RateLimitError(XCropError):
    """Raised on 429 Too Many Requests (after all retries exhausted)."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message, status_code=429, error_code=error_code,
            response=response, reason=reason,
        )
        self.retry_after = retry_after


class NotFoundError(XCropError):
    """Raised on 404 Not Found responses.

    ``code`` is ``NOT_FOUND`` for a missing user, tweet, list or community.
    Suspended and unavailable accounts raise the subclasses
    :class:`UserSuspendedError` and :class:`UserUnavailableError`, so existing
    ``except NotFoundError`` handlers keep working.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message, status_code=404, error_code=error_code,
            response=response, reason=reason,
        )


class UserSuspendedError(NotFoundError):
    """Raised on 404 ``USER_SUSPENDED``: the account is suspended. Retrying will not help."""


class UserUnavailableError(NotFoundError):
    """Raised on 404 ``USER_UNAVAILABLE``: the account is deactivated or restricted.

    ``reason`` says why (for example ``"deactivated"``).
    """


class ServerError(XCropError):
    """Raised on 5xx responses (after all retries exhausted)."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message, status_code=status_code, error_code=error_code,
            response=response, reason=reason,
        )


class StreamError(XCropError):
    """Raised when an SSE stream encounters an error."""
    pass
