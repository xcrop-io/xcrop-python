"""Account resource — connect, status, disconnect."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import AccountStatus as AccountStatusType, ApiResponse


class AccountResource:
    """Sync account resource for managing X account connections."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def connect(
        self,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        totp_secret: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Connect an X account via credentials or cookies.

        Either provide (username, password, optional totp_secret) or cookies dict.

        Raises:
            ValueError: If neither credentials nor cookies are provided.
        """
        body: Dict[str, Any] = {}
        if cookies is not None:
            body["cookies"] = cookies
        elif username is not None and password is not None:
            body["username"] = username
            body["password"] = password
            if totp_secret is not None:
                body["totp_secret"] = totp_secret
        else:
            raise ValueError(
                "Either provide cookies dict or (username, password) credentials."
            )
        return self._transport.post("/account/connect", body=body)

    def status(self) -> Dict[str, Any]:
        """Check if an X account is connected."""
        return self._transport.get("/account/status")

    def disconnect(self) -> Dict[str, Any]:
        """Disconnect the X account and remove stored credentials."""
        return self._transport.delete("/account/disconnect")


class AsyncAccountResource:
    """Async account resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def connect(
        self,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        totp_secret: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Connect an X account via credentials or cookies.

        Raises:
            ValueError: If neither credentials nor cookies are provided.
        """
        body: Dict[str, Any] = {}
        if cookies is not None:
            body["cookies"] = cookies
        elif username is not None and password is not None:
            body["username"] = username
            body["password"] = password
            if totp_secret is not None:
                body["totp_secret"] = totp_secret
        else:
            raise ValueError(
                "Either provide cookies dict or (username, password) credentials."
            )
        return await self._transport.post("/account/connect", body=body)

    async def status(self) -> Dict[str, Any]:
        return await self._transport.get("/account/status")

    async def disconnect(self) -> Dict[str, Any]:
        return await self._transport.delete("/account/disconnect")
