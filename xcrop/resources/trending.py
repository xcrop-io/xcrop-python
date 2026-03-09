"""Trending resource."""

from __future__ import annotations

from typing import Any, Dict

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse


class TrendingResource:
    """Sync trending resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def get(self) -> ApiResponse:
        """Get current trending topics."""
        return self._transport.get("/trending")


class AsyncTrendingResource:
    """Async trending resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def get(self) -> ApiResponse:
        return await self._transport.get("/trending")
