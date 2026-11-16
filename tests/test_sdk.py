"""Basic tests for the XCROP Python SDK."""

import json
from unittest.mock import MagicMock, patch

import pytest

import xcrop
from xcrop import XCropClient, AsyncXCropClient, __version__
from xcrop.errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    XCropError,
)
from xcrop._http import _parse_sse_data, HttpTransport


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def test_version_exists():
    assert __version__ == "1.2.0"


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------

def test_xcrop_error():
    err = XCropError("fail", status_code=400, error_code="BAD")
    assert err.message == "fail"
    assert err.status_code == 400
    assert err.error_code == "BAD"
    assert "fail" in str(err)


def test_auth_error_defaults():
    err = AuthError("unauthorized")
    assert err.status_code == 401


def test_auth_error_custom_status():
    err = AuthError("forbidden", status_code=403)
    assert err.status_code == 403


def test_rate_limit_error():
    err = RateLimitError("slow down", retry_after=30.0)
    assert err.status_code == 429
    assert err.retry_after == 30.0


def test_not_found_error():
    err = NotFoundError("gone")
    assert err.status_code == 404


def test_server_error_default():
    err = ServerError("oops")
    assert err.status_code == 500


def test_server_error_custom():
    err = ServerError("oops", status_code=503)
    assert err.status_code == 503


# ---------------------------------------------------------------------------
# SSE parser
# ---------------------------------------------------------------------------

def test_parse_sse_single_data_line():
    result = _parse_sse_data('data: {"id": "123"}')
    assert result == '{"id": "123"}'


def test_parse_sse_multiple_data_lines():
    event = 'data: {"first": 1}\ndata: {"second": 2}'
    result = _parse_sse_data(event)
    assert result == '{"first": 1}\n{"second": 2}'


def test_parse_sse_done_signal():
    result = _parse_sse_data("data: [DONE]")
    assert result is None


def test_parse_sse_no_data():
    result = _parse_sse_data("event: ping")
    assert result is None


def test_parse_sse_data_no_space():
    result = _parse_sse_data("data:hello")
    assert result == "hello"


# ---------------------------------------------------------------------------
# Types import (should work without typing_extensions on 3.12+)
# ---------------------------------------------------------------------------

def test_types_importable():
    from xcrop.types import User, Tweet, ApiResponse, Meta
    # TypedDicts should be usable as types
    assert User is not None
    assert Tweet is not None


# ---------------------------------------------------------------------------
# Account validation
# ---------------------------------------------------------------------------

def test_account_connect_requires_credentials_or_cookies():
    transport = MagicMock()
    from xcrop.resources.account import AccountResource
    resource = AccountResource(transport)
    with pytest.raises(ValueError, match="credentials"):
        resource.connect()


def test_account_connect_with_cookies():
    transport = MagicMock()
    transport.post.return_value = {"success": True}
    from xcrop.resources.account import AccountResource
    resource = AccountResource(transport)
    result = resource.connect(cookies={"auth_token": "abc", "ct0": "def"})
    assert result == {"success": True}
    transport.post.assert_called_once()


def test_account_connect_with_credentials():
    transport = MagicMock()
    transport.post.return_value = {"success": True}
    from xcrop.resources.account import AccountResource
    resource = AccountResource(transport)
    result = resource.connect(username="user", password="pass")
    assert result == {"success": True}


# ---------------------------------------------------------------------------
# Users — likes / kol endpoints removed
# ---------------------------------------------------------------------------

def test_users_no_likes_attribute():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    assert not hasattr(resource, "likes")


def test_users_no_relationship_method():
    """`.relationship()` was removed — replaced by `.check_follow()`."""
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    assert not hasattr(resource, "relationship")


def test_client_has_no_kol_resource():
    """The `kol` resource was removed — `/kol/timeline` no longer exists."""
    client = XCropClient(api_key="test")
    assert not hasattr(client, "kol")
    client.close()


def test_users_check_follow():
    transport = MagicMock()
    transport.get.return_value = {"data": {"source_follows_target": True}}
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    result = resource.check_follow(source="jack", target="elonmusk")
    assert result == {"data": {"source_follows_target": True}}
    transport.get.assert_called_once_with("/users/check-follow", source="jack", target="elonmusk")


def test_users_check_qualified_account():
    transport = MagicMock()
    transport.get.return_value = {"data": {"qualified": True}}
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    result = resource.check_qualified_account("elonmusk", min_followers=100, min_age_days=30)
    assert result == {"data": {"qualified": True}}


