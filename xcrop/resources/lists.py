"""Lists resource — tweets, members, subscribers."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, FrozenSet, Iterator, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse
from ._params import TimeValue, encode_query

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100

_NO_OPTIONS: FrozenSet[str] = frozenset()
_TWEETS: FrozenSet[str] = frozenset({"since", "until", "include_replies"})


class _ListPaginatedEndpoint:
    def __init__(
        self,
        transport: HttpTransport,
        path_template: str,
        options: FrozenSet[str] = _NO_OPTIONS,
    ) -> None:
        self._transport = transport
        self._path_template = path_template
        self._options = options

    def __call__(
        self,
        list_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            since: ``tweets`` only: items at or after this time (unix seconds or ISO date).
            until: ``tweets`` only: items before this time (unix seconds or ISO date).
            include_replies: ``tweets`` only: ``False`` leaves replies out (default true).
        """
        path = self._path_template.format(listId=list_id)
        query = encode_query(
            self._path_template, self._options, {"since": since, "until": until,
             "include_replies": include_replies},
        )
        return self._transport.get(path, count=count, cursor=cursor, **query)

    def paginate(
        self,
        list_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items.

        Args:
            list_id: The list ID.
            count: Total number of items to yield.
            max_pages: Safety limit on pages fetched (default 100).
            since, until, include_replies: ``tweets`` only, see ``__call__``.
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(list_id, count=page_size, cursor=cursor, since=since, until=until,
                       include_replies=include_replies)
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


class _AsyncListPaginatedEndpoint:
    def __init__(
        self,
        transport: AsyncHttpTransport,
        path_template: str,
        options: FrozenSet[str] = _NO_OPTIONS,
    ) -> None:
        self._transport = transport
        self._path_template = path_template
        self._options = options

    async def __call__(
        self,
        list_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> ApiResponse:
        path = self._path_template.format(listId=list_id)
        query = encode_query(
            self._path_template, self._options, {"since": since, "until": until,
             "include_replies": include_replies},
        )
        return await self._transport.get(path, count=count, cursor=cursor, **query)

    async def paginate(
        self,
        list_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items."""
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self(list_id, count=page_size, cursor=cursor, since=since, until=until,
                       include_replies=include_replies)
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


class ListsResource:
    """Sync lists resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self.tweets = _ListPaginatedEndpoint(transport, "/lists/{listId}/tweets", _TWEETS)
        self.members = _ListPaginatedEndpoint(transport, "/lists/{listId}/members")
        self.subscribers = _ListPaginatedEndpoint(transport, "/lists/{listId}/subscribers")


class AsyncListsResource:
    """Async lists resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self.tweets = _AsyncListPaginatedEndpoint(
            transport, "/lists/{listId}/tweets", _TWEETS,
        )
        self.members = _AsyncListPaginatedEndpoint(transport, "/lists/{listId}/members")
        self.subscribers = _AsyncListPaginatedEndpoint(transport, "/lists/{listId}/subscribers")
