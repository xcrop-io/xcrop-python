"""XCROP API resource namespaces."""

from .users import UsersResource, AsyncUsersResource
from .tweets import TweetsResource, AsyncTweetsResource
from .search import SearchResource, AsyncSearchResource
from .lists import ListsResource, AsyncListsResource
from .communities import CommunitiesResource, AsyncCommunitiesResource
from .trending import TrendingResource, AsyncTrendingResource
from .account import AccountResource, AsyncAccountResource
from .stream import StreamResource, AsyncStreamResource

__all__ = [
    "UsersResource",
    "AsyncUsersResource",
    "TweetsResource",
    "AsyncTweetsResource",
    "SearchResource",
    "AsyncSearchResource",
    "ListsResource",
    "AsyncListsResource",
    "CommunitiesResource",
    "AsyncCommunitiesResource",
    "TrendingResource",
    "AsyncTrendingResource",
    "AccountResource",
    "AsyncAccountResource",
    "StreamResource",
    "AsyncStreamResource",
]
