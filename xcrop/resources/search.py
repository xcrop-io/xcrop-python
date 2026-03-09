"""Search resource — tweets and users search with optional SSE streaming."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100


class SearchResource:
    """Sync search resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def tweets(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> ApiResponse:
        """Search tweets. Returns a single page of results."""
        body: Dict[str, Any] = {"query": query, "count": count}
        if sort is not None:
            body["sort"] = sort
        if cursor is not None:
            body["cursor"] = cursor
        if lang is not None:
            body["lang"] = lang
        if min_likes is not None:
            body["min_likes"] = min_likes
        if min_retweets is not None:
            body["min_retweets"] = min_retweets
        if exclude_replies is not None:
            body["exclude_replies"] = exclude_replies
        if exclude_retweets is not None:
            body["exclude_retweets"] = exclude_retweets
        if since is not None:
            body["since"] = since
        if until is not None:
            body["until"] = until
        return self._transport.post("/search", body=body)

    def tweets_paginate(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        max_pages: int = _MAX_PAGES,
    ) -> Iterator[Dict[str, Any]]:
        """Auto-paginate through all search results, yielding individual tweets.

        Args:
            max_pages: Safety limit on pages fetched (default 100).
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self.tweets(
                query,
                count=page_size,
                sort=sort,
                cursor=cursor,
                lang=lang,
                min_likes=min_likes,
                min_retweets=min_retweets,
                exclude_replies=exclude_replies,
                exclude_retweets=exclude_retweets,
                since=since,
                until=until,
            )
            pages_fetched += 1
            data = resp.get("data")
            if data is None:
                return
            if isinstance(data, list):
                for item in data:
                    yield item
                    remaining -= 1
                    if remaining <= 0:
                        return
            else:
                yield data
                return
            meta = resp.get("meta", {})
            if not meta.get("has_next"):
                return
            cursor = meta.get("cursor")
            if not cursor:
                return

    def tweets_stream(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream search results via SSE. Yields individual tweet objects."""
        body: Dict[str, Any] = {"query": query, "count": count, "stream": True}
        if sort is not None:
            body["sort"] = sort
        if lang is not None:
            body["lang"] = lang
        if min_likes is not None:
            body["min_likes"] = min_likes
        if min_retweets is not None:
            body["min_retweets"] = min_retweets
        if exclude_replies is not None:
            body["exclude_replies"] = exclude_replies
        if exclude_retweets is not None:
            body["exclude_retweets"] = exclude_retweets
        if since is not None:
            body["since"] = since
        if until is not None:
            body["until"] = until
        return self._transport.stream_sse("POST", "/search", json_body=body)

    def users(self, query: str, *, count: int = 20) -> ApiResponse:
        """Search users."""
        return self._transport.post("/search/users", body={"query": query, "count": count})


class AsyncSearchResource:
    """Async search resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def tweets(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> ApiResponse:
        body: Dict[str, Any] = {"query": query, "count": count}
        if sort is not None:
            body["sort"] = sort
        if cursor is not None:
            body["cursor"] = cursor
        if lang is not None:
            body["lang"] = lang
        if min_likes is not None:
            body["min_likes"] = min_likes
        if min_retweets is not None:
            body["min_retweets"] = min_retweets
        if exclude_replies is not None:
            body["exclude_replies"] = exclude_replies
        if exclude_retweets is not None:
            body["exclude_retweets"] = exclude_retweets
        if since is not None:
            body["since"] = since
        if until is not None:
            body["until"] = until
        return await self._transport.post("/search", body=body)

    async def tweets_paginate(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        max_pages: int = _MAX_PAGES,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Auto-paginate through all search results."""
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self.tweets(
                query,
                count=page_size,
                sort=sort,
                cursor=cursor,
                lang=lang,
                min_likes=min_likes,
                min_retweets=min_retweets,
                exclude_replies=exclude_replies,
                exclude_retweets=exclude_retweets,
                since=since,
                until=until,
            )
            pages_fetched += 1
            data = resp.get("data")
            if data is None:
                return
            if isinstance(data, list):
                for item in data:
                    yield item
                    remaining -= 1
                    if remaining <= 0:
                        return
            else:
                yield data
                return
            meta = resp.get("meta", {})
            if not meta.get("has_next"):
                return
            cursor = meta.get("cursor")
            if not cursor:
                return

    async def tweets_stream(
        self,
        query: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        lang: Optional[str] = None,
        min_likes: Optional[int] = None,
        min_retweets: Optional[int] = None,
        exclude_replies: Optional[bool] = None,
        exclude_retweets: Optional[bool] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        body: Dict[str, Any] = {"query": query, "count": count, "stream": True}
        if sort is not None:
            body["sort"] = sort
        if lang is not None:
            body["lang"] = lang
        if min_likes is not None:
            body["min_likes"] = min_likes
        if min_retweets is not None:
            body["min_retweets"] = min_retweets
        if exclude_replies is not None:
            body["exclude_replies"] = exclude_replies
        if exclude_retweets is not None:
            body["exclude_retweets"] = exclude_retweets
        if since is not None:
            body["since"] = since
        if until is not None:
            body["until"] = until
        async for item in self._transport.stream_sse("POST", "/search", json_body=body):
            yield item

    async def users(self, query: str, *, count: int = 20) -> ApiResponse:
        return await self._transport.post("/search/users", body={"query": query, "count": count})
