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
    assert __version__ == "1.0.0"


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
# KOL validation
# ---------------------------------------------------------------------------

def test_kol_empty_usernames_raises():
    transport = MagicMock()
    from xcrop.resources.kol import KolResource
    resource = KolResource(transport)
    with pytest.raises(ValueError, match="empty"):
        resource.timeline([])


# ---------------------------------------------------------------------------
# Users — likes endpoint removed
# ---------------------------------------------------------------------------

def test_users_no_likes_attribute():
    transport = MagicMock()
    from xcrop.resources.users import UsersResource
    resource = UsersResource(transport)
    assert not hasattr(resource, "likes")


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
