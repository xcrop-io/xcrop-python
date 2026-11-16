"""XCROP — Official Python SDK for the XCROP API (X/Twitter data intelligence platform).

Usage::

    from xcrop import XCropClient

    client = XCropClient(api_key="xc_live_...")
    user = client.users.get("elonmusk")
    print(user["data"]["username"])

Async::

    from xcrop import AsyncXCropClient

    async with AsyncXCropClient(api_key="xc_live_...") as client:
        user = await client.users.get("elonmusk")
"""

from .client import AsyncXCropClient, XCropClient
from .errors import (
    AuthError,
    ErrorCode,
    NotFoundError,
    RateLimitError,
    ServerError,
    StreamError,
    UserSuspendedError,
    UserUnavailableError,
    XCropError,
)

from ._version import __version__

__all__ = [
    "XCropClient",
    "AsyncXCropClient",
    "XCropError",
    "AuthError",
    "RateLimitError",
    "NotFoundError",
    "ServerError",
    "StreamError",
    "UserSuspendedError",
    "UserUnavailableError",
    "ErrorCode",
    "__version__",
]
