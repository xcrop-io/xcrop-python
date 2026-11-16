"""Communities resource: community profile, tweets, members, moderators.

Members, moderators and tweets may return more rows than ``count`` (X serves
whole pages), so treat ``count`` as a minimum on those lists.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100


class _CommunityPaginatedEndpoint:
    def __init__(self, transport: HttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    def __call__(
        self,
        community_id: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        path = self._path_template.format(communityId=community_id)
        return self._transport.get(path, count=count, sort=sort, cursor=cursor)

    def paginate(
        self,
        community_id: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        max_pages: int = _MAX_PAGES,
    ) -> Iterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items.

        Args:
            community_id: The community ID.
            count: Total number of items to yield.
            sort: ``members`` and ``moderators`` only: "default" or "name".
                ``tweets`` has no sort option.
            max_pages: Safety limit on pages fetched (default 100).
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(community_id, count=page_size, sort=sort, cursor=cursor)
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


class _AsyncCommunityPaginatedEndpoint:
    def __init__(self, transport: AsyncHttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    async def __call__(
        self,
        community_id: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        path = self._path_template.format(communityId=community_id)
        return await self._transport.get(path, count=count, sort=sort, cursor=cursor)

    async def paginate(
        self,
        community_id: str,
        *,
        count: int = 20,
        sort: Optional[str] = None,
        max_pages: int = _MAX_PAGES,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items."""
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self(community_id, count=page_size, sort=sort, cursor=cursor)
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


class CommunitiesResource:
    """Sync communities resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.tweets = _CommunityPaginatedEndpoint(transport, "/communities/{communityId}/tweets")
        self.members = _CommunityPaginatedEndpoint(transport, "/communities/{communityId}/members")
        self.moderators = _CommunityPaginatedEndpoint(
            transport, "/communities/{communityId}/moderators",
        )

    def get(self, community_id: str) -> ApiResponse:
        """Get community details by ID."""
        return self._transport.get(f"/communities/{community_id}")


class AsyncCommunitiesResource:
    """Async communities resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.tweets = _AsyncCommunityPaginatedEndpoint(
            transport, "/communities/{communityId}/tweets",
        )
        self.members = _AsyncCommunityPaginatedEndpoint(
            transport, "/communities/{communityId}/members",
        )
        self.moderators = _AsyncCommunityPaginatedEndpoint(
            transport, "/communities/{communityId}/moderators",
        )

    async def get(self, community_id: str) -> ApiResponse:
        """Get community details by ID."""
        return await self._transport.get(f"/communities/{community_id}")
