"""XCROP API resource namespaces."""

from .users import UsersResource, AsyncUsersResource
from .tweets import TweetsResource, AsyncTweetsResource
from .search import SearchResource, AsyncSearchResource
from .lists import ListsResource, AsyncListsResource
from .trending import TrendingResource, AsyncTrendingResource
from .kol import KolResource, AsyncKolResource
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
    "TrendingResource",
    "AsyncTrendingResource",
    "KolResource",
    "AsyncKolResource",
    "AccountResource",
    "AsyncAccountResource",
    "StreamResource",
    "AsyncStreamResource",
]
