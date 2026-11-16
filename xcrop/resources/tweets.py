"""Tweets resource — get, conversation, quotes, write operations, interaction checks."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, FrozenSet, Iterator, List, Optional, Union

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse
from ._params import TimeValue, encode_query

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100

_NO_OPTIONS: FrozenSet[str] = frozenset()
_CONVERSATION: FrozenSet[str] = frozenset({"sort", "since", "until"})
_QUOTES: FrozenSet[str] = frozenset({"since", "until", "include_replies"})


def _create_body(
    text: str,
    media_ids: Optional[List[str]],
    community_id: Optional[Union[str, int]],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"text": text}
    if media_ids is not None:
        body["media_ids"] = media_ids
    if community_id is not None:
        # Always a string: ids above 2^53 would lose precision as a JSON number.
        body["community_id"] = str(community_id)
    return body


# ---------------------------------------------------------------------------
# Paginated tweet sub-endpoints
# ---------------------------------------------------------------------------

class _TweetPaginatedEndpoint:
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
        tweet_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        sort: Optional[str] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            tweet_id: The tweet ID.
            count: Number of items to request per page.
            cursor: Pagination cursor from a previous response.
            sort: ``conversation`` only: "latest" (default), "relevance" or "likes".
                "popular" and "engagement" are aliases of "relevance".
            since: Only items at or after this time (unix seconds or ISO date).
                Supported on ``conversation`` and ``quotes``.
            until: Only items before this time (unix seconds or ISO date).
                Supported on ``conversation`` and ``quotes``.
            include_replies: ``quotes`` only: ``False`` leaves replies out (default true).
        """
        path = self._path_template.format(tweetId=tweet_id)
        query = encode_query(
            self._path_template, self._options,
            {"sort": sort, "since": since, "until": until,
             "include_replies": include_replies},
        )
        return self._transport.get(path, count=count, cursor=cursor, **query)

    def paginate(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        sort: Optional[str] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items.

        Args:
            tweet_id: The tweet ID.
            count: Total number of items to yield.
            max_pages: Safety limit on pages fetched (default 100).
            sort, since, until, include_replies: See ``__call__``.
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(
                tweet_id, count=page_size, cursor=cursor, sort=sort, since=since, until=until,
                include_replies=include_replies,
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


class _AsyncTweetPaginatedEndpoint:
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
        tweet_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
        sort: Optional[str] = None,
        since: Optional[TimeValue] = None,
        until: Optional[TimeValue] = None,
        include_replies: Optional[bool] = None,
    ) -> ApiResponse:
        """Fetch a single page.

        Args:
            tweet_id: The tweet ID.
            count: Number of items to request per page.
            cursor: Pagination cursor from a previous response.
            sort: ``conversation`` only: "latest" (default), "relevance" or "likes".
                "popular" and "engagement" are aliases of "relevance".
            since: Only items at or after this time (unix seconds or ISO date).
                Supported on ``conversation`` and ``quotes``.
            until: Only items before this time (unix seconds or ISO date).
                Supported on ``conversation`` and ``quotes``.
            include_replies: ``quotes`` only: ``False`` leaves replies out (default true).
        """
        path = self._path_template.format(tweetId=tweet_id)
        query = encode_query(
            self._path_template, self._options,
            {"sort": sort, "since": since, "until": until,
             "include_replies": include_replies},
        )
        return await self._transport.get(path, count=count, cursor=cursor, **query)

    async def paginate(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
        sort: Optional[str] = None,
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
            resp = await self(
                tweet_id, count=page_size, cursor=cursor, sort=sort, since=since, until=until,
                include_replies=include_replies,
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


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class TweetsResource:
    """Sync tweets resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport
        self.conversation = _TweetPaginatedEndpoint(
            transport, "/tweets/{tweetId}/conversation", _CONVERSATION,
        )
        self.quotes = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/quotes", _QUOTES)
        self.retweeters = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/retweeters")

    def get(self, tweet_id: str) -> ApiResponse:
        """Get a single tweet by ID."""
        return self._transport.get(f"/tweets/{tweet_id}")

    def batch(self, tweet_ids: List[str]) -> ApiResponse:
        """Batch lookup up to 100 tweets."""
        return self._transport.post("/tweets/batch", body={"tweet_ids": tweet_ids})

    # -- write operations --

    def create(
        self,
        text: str,
        *,
        media_ids: Optional[List[str]] = None,
        community_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Create a tweet (requires connected account).

        Args:
            media_ids: Media ids from ``media.upload()``.
            community_id: Post into a community the account has joined. Sent as a
                string of digits (ids exceed 2^53, a JSON number is rejected with
                ``BAD_COMMUNITY_ID``). Community posts are limited to 280 characters.
        """
        return self._transport.post("/tweets/create", body=_create_body(text, media_ids, community_id))

    def reply(self, tweet_id: str, text: str) -> Dict[str, Any]:
        """Reply to a tweet (requires connected account)."""
        return self._transport.post("/tweets/reply", body={"tweet_id": tweet_id, "text": text})

    def quote(self, tweet_id: str, text: str) -> Dict[str, Any]:
        """Quote a tweet (requires connected account)."""
        return self._transport.post("/tweets/quote", body={"tweet_id": tweet_id, "text": text})

    def delete(self, tweet_id: str) -> Dict[str, Any]:
        """Delete a tweet (requires connected account)."""
        return self._transport.delete(f"/tweets/{tweet_id}")

    def like(self, tweet_id: str) -> Dict[str, Any]:
        """Like a tweet (requires connected account)."""
        return self._transport.post(f"/tweets/{tweet_id}/like")

    def unlike(self, tweet_id: str) -> Dict[str, Any]:
        """Unlike a tweet (requires connected account)."""
        return self._transport.delete(f"/tweets/{tweet_id}/like")

    def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """Retweet a tweet (requires connected account)."""
        return self._transport.post(f"/tweets/{tweet_id}/retweet")

    def unretweet(self, tweet_id: str) -> Dict[str, Any]:
        """Remove a retweet (requires connected account)."""
        return self._transport.delete(f"/tweets/{tweet_id}/retweet")

    def bookmark(self, tweet_id: str) -> Dict[str, Any]:
        """Bookmark a tweet (requires connected account). ``data.already`` is true if it was already bookmarked."""
        return self._transport.post(f"/tweets/{tweet_id}/bookmark")

    def unbookmark(self, tweet_id: str) -> Dict[str, Any]:
        """Remove a bookmark (requires connected account)."""
        return self._transport.delete(f"/tweets/{tweet_id}/bookmark")

    def pin(self, tweet_id: str) -> Dict[str, Any]:
        """Pin one of your own tweets to your profile (another account's post gives 400 ``X_REFUSED``)."""
        return self._transport.post(f"/tweets/{tweet_id}/pin")

    def unpin(self, tweet_id: str) -> Dict[str, Any]:
        """Unpin a tweet from your profile (requires connected account)."""
        return self._transport.delete(f"/tweets/{tweet_id}/pin")

    # -- interaction checks --

    def check_retweet(self, tweet_id: str, username: str) -> Dict[str, Any]:
        """Check if a user retweeted a tweet."""
        return self._transport.get(f"/tweets/{tweet_id}/check-retweet", username=username)

    def check_reply(
        self,
        tweet_id: str,
        username: str,
        *,
        min_tags: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Check if a user replied to a tweet.

        Args:
            min_tags: Optional minimum number of @mentions (0-20) required in the reply.
        """
        return self._transport.get(
            f"/tweets/{tweet_id}/check-reply", username=username, min_tags=min_tags,
        )

    def check_quote(
        self,
        tweet_id: str,
        username: str,
        *,
        min_tags: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Check if a user quoted a tweet.

        Args:
            min_tags: Optional minimum number of @mentions (0-20) required in the quote.
        """
        return self._transport.get(
            f"/tweets/{tweet_id}/check-quote", username=username, min_tags=min_tags,
        )


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncTweetsResource:
    """Async tweets resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.conversation = _AsyncTweetPaginatedEndpoint(
            transport, "/tweets/{tweetId}/conversation", _CONVERSATION,
        )
        self.quotes = _AsyncTweetPaginatedEndpoint(
            transport, "/tweets/{tweetId}/quotes", _QUOTES,
        )
        self.retweeters = _AsyncTweetPaginatedEndpoint(
            transport, "/tweets/{tweetId}/retweeters",
        )

    async def get(self, tweet_id: str) -> ApiResponse:
        return await self._transport.get(f"/tweets/{tweet_id}")

    async def batch(self, tweet_ids: List[str]) -> ApiResponse:
        return await self._transport.post("/tweets/batch", body={"tweet_ids": tweet_ids})

    async def create(
        self,
        text: str,
        *,
        media_ids: Optional[List[str]] = None,
        community_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Create a tweet. See :meth:`TweetsResource.create`."""
        return await self._transport.post("/tweets/create", body=_create_body(text, media_ids, community_id))

    async def reply(self, tweet_id: str, text: str) -> Dict[str, Any]:
        return await self._transport.post("/tweets/reply", body={"tweet_id": tweet_id, "text": text})

    async def quote(self, tweet_id: str, text: str) -> Dict[str, Any]:
        return await self._transport.post("/tweets/quote", body={"tweet_id": tweet_id, "text": text})

    async def delete(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/tweets/{tweet_id}")

    async def like(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.post(f"/tweets/{tweet_id}/like")

    async def unlike(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/tweets/{tweet_id}/like")

    async def retweet(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.post(f"/tweets/{tweet_id}/retweet")

    async def unretweet(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/tweets/{tweet_id}/retweet")

    async def bookmark(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.post(f"/tweets/{tweet_id}/bookmark")

    async def unbookmark(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/tweets/{tweet_id}/bookmark")

    async def pin(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.post(f"/tweets/{tweet_id}/pin")

    async def unpin(self, tweet_id: str) -> Dict[str, Any]:
        return await self._transport.delete(f"/tweets/{tweet_id}/pin")

    async def check_retweet(self, tweet_id: str, username: str) -> Dict[str, Any]:
        return await self._transport.get(f"/tweets/{tweet_id}/check-retweet", username=username)

    async def check_reply(
        self,
        tweet_id: str,
        username: str,
        *,
        min_tags: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Check if a user replied to a tweet.

        Args:
            min_tags: Optional minimum number of @mentions (0-20) required in the reply.
        """
        return await self._transport.get(
            f"/tweets/{tweet_id}/check-reply", username=username, min_tags=min_tags,
        )

    async def check_quote(
        self,
        tweet_id: str,
        username: str,
        *,
        min_tags: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Check if a user quoted a tweet.

        Args:
            min_tags: Optional minimum number of @mentions (0-20) required in the quote.
        """
        return await self._transport.get(
            f"/tweets/{tweet_id}/check-quote", username=username, min_tags=min_tags,
        )
