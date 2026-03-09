"""Type definitions for the XCROP SDK."""

from typing import Any, Dict, List, Optional, Union

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Meta / envelope
# ---------------------------------------------------------------------------

class Meta(TypedDict, total=False):
    latency_ms: int
    cached: bool
    total: int
    cursor: Optional[str]
    has_next: bool


class ApiResponse(TypedDict, total=False):
    data: Any
    meta: Meta


class ErrorResponse(TypedDict):
    error: str
    code: str


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserPublicMetrics(TypedDict, total=False):
    followers_count: int
    following_count: int
    tweet_count: int
    listed_count: int
    like_count: int
    media_count: int


class User(TypedDict, total=False):
    id: str
    username: str
    name: str
    description: str
    profile_image_url: str
    profile_banner_url: str
    verified: bool
    is_blue_verified: bool
    created_at: str
    location: str
    url: str
    public_metrics: UserPublicMetrics
    pinned_tweet_id: Optional[str]
    protected: bool


class Relationship(TypedDict, total=False):
    source: str
    target: str
    following: bool
    followed_by: bool
    blocking: bool
    muting: bool


# ---------------------------------------------------------------------------
# Tweets
# ---------------------------------------------------------------------------

class TweetPublicMetrics(TypedDict, total=False):
    retweet_count: int
    reply_count: int
    like_count: int
    quote_count: int
    bookmark_count: int
    impression_count: int


class TweetMedia(TypedDict, total=False):
    type: str
    url: str
    preview_image_url: str
    width: int
    height: int
    duration_ms: int
    alt_text: str


class Tweet(TypedDict, total=False):
    id: str
    text: str
    author: User
    created_at: str
    public_metrics: TweetPublicMetrics
    media: List[TweetMedia]
    lang: str
    source: str
    conversation_id: str
    in_reply_to_user_id: Optional[str]
    referenced_tweets: List[Dict[str, str]]
    entities: Dict[str, Any]
    quoted_tweet: Optional["Tweet"]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchParams(TypedDict, total=False):
    query: str
    count: int
    sort: str  # "latest" | "popular" | "engagement"
    cursor: str
    lang: str
    min_likes: int
    min_retweets: int
    exclude_replies: bool
    exclude_retweets: bool
    since: str
    until: str
    stream: bool


class UserSearchParams(TypedDict, total=False):
    query: str
    count: int


# ---------------------------------------------------------------------------
# Trending
# ---------------------------------------------------------------------------

class TrendingTopic(TypedDict, total=False):
    name: str
    tweet_count: int
    domain: str
    context: str


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

class ConnectCredentials(TypedDict, total=False):
    username: str
    password: str
    totp_secret: str


class ConnectCookies(TypedDict, total=False):
    cookies: Dict[str, str]


class AccountStatus(TypedDict, total=False):
    connected: bool
    username: str
    connected_at: str


# ---------------------------------------------------------------------------
# Interaction Check
# ---------------------------------------------------------------------------

class InteractionCheck(TypedDict, total=False):
    checked: bool
    tweet_id: str
    username: str
    result: bool


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

PaginatedData = Dict[str, Any]
"""A single page response with ``data`` and ``meta`` keys."""