def test_users_check_qualified_name():
    transport = MagicMock()
    transport.get.return_value = {"data": {"qualified": True}}
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    result = resource.check_qualified_name("elonmusk", contains="Musk", position="anywhere")
    assert result == {"data": {"qualified": True}}


# ---------------------------------------------------------------------------
# Communities (beta)
# ---------------------------------------------------------------------------

def test_communities_get():
    transport = MagicMock()
    transport.get.return_value = {"data": {"id": "123"}}
    from xcrop.resources.communities import CommunitiesResource
    resource = CommunitiesResource(transport)
    result = resource.get("123")
    assert result == {"data": {"id": "123"}}
    transport.get.assert_called_once_with("/communities/123")


def test_client_has_communities_resource():
    client = XCropClient(api_key="test")
    assert client.communities is not None
    client.close()


# ---------------------------------------------------------------------------
# Pagination max_pages safety
# ---------------------------------------------------------------------------

def test_pagination_max_pages_limit():
    """Pagination should stop after max_pages even if server keeps returning has_next."""
    transport = MagicMock()
    transport.get.return_value = {
        "data": [{"id": "1"}],
        "meta": {"has_next": True, "cursor": "next"},
    }
    from xcrop.resources.users import _PaginatedEndpoint
    endpoint = _PaginatedEndpoint(transport, "/users/{username}/tweets")
    items = list(endpoint.paginate("test", count=999999, max_pages=3))
    # Should have called get exactly 3 times (max_pages=3)
    assert transport.get.call_count == 3
    assert len(items) == 3


# ---------------------------------------------------------------------------
# Transport — headers not mutated on user client
# ---------------------------------------------------------------------------

def test_transport_does_not_mutate_user_client_headers():
    """When a user provides their own httpx.Client, its headers should not be mutated."""
    import httpx
    client = httpx.Client()
    original_headers = dict(client.headers)
    transport = HttpTransport(api_key="test_key", http_client=client)
    # The user client's headers should remain unchanged
    assert dict(client.headers) == original_headers
    client.close()


# ---------------------------------------------------------------------------
# Client context managers
# ---------------------------------------------------------------------------

def test_sync_client_context_manager():
    with XCropClient(api_key="test") as client:
        assert client.users is not None
        assert client.tweets is not None


# ---------------------------------------------------------------------------
# py.typed marker
# ---------------------------------------------------------------------------

def test_py_typed_exists():
    import pathlib
    marker = pathlib.Path(xcrop.__file__).parent / "py.typed"
    assert marker.exists(), "py.typed marker file should exist in xcrop package"


# ---------------------------------------------------------------------------
# 1.1.0: new endpoints and params
# ---------------------------------------------------------------------------

def test_tweets_retweeters_path():
    transport = MagicMock()
    transport.get.return_value = {"data": []}
    from xcrop.resources.tweets import TweetsResource
    TweetsResource(transport).retweeters("123", count=50, cursor="c")
    transport.get.assert_called_once_with("/tweets/123/retweeters", count=50, cursor="c")


def test_tweets_conversation_sort_and_window():
    transport = MagicMock()
    from xcrop.resources.tweets import TweetsResource
    TweetsResource(transport).conversation("1", sort="likes", since="2026-11-01", until=1763251200)
    transport.get.assert_called_once_with(
        "/tweets/1/conversation", count=20, cursor=None,
        sort="likes", since="2026-11-01", until=1763251200,
    )


def test_tweets_quotes_rejects_sort():
    transport = MagicMock()
    from xcrop.resources.tweets import TweetsResource
    with pytest.raises(TypeError):
        TweetsResource(transport).quotes("1", sort="likes")


def test_users_following_ids():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    UsersResource(transport).following_ids("jack", count=5000)
    transport.get.assert_called_once_with("/users/jack/following-ids", count=5000, cursor=None)


def test_users_user_id_forms():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    res = UsersResource(transport)
    res.tweets(user_id=44196397)
    transport.get.assert_called_with(
        "/users/id:44196397/tweets", count=20, cursor=None, user_id="44196397",
    )
    res.get(user_id="44196397")
    transport.get.assert_called_with("/users/id:44196397", user_id="44196397")
    res.get("id:44196397")
    transport.get.assert_called_with("/users/id:44196397")
    with pytest.raises(ValueError):
        res.tweets()


def test_users_include_unavailable_and_mentions_window():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    res = UsersResource(transport)
    res.followers("nasa", include_unavailable=True)
    transport.get.assert_called_with(
        "/users/nasa/followers", count=20, cursor=None, include_unavailable="true",
    )
    res.mentions("nasa", since="2026-11-01")
    transport.get.assert_called_with(
        "/users/nasa/mentions", count=20, cursor=None, since="2026-11-01",
    )
    with pytest.raises(TypeError):
        res.tweets("nasa", include_unavailable=True)


