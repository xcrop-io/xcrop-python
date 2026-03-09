"""Tweets resource — get, conversation, quotes, likers, write operations, interaction checks."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import ApiResponse

# Default safety limit for pagination to prevent infinite loops.
_MAX_PAGES = 100


# ---------------------------------------------------------------------------
# Paginated tweet sub-endpoints
# ---------------------------------------------------------------------------

class _TweetPaginatedEndpoint:
    def __init__(self, transport: HttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    def __call__(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        path = self._path_template.format(tweetId=tweet_id)
        return self._transport.get(path, count=count, cursor=cursor)

    def paginate(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
    ) -> Iterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items.

        Args:
            tweet_id: The tweet ID.
            count: Total number of items to yield.
            max_pages: Safety limit on pages fetched (default 100).
        """
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = self(tweet_id, count=page_size, cursor=cursor)
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
    def __init__(self, transport: AsyncHttpTransport, path_template: str) -> None:
        self._transport = transport
        self._path_template = path_template

    async def __call__(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        path = self._path_template.format(tweetId=tweet_id)
        return await self._transport.get(path, count=count, cursor=cursor)

    async def paginate(
        self,
        tweet_id: str,
        *,
        count: int = 20,
        max_pages: int = _MAX_PAGES,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Auto-paginate, yielding individual items."""
        cursor: Optional[str] = None
        remaining = count
        pages_fetched = 0
        while pages_fetched < max_pages:
            page_size = min(remaining, 100) if remaining > 0 else 20
            resp = await self(tweet_id, count=page_size, cursor=cursor)
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
        self.conversation = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/conversation")
        self.quotes = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/quotes")
        self.likers = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/likers")
        self.retweeters = _TweetPaginatedEndpoint(transport, "/tweets/{tweetId}/retweeters")

    def get(self, tweet_id: str) -> ApiResponse:
        """Get a single tweet by ID."""
        return self._transport.get(f"/tweets/{tweet_id}")

    def batch(self, tweet_ids: List[str]) -> ApiResponse:
        """Batch lookup up to 100 tweets."""
        return self._transport.post("/tweets/batch", body={"tweet_ids": tweet_ids})

    # -- write operations --

    def create(self, text: str) -> Dict[str, Any]:
        """Create a tweet (requires connected account)."""
        return self._transport.post("/tweets/create", body={"text": text})

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

    # -- interaction checks --

    def check_retweet(self, tweet_id: str, username: str) -> Dict[str, Any]:
        """Check if a user retweeted a tweet."""
        return self._transport.get(f"/tweets/{tweet_id}/check-retweet", username=username)

    def check_reply(self, tweet_id: str, username: str) -> Dict[str, Any]:
        """Check if a user replied to a tweet."""
        return self._transport.get(f"/tweets/{tweet_id}/check-reply", username=username)

    def check_quote(self, tweet_id: str, username: str) -> Dict[str, Any]:
        """Check if a user quoted a tweet."""
        return self._transport.get(f"/tweets/{tweet_id}/check-quote", username=username)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class AsyncTweetsResource:
    """Async tweets resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport
        self.conversation = _AsyncTweetPaginatedEndpoint(transport, "/tweets/{tweetId}/conversation")
        self.quotes = _AsyncTweetPaginatedEndpoint(transport, "/tweets/{tweetId}/quotes")
        self.likers = _AsyncTweetPaginatedEndpoint(transport, "/tweets/{tweetId}/likers")
        self.retweeters = _AsyncTweetPaginatedEndpoint(transport, "/tweets/{tweetId}/retweeters")

    async def get(self, tweet_id: str) -> ApiResponse:
        return await self._transport.get(f"/tweets/{tweet_id}")

    async def batch(self, tweet_ids: List[str]) -> ApiResponse:
        return await self._transport.post("/tweets/batch", body={"tweet_ids": tweet_ids})

    async def create(self, text: str) -> Dict[str, Any]:
        return await self._transport.post("/tweets/create", body={"text": text})

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

    async def check_retweet(self, tweet_id: str, username: str) -> Dict[str, Any]:
        return await self._transport.get(f"/tweets/{tweet_id}/check-retweet", username=username)

    async def check_reply(self, tweet_id: str, username: str) -> Dict[str, Any]:
        return await self._transport.get(f"/tweets/{tweet_id}/check-reply", username=username)

    async def check_quote(self, tweet_id: str, username: str) -> Dict[str, Any]:
        return await self._transport.get(f"/tweets/{tweet_id}/check-quote", username=username)
