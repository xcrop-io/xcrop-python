"""Users resource: profile, timeline, followers, etc."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, FrozenSet, Iterator, List, Optional, Union

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse, User
from ._params import TimeValue, encode_query, user_path

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100

_ID_ONLY: FrozenSet[str] = frozenset({"user_id"})
_WITH_WINDOW: FrozenSet[str] = frozenset({"user_id", "since", "until"})
_WITH_UNAVAILABLE: FrozenSet[str] = frozenset({"user_id", "include_unavailable"})


# ---------------------------------------------------------------------------
# Paginated sub-resource (callable + .paginate)
# ---------------------------------------------------------------------------

class _PaginatedEndpoint:
    """A callable that also exposes ``.paginate()`` for auto-pagination."""

    def __init__(
        self,
        transport: HttpTransport,
        path_template: str,
        options: FrozenSet[str] = _ID_ONLY,
    ) -> None:
        self._transport = transport
        self._path_template = path_template
        self._options = options

    def __call__(
        self,
        username: Optional[str] = None,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[Union[str, int]] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_unavailable: Optional[bool] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            username: The X username. Also accepts ``"id:<digits>"``.
            count: Number of items to request *per page* from the API (max 100).
            cursor: Pagination cursor from a previous response.
            user_id: Numeric X user id, used instead of ``username``.
            since: Only items at or after this time (unix seconds or ISO date).
                Supported on ``mentions``.
            until: Only items before this time (unix seconds or ISO date).
                Supported on ``mentions``.
            include_unavailable: Also return suspended/deactivated accounts as
                ``{"id", "unavailable": True, ...}`` rows (not billed).
                Supported on followers, following and verified_followers.
        """
        uid = None if user_id is None else str(user_id)
        path = user_path(self._path_template, username, uid)
        query = encode_query(
            self._path_template, self._options,
            {"user_id": uid, "since": since, "until": until,
             "include_unavailable": include_unavailable},
        )
        return self._transport.get(path, count=count, cursor=cursor, **query)

    def paginate(
        self,
        username: Optional[str] = None,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        user_id: Optional[Union[str, int]] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_unavailable: Optional[bool] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over all items across pages, yielding individual data items.

        Args:
            username: The X username (or pass ``user_id``).
            count: *Total* number of items to yield across all pages.
            max_pages: Safety limit on pages fetched to prevent infinite loops (default 100).
            user_id, since, until, include_unavailable: See ``__call__``.
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(
                username, count=page_size, cursor=cursor, user_id=user_id,
                since=since, until=until, include_unavailable=include_unavailable,
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


class _AsyncPaginatedEndpoint:
    """Async version of _PaginatedEndpoint."""

    def __init__(
        self,
        transport: AsyncHttpTransport,
        path_template: str,
        options: FrozenSet[str] = _ID_ONLY,
    ) -> None:
        self._transport = transport
        self._path_template = path_template
        self._options = options

    async def __call__(
        self,
        username: Optional[str] = None,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[Union[str, int]] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_unavailable: Optional[bool] = None,
    ) -> ApiResponse:
        """Fetch a single page. See :class:`_PaginatedEndpoint` for the arguments."""
        uid = None if user_id is None else str(user_id)
        path = user_path(self._path_template, username, uid)
        query = encode_query(
            self._path_template, self._options,
            {"user_id": uid, "since": since, "until": until,
             "include_unavailable": include_unavailable},
        )
        return await self._transport.get(path, count=count, cursor=cursor, **query)

    async def paginate(
        self,
        username: Optional[str] = None,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        user_id: Optional[Union[str, int]] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_unavailable: Optional[bool] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Iterate over all items across pages, yielding individual data items.

        Args:
            username: The X username (or pass ``user_id``).
            count: *Total* number of items to yield across all pages.
            max_pages: Safety limit on pages fetched to prevent infinite loops (default 100).
            user_id, since, until, include_unavailable: See ``__call__``.
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self(
                username, count=page_size, cursor=cursor, user_id=user_id,
                since=since, until=until, include_unavailable=include_unavailable,
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


def _batch_body(
    usernames: Optional[List[str]],
    ids: Optional[List[Union[str, int]]],
) -> Dict[str, Any]:
    if usernames is not None and ids is not None:
        raise ValueError("Send either usernames or ids, not both.")
    if ids is not None:
        # Strings, so ids above 2^53 never lose precision in JSON.
        return {"ids": [str(i) for i in ids]}
    if usernames is not None:
        return {"usernames": usernames}
    raise ValueError("Provide usernames or ids.")


def _user_action_path(action: str, username: Optional[str], user_id: Optional[Union[str, int]]) -> str:
    uid = None if user_id is None else str(user_id)
    return user_path("/users/{username}/" + action, username, uid)


# ---------------------------------------------------------------------------
# Sync resource
# ---------------------------------------------------------------------------

class UsersResource:
    """Sync users resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.tweets = _PaginatedEndpoint(transport, "/users/{username}/tweets")
        self.mentions = _PaginatedEndpoint(
            transport, "/users/{username}/mentions", _WITH_WINDOW,
        )
        self.followers = _PaginatedEndpoint(
            transport, "/users/{username}/followers", _WITH_UNAVAILABLE,
        )
        self.following = _PaginatedEndpoint(
            transport, "/users/{username}/following", _WITH_UNAVAILABLE,
        )
        self.replies = _PaginatedEndpoint(transport, "/users/{username}/replies")
        self.media = _PaginatedEndpoint(transport, "/users/{username}/media")
        self.verified_followers = _PaginatedEndpoint(
            transport, "/users/{username}/verified-followers", _WITH_UNAVAILABLE,
        )
        self.followers_ids = _PaginatedEndpoint(
            transport, "/users/{username}/followers-ids",
        )
        self.following_ids = _PaginatedEndpoint(
            transport, "/users/{username}/following-ids",
        )

    def get(
        self,
        username: Optional[str] = None,
        *,
        user_id: Optional[Union[str, int]] = None,
    ) -> ApiResponse:
        """Get a user profile by username, or by numeric id (``user_id=``)."""
        uid = None if user_id is None else str(user_id)
        path = user_path("/users/{username}", username, uid)
        return self._transport.get(path, **encode_query("/users", _ID_ONLY, {"user_id": uid}))

    def batch(
        self,
        usernames: Optional[List[str]] = None,
        *,
        ids: Optional[List[Union[str, int]]] = None,
    ) -> ApiResponse:
        """Batch lookup up to 100 users, by ``usernames`` or by numeric ``ids``.

        Send one or the other, not both. Ids are sent as strings.
        """
        return self._transport.post("/users/batch", body=_batch_body(usernames, ids))

    def check_follow(self, source: str, target: str) -> ApiResponse:
        """Check whether ``source`` follows ``target``."""
        return self._transport.get("/users/check-follow", source=source, target=target)

    def check_qualified_account(
        self,
        username: str,
        *,
        min_followers: int,
        min_age_days: int,
    ) -> ApiResponse:
        """Eligibility check: does the account meet a minimum follower count
        and minimum account age (in days)? For giveaway/airdrop gating.
        """
        return self._transport.get(
            f"/users/{username}/check-qualified-account",
            min_followers=min_followers,
            min_age_days=min_age_days,
        )

    def check_qualified_name(
        self,
        username: str,
        *,
        contains: str,
        position: str = "anywhere",
    ) -> ApiResponse:
        """Eligibility check: does the account display name contain
        ``contains``? ``position`` is one of "anywhere", "left", "right".
        For giveaway/airdrop gating.
        """
        return self._transport.get(
            f"/users/{username}/check-qualified-name",
            contains=contains,
            position=position,
        )

    def follow(self, username: str) -> Dict[str, Any]:
        """Follow a user (requires connected account)."""
        return self._transport.post(f"/users/{username}/follow")

    def unfollow(self, username: str) -> Dict[str, Any]:
        """Unfollow a user (requires connected account)."""
        return self._transport.delete(f"/users/{username}/follow")

    def mute(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Mute a user (requires connected account). ``username`` or ``"id:<digits>"`` or ``user_id=``.

        ``data`` is ``{user_id, username, muted: True, already}``.
        """
        return self._transport.post(_user_action_path("mute", username, user_id))

    def unmute(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Unmute a user (requires connected account)."""
        return self._transport.delete(_user_action_path("mute", username, user_id))

    def block(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Block a user (requires connected account). ``data`` is ``{user_id, username, blocked: True, already}``."""
        return self._transport.post(_user_action_path("block", username, user_id))

    def unblock(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Unblock a user (requires connected account)."""
        return self._transport.delete(_user_action_path("block", username, user_id))


# ---------------------------------------------------------------------------
# Async resource
# ---------------------------------------------------------------------------

class AsyncUsersResource:
    """Async users resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.tweets = _AsyncPaginatedEndpoint(transport, "/users/{username}/tweets")
        self.mentions = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/mentions", _WITH_WINDOW,
        )
        self.followers = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/followers", _WITH_UNAVAILABLE,
        )
        self.following = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/following", _WITH_UNAVAILABLE,
        )
        self.replies = _AsyncPaginatedEndpoint(transport, "/users/{username}/replies")
        self.media = _AsyncPaginatedEndpoint(transport, "/users/{username}/media")
        self.verified_followers = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/verified-followers", _WITH_UNAVAILABLE,
        )
        self.followers_ids = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/followers-ids",
        )
        self.following_ids = _AsyncPaginatedEndpoint(
            transport, "/users/{username}/following-ids",
        )

    async def get(
        self,
        username: Optional[str] = None,
        *,
        user_id: Optional[Union[str, int]] = None,
    ) -> ApiResponse:
        """Get a user profile by username, or by numeric id (``user_id=``)."""
        uid = None if user_id is None else str(user_id)
        path = user_path("/users/{username}", username, uid)
        return await self._transport.get(path, **encode_query("/users", _ID_ONLY, {"user_id": uid}))

    async def batch(
        self,
        usernames: Optional[List[str]] = None,
        *,
        ids: Optional[List[Union[str, int]]] = None,
    ) -> ApiResponse:
        """Batch lookup up to 100 users, by ``usernames`` or by numeric ``ids``."""
        return await self._transport.post("/users/batch", body=_batch_body(usernames, ids))

    async def check_follow(self, source: str, target: str) -> ApiResponse:
        """Check whether ``source`` follows ``target``."""
        return await self._transport.get("/users/check-follow", source=source, target=target)

    async def check_qualified_account(
        self,
        username: str,
        *,
        min_followers: int,
        min_age_days: int,
    ) -> ApiResponse:
        """Eligibility check: does the account meet a minimum follower count
        and minimum account age (in days)? For giveaway/airdrop gating.
        """
        return await self._transport.get(
            f"/users/{username}/check-qualified-account",
            min_followers=min_followers,
            min_age_days=min_age_days,
        )

    async def check_qualified_name(
        self,
        username: str,
        *,
        contains: str,
        position: str = "anywhere",
    ) -> ApiResponse:
        """Eligibility check: does the account display name contain
        ``contains``? ``position`` is one of "anywhere", "left", "right".
        For giveaway/airdrop gating.
        """
        return await self._transport.get(
            f"/users/{username}/check-qualified-name",
            contains=contains,
            position=position,
        )

    async def follow(self, username: str) -> Dict[str, Any]:
        return await self._transport.post(f"/users/{username}/follow")

    async def unfollow(self, username: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/users/{username}/follow")

    async def mute(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        return await self._transport.post(_user_action_path("mute", username, user_id))

    async def unmute(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        return await self._transport.delete(_user_action_path("mute", username, user_id))

    async def block(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        return await self._transport.post(_user_action_path("block", username, user_id))

    async def unblock(self, username: Optional[str] = None, *, user_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        return await self._transport.delete(_user_action_path("block", username, user_id))
