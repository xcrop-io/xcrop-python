"""KOL (Key Opinion Leader) resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse


class KolResource:
    """Sync KOL resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def timeline(
        self,
        usernames: List[str],
        *,
        count: int = 20,
    ) -> ApiResponse:
        """Get aggregated timeline for multiple KOL accounts.

        Args:
            usernames: List of X usernames to aggregate. Must not be empty.
            count: Number of tweets to return.

        Raises:
            ValueError: If usernames list is empty.
        """
        if not usernames:
            raise ValueError("usernames list must not be empty.")
        return self._transport.get(
            "/kol/timeline",
            usernames=",".join(usernames),
            count=count,
        )


class AsyncKolResource:
    """Async KOL resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def timeline(
        self,
        usernames: List[str],
        *,
        count: int = 20,
    ) -> ApiResponse:
        """Get aggregated timeline for multiple KOL accounts.

        Raises:
            ValueError: If usernames list is empty.
        """
        if not usernames:
            raise ValueError("usernames list must not be empty.")
        return await self._transport.get(
            "/kol/timeline",
            usernames=",".join(usernames),
            count=count,
        )
