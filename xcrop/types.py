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
    # Conversation endpoint only
    sort: str  # "latest" | "relevance" | "likes"
    thread_context: List["Tweet"]  # tweets above a mid-thread tweet, oldest first


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


class UserAffiliation(TypedDict, total=False):
    """Organisation badge shown next to a profile."""

    label: Optional[str]
    username: Optional[str]
    badge_url: Optional[str]


class User(TypedDict, total=False):
    """A user object. Fields added in 1.1.0 are all nullable (None = X did not send it)."""

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
    protected: Optional[bool]
    # Added in 1.1.0 (all nullable)
    banner_image: Optional[str]
    likes_count: Optional[int]
    media_count: Optional[int]
    can_dm: Optional[bool]
    pinned_tweet_ids: Optional[List[str]]
    automated: Optional[bool]  # X "Automated by @owner" bot label
    automated_by: Optional[str]
    affiliation: Optional[UserAffiliation]
    verified_type: Optional[str]  # "Business" | "Government" | None
    community_role: str  # "Admin" | "Moderator" | "Member"; community lists only
    # Only on rows returned with include_unavailable=True (every other field is None)
    unavailable: bool
    unavailable_reason: Optional[str]


class Relationship(TypedDict, total=False):
    """Result of ``users.check_follow(source, target)``."""

    source: str
    target: str
    source_follows_target: bool
    target_follows_source: bool


class QualifiedAccountCheck(TypedDict, total=False):
    """Result of ``users.check_qualified_account()``."""

    username: str
    qualified: bool
    followers_count: int
    account_age_days: int


class QualifiedNameCheck(TypedDict, total=False):
    """Result of ``users.check_qualified_name()``."""

    username: str
    qualified: bool
    name: str
    contains: str
    position: str


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


class TweetMetrics(TypedDict, total=False):
    likes: int
    retweets: int
    replies: int
    quotes: int  # added in 1.1.0
    views: int
    bookmarks: int


class TweetAuthor(TypedDict, total=False):
    id: str
    username: str
    name: str
    # Added in 1.1.0 (nullable)
    followers: Optional[int]
    verified: Optional[bool]
    verified_type: Optional[str]
    profile_image: Optional[str]


class TweetInReplyTo(TypedDict, total=False):
    tweet_id: Optional[str]
    user_id: Optional[str]
    username: Optional[str]


class TweetEdit(TypedDict, total=False):
    is_edited: bool
    edit_tweet_ids: Optional[List[str]]
    editable_until: Optional[str]  # ISO 8601


class TweetPlace(TypedDict, total=False):
    full_name: Optional[str]
    country: Optional[str]
    country_code: Optional[str]


class TweetCard(TypedDict, total=False):
    name: Optional[str]
    url: Optional[str]
    title: Optional[str]
    poll: Optional[Any]


class TweetEntities(TypedDict, total=False):
    urls: List[Dict[str, Optional[str]]]  # url, expanded_url, display_url
    mentions: List[Dict[str, Optional[str]]]  # id, username, name
    hashtags: List[Any]
    symbols: List[Any]


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
    author: Union[User, TweetAuthor]
    created_at: str
    public_metrics: TweetPublicMetrics
    media: List[TweetMedia]
    lang: str
    source: str
    conversation_id: str
    in_reply_to_user_id: Optional[str]
    referenced_tweets: List[Dict[str, str]]
    entities: Optional[TweetEntities]
    quoted_tweet: Optional["Tweet"]
    # Added in 1.1.0 (nullable). ``text`` is the full text of a long post.
    url: Optional[str]
    metrics: TweetMetrics
    is_reply: bool
    in_reply_to: Optional[TweetInReplyTo]
    is_quote: bool
    quoted_tweet_id: Optional[str]
    is_retweet: bool
    retweeted_tweet_id: Optional[str]
    retweeted_tweet: Optional["Tweet"]  # nested one level
    is_long_post: bool
    possibly_sensitive: Optional[bool]
    edit: Optional[TweetEdit]
    has_community_notes: Optional[bool]
    place: Optional[TweetPlace]
    card: Optional[TweetCard]


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
    rank: int  # 1-based, added in 1.1.0
    volume: None  # always None: X no longer publishes counts
    tweet_count: int
    domain: str
    context: str


# ---------------------------------------------------------------------------
# Communities
# ---------------------------------------------------------------------------

class CommunityTopic(TypedDict, total=False):
    id: Optional[str]
    name: Optional[str]


class CommunityRule(TypedDict, total=False):
    name: str
    description: str


class Community(TypedDict, total=False):
    id: str
    name: str
    description: str
    member_count: Optional[int]
    is_nsfw: Optional[bool]
    created_at: Optional[str]
    # Added in 1.1.0
    moderator_count: Optional[int]
    join_policy: Optional[str]
    invites_policy: Optional[str]
    question: Optional[str]
    topic: Optional[CommunityTopic]
    search_tags: List[str]
    banner_image: Optional[str]
    rules: List[CommunityRule]
    creator: Optional[User]
    admin: Optional[User]
    members_preview: List[Any]
    url: Optional[str]


class CommunityMember(TypedDict, total=False):
    user: User
    role: str


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


class AccountCredits(TypedDict, total=False):
    """Result of ``account.credits()`` (``data`` of the response)."""

    plan: str
    plan_credits: int
    plan_used: int
    plan_remaining: int
    topup_remaining: int
    total_remaining: int
    period_start: str  # ISO 8601
    period_end: str  # ISO 8601
    rate_limit_per_minute: int


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