def test_users_batch_ids_as_strings():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    res = UsersResource(transport)
    res.batch(ids=[44196397, "1893456789012345678"])
    transport.post.assert_called_with(
        "/users/batch", body={"ids": ["44196397", "1893456789012345678"]},
    )
    res.batch(["jack"])
    transport.post.assert_called_with("/users/batch", body={"usernames": ["jack"]})
    with pytest.raises(ValueError):
        res.batch(["jack"], ids=["1"])
    with pytest.raises(ValueError):
        res.batch()


def test_lists_tweets_window():
    transport = MagicMock()
    from xcrop.resources.lists import ListsResource
    res = ListsResource(transport)
    res.tweets("9", since=1763251200)
    transport.get.assert_called_with("/lists/9/tweets", count=20, cursor=None, since=1763251200)
    with pytest.raises(TypeError):
        res.members("9", since=1)


def test_communities_moderators_and_members_sort():
    transport = MagicMock()
    from xcrop.resources.communities import CommunitiesResource
    res = CommunitiesResource(transport)
    res.moderators("1493446837214187523", count=10, sort="name")
    transport.get.assert_called_with(
        "/communities/1493446837214187523/moderators", count=10, sort="name", cursor=None,
    )


def test_account_credits():
    transport = MagicMock()
    transport.get.return_value = {"data": {"total_remaining": 10}}
    from xcrop.resources.account import AccountResource
    assert AccountResource(transport).credits() == {"data": {"total_remaining": 10}}
    transport.get.assert_called_once_with("/account/credits")


def test_client_exposes_new_resources():
    client = XCropClient(api_key="test")
    assert client.tweets.retweeters is not None
    assert client.users.following_ids is not None
    assert client.communities.moderators is not None
    assert client.account.credits is not None
    client.close()


# ---------------------------------------------------------------------------
# 1.1.0: error codes
# ---------------------------------------------------------------------------

def _fake_response(status, body):
    import httpx
    return httpx.Response(status, json=body, request=httpx.Request("GET", "https://x/y"))


def test_error_code_suspended():
    from xcrop._http import _raise_for_status
    from xcrop.errors import UserSuspendedError
    resp = _fake_response(404, {"error": "User is suspended", "code": "USER_SUSPENDED", "reason": "suspended"})
    with pytest.raises(UserSuspendedError) as ei:
        _raise_for_status(resp)
    assert isinstance(ei.value, NotFoundError)
    assert ei.value.code == "USER_SUSPENDED"
    assert ei.value.reason == "suspended"
    assert ei.value.status_code == 404


def test_error_code_unavailable_reason():
    from xcrop._http import _raise_for_status
    from xcrop.errors import UserUnavailableError
    resp = _fake_response(404, {"error": "x", "code": "USER_UNAVAILABLE", "reason": "deactivated"})
    with pytest.raises(UserUnavailableError) as ei:
        _raise_for_status(resp)
    assert ei.value.reason == "deactivated"


def test_error_code_plain_not_found_and_bad_request():
    from xcrop._http import _raise_for_status
    with pytest.raises(NotFoundError) as ei:
        _raise_for_status(_fake_response(404, {"error": "User not found", "code": "NOT_FOUND", "reason": "not_found"}))
    assert type(ei.value) is NotFoundError
    assert ei.value.code == "NOT_FOUND"
    with pytest.raises(XCropError) as ei2:
        _raise_for_status(_fake_response(400, {"error": "bad", "code": "BAD_TIME_WINDOW"}))
    assert ei2.value.code == "BAD_TIME_WINDOW"
    with pytest.raises(ServerError) as ei3:
        _raise_for_status(_fake_response(500, {"error": "boom", "code": "INTERNAL_ERROR"}))
    assert ei3.value.code == "INTERNAL_ERROR"


def test_error_code_constants_exported():
    assert xcrop.ErrorCode.BAD_COMMUNITY_ID == "BAD_COMMUNITY_ID"
    assert xcrop.UserSuspendedError is not None


# ---------------------------------------------------------------------------
# 1.2.0: write API
# ---------------------------------------------------------------------------

def test_tweets_bookmark_pin_paths():
    transport = MagicMock()
    from xcrop.resources.tweets import TweetsResource
    res = TweetsResource(transport)
    res.bookmark("5")
    transport.post.assert_called_with("/tweets/5/bookmark")
    res.unbookmark("5")
    transport.delete.assert_called_with("/tweets/5/bookmark")
    res.pin("5")
    transport.post.assert_called_with("/tweets/5/pin")
    res.unpin("5")
    transport.delete.assert_called_with("/tweets/5/pin")


