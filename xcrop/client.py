"""XCROP API clients — sync and async."""

from __future__ import annotations

from typing import Optional

import httpx

from ._http import AsyncHttpTransport, HttpTransport, DEFAULT_BASE_URL, DEFAULT_TIMEOUT, MAX_RETRIES
from .resources import (
    AccountResource,
    AsyncAccountResource,
    AsyncKolResource,
    AsyncListsResource,
    AsyncSearchResource,
    AsyncStreamResource,
    AsyncTrendingResource,
    AsyncTweetsResource,
    AsyncUsersResource,
    KolResource,
    ListsResource,
    SearchResource,
    StreamResource,
    TrendingResource,
    TweetsResource,
    UsersResource,
)


class XCropClient:
    """Synchronous XCROP API client.

    Usage::

        client = XCropClient(api_key="xc_live_...")
        user = client.users.get("elonmusk")

        # Auto-paginate
        for tweet in client.users.tweets.paginate("elonmusk", count=200):
            print(tweet["text"])

        client.close()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._transport = HttpTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.users = UsersResource(self._transport)
        self.tweets = TweetsResource(self._transport)
        self.search = SearchResource(self._transport)
        self.lists = ListsResource(self._transport)
        self.trending = TrendingResource(self._transport)
        self.kol = KolResource(self._transport)
        self.account = AccountResource(self._transport)
        self.stream = StreamResource(self._transport)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._transport.close()

    def __enter__(self) -> "XCropClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncXCropClient:
    """Asynchronous XCROP API client.

    Usage::

        async with AsyncXCropClient(api_key="xc_live_...") as client:
            user = await client.users.get("elonmusk")
            async for tweet in client.users.tweets.paginate("elonmusk", count=200):
                print(tweet)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._transport = AsyncHttpTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.users = AsyncUsersResource(self._transport)
        self.tweets = AsyncTweetsResource(self._transport)
        self.search = AsyncSearchResource(self._transport)
        self.lists = AsyncListsResource(self._transport)
        self.trending = AsyncTrendingResource(self._transport)
        self.kol = AsyncKolResource(self._transport)
        self.account = AsyncAccountResource(self._transport)
        self.stream = AsyncStreamResource(self._transport)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._transport.close()

    async def __aenter__(self) -> "AsyncXCropClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
