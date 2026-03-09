"""SSE real-time stream resource."""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Iterator

from .._http import AsyncHttpTransport, HttpTransport


class StreamResource:
    """Sync SSE stream resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def connect(self) -> Iterator[Dict[str, Any]]:
        """Connect to the real-time SSE stream. Yields event dicts."""
        return self._transport.stream_sse("GET", "/stream")


class AsyncStreamResource:
    """Async SSE stream resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def connect(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Connect to the real-time SSE stream. Yields event dicts."""
        async for item in self._transport.stream_sse("GET", "/stream"):
            yield item
