"""Users resource — profile, timeline, followers, etc."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse, User, Relationship as RelationshipType

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100


# ---------------------------------------------------------------------------
# Paginated sub-resource (callable + .paginate)
# ---------------------------------------------------------------------------

class _PaginatedEndpoint:
    """A callable that also exposes ``.paginate()`` for auto-pagination."""

    def __init__(self, transport: HttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    def __call__(
        self,
        username: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            username: The X username.
            count: Number of items to request *per page* from the API (max 100).
            cursor: Pagination cursor from a previous response.
        """
        path = self._path_template.format(username=username)
        return self._transport.get(path, count=count, cursor=cursor)

    def paginate(
        self,
        username: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over all items across pages, yielding individual data items.

        Args:
            username: The X username.
            count: *Total* number of items to yield across all pages.
            max_pages: Safety limit on pages fetched to prevent infinite loops (default 100).
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(username, count=page_size, cursor=cursor)
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


class _AsyncPaginatedEndpoint:
    """Async version of _PaginatedEndpoint."""

    def __init__(self, transport: AsyncHttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    async def __call__(
        self,
        username: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            username: The X username.
            count: Number of items to request *per page* from the API (max 100).
            cursor: Pagination cursor from a previous response.
        """
        path = self._path_template.format(username=username)
        return await self._transport.get(path, count=count, cursor=cursor)

    async def paginate(
        self,
        username: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Iterate over all items across pages, yielding individual data items.

        Args:
            username: The X username.
            count: *Total* number of items to yield across all pages.
            max_pages: Safety limit on pages fetched to prevent infinite loops (default 100).
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self(username, count=page_size, cursor=cursor)
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


# ---------------------------------------------------------------------------
# Sync resource
# ---------------------------------------------------------------------------

class UsersResource:
    """Sync users resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.tweets = _PaginatedEndpoint(transport, "/users/{username}/tweets")
        self.mentions = _PaginatedEndpoint(transport, "/users/{username}/mentions")
        self.followers = _PaginatedEndpoint(transport, "/users/{username}/followers")
        self.following = _PaginatedEndpoint(transport, "/users/{username}/following")
        self.replies = _PaginatedEndpoint(transport, "/users/{username}/replies")
        self.media = _PaginatedEndpoint(transport, "/users/{username}/media")
        self.verified_followers = _PaginatedEndpoint(
            transport, "/users/{username}/verified-followers",
        )

    def get(self, username: str) -> ApiResponse:
        """Get a user profile by username."""
        return self._transport.get(f"/users/{username}")

    def batch(self, usernames: List[str]) -> ApiResponse:
        """Batch lookup up to 100 users."""
        return self._transport.post("/users/batch", body={"usernames": usernames})

    def relationship(self, source: str, target: str) -> ApiResponse:
        """Check follow relationship between two users."""
        return self._transport.get("/users/relationship", source=source, target=target)

    def follow(self, username: str) -> Dict[str, Any]:
        """Follow a user (requires connected account)."""
        return self._transport.post(f"/users/{username}/follow")

    def unfollow(self, username: str) -> Dict[str, Any]:
        """Unfollow a user (requires connected account)."""
        return self._transport.delete(f"/users/{username}/follow")


# ---------------------------------------------------------------------------
# Async resource
# ---------------------------------------------------------------------------

class AsyncUsersResource:
    """Async users resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.tweets = _AsyncPaginatedEndpoint(transport, "/users/{username}/tweets")
        self.mentions = _AsyncPaginatedEndpoint(transport, "/users/{username}/mentions")
        self.followers = _AsyncPaginatedEndpoint(transport, "/users/{username}/followers")
        self.following = _AsyncPaginatedEndpoint(transport, "/users/{username}/following")
        self.replies = _AsyncPaginatedEndpoint(transport, "/users/{username}/replies")
        self.media = _AsyncPaginatedEndpoint(transport, "/users/{username}/media")
        self.verified_followers = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/verified-followers",
        )

    async def get(self, username: str) -> ApiResponse:
        return await self._transport.get(f"/users/{username}")

    async def batch(self, usernames: List[str]) -> ApiResponse:
        return await self._transport.post("/users/batch", body={"usernames": usernames})

    async def relationship(self, source: str, target: str) -> ApiResponse:
        return await self._transport.get("/users/relationship", source=source, target=target)

    async def follow(self, username: str) -> Dict[str, Any]:
        return await self._transport.post(f"/users/{username}/follow")

    async def unfollow(self, username: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/users/{username}/follow")
