"""XCROP API exception classes."""

from typing import Optional


class XCropError(Exception):
    """Base exception for all XCROP API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response = response
        super().__init__(message)

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
    ) -> None:
        super().__init__(
            message, status_code=status_code, error_code=error_code, response=response,
        )


class RateLimitError(XCropError):
    """Raised on 429 Too Many Requests (after all retries exhausted)."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
    ) -> None:
        super().__init__(
            message, status_code=429, error_code=error_code, response=response,
        )
        self.retry_after = retry_after


class NotFoundError(XCropError):
    """Raised on 404 Not Found responses."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
    ) -> None:
        super().__init__(
            message, status_code=404, error_code=error_code, response=response,
        )


class ServerError(XCropError):
    """Raised on 5xx responses (after all retries exhausted)."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        response: Optional[object] = None,
    ) -> None:
        super().__init__(
            message, status_code=status_code, error_code=error_code, response=response,
        )


class StreamError(XCropError):
    """Raised when an SSE stream encounters an error."""
    pass