def test_users_mute_block_paths():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    res = UsersResource(transport)
    res.mute("jack")
    transport.post.assert_called_with("/users/jack/mute")
    res.unmute("id:12")
    transport.delete.assert_called_with("/users/id:12/mute")
    res.block(user_id=12)
    transport.post.assert_called_with("/users/id:12/block")
    res.unblock("jack")
    transport.delete.assert_called_with("/users/jack/block")
    with pytest.raises(ValueError):
        res.mute()


def test_account_update_profile():
    transport = MagicMock()
    from xcrop.resources.account import AccountResource
    res = AccountResource(transport)
    res.update_profile(name="N", location="L")
    transport.post.assert_called_with("/account/profile", body={"name": "N", "location": "L"})
    with pytest.raises(ValueError):
        res.update_profile()


def test_dm_send():
    transport = MagicMock()
    from xcrop.resources.dm import DmResource
    res = DmResource(transport)
    res.send("jack", "hi")
    transport.post.assert_called_with("/dm/send", body={"text": "hi", "username": "jack"})
    res.send(text="yo", user_id=1893456789012345678)
    transport.post.assert_called_with("/dm/send", body={"text": "yo", "user_id": "1893456789012345678"})
    with pytest.raises(ValueError):
        res.send(text="x")


def test_media_upload_encodes_bytes():
    transport = MagicMock()
    from xcrop.resources.media import MediaResource
    res = MediaResource(transport)
    res.upload(b"abc", "image/png")
    transport.post.assert_called_with("/media/upload", body={"base64": "YWJj", "mime_type": "image/png"})
    res.upload("YWJj")
    transport.post.assert_called_with("/media/upload", body={"base64": "YWJj", "mime_type": "image/jpeg"})


def test_tweets_create_community_id_is_string():
    transport = MagicMock()
    from xcrop.resources.tweets import TweetsResource
    res = TweetsResource(transport)
    res.create("hi")
    transport.post.assert_called_with("/tweets/create", body={"text": "hi"})
    res.create("hi", community_id=1493446837214187523, media_ids=["9"])
    transport.post.assert_called_with(
        "/tweets/create",
        body={"text": "hi", "media_ids": ["9"], "community_id": "1493446837214187523"},
    )


def test_include_replies_on_quotes_and_list_tweets():
    transport = MagicMock()
    from xcrop.resources.tweets import TweetsResource
    from xcrop.resources.lists import ListsResource
    TweetsResource(transport).quotes("1", include_replies=False)
    transport.get.assert_called_with("/tweets/1/quotes", count=20, cursor=None, include_replies="false")
    ListsResource(transport).tweets("9", include_replies=True)
    transport.get.assert_called_with("/lists/9/tweets", count=20, cursor=None, include_replies="true")
    with pytest.raises(TypeError):
        TweetsResource(transport).retweeters("1", include_replies=False)
    with pytest.raises(TypeError):
        ListsResource(transport).members("9", include_replies=False)


def test_client_exposes_dm_and_media():
    client = XCropClient(api_key="test")
    assert client.dm.send is not None
    assert client.media.upload is not None
    client.close()
    aclient = AsyncXCropClient(api_key="test")
    assert aclient.dm.send is not None
    assert aclient.media.upload is not None
    assert aclient.users.mute is not None


def test_write_error_codes_and_x_reason():
    from xcrop._http import _raise_for_status
    assert xcrop.ErrorCode.X_REFUSED == "X_REFUSED"
    assert xcrop.ErrorCode.DM_NOT_ALLOWED == "DM_NOT_ALLOWED"
    with pytest.raises(XCropError) as ei:
        _raise_for_status(_fake_response(400, {"error": "X refused", "code": "X_REFUSED", "x_reason": "not yours"}))
    assert ei.value.code == "X_REFUSED"
    assert ei.value.x_reason == "not yours"
    with pytest.raises(NotFoundError) as ei2:
        _raise_for_status(_fake_response(404, {"error": "gone", "code": "NOT_FOUND", "x_reason": "Missing"}))
    assert ei2.value.x_reason == "Missing"
    with pytest.raises(AuthError) as ei3:
        _raise_for_status(_fake_response(403, {"error": "no", "code": "DM_NOT_ALLOWED"}))
    assert ei3.value.code == "DM_NOT_ALLOWED"
    assert ei3.value.x_reason is None


def test_user_agent_uses_version():
    t = HttpTransport(api_key="k")
    assert t._default_hdrs["User-Agent"] == "xcrop-python/1.2.0"
    t.close()
