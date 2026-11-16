"""Shared helpers for optional query parameters (internal)."""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Optional, Union

# ``since`` / ``until`` accept unix seconds, unix milliseconds or an ISO 8601 date/time.
TimeValue = Union[int, float, str]


def encode_query(
    endpoint: str,
    supported: FrozenSet[str],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the non-None options as query parameters.

    Raises:
        TypeError: If an option is set that ``endpoint`` does not support.
    """
    out: Dict[str, Any] = {}
    for key, value in options.items():
        if value is None:
            continue
        if key not in supported:
            raise TypeError(f"{endpoint} does not support the {key!r} option")
        if isinstance(value, bool):
            value = "true" if value else "false"
        out[key] = value
    return out


def user_path(path_template: str, username: Optional[str], user_id: Optional[str]) -> str:
    """Build a ``/users/{username}/...`` path from a username or a numeric id.

    With only ``user_id`` the path uses the ``id:<digits>`` form.
    """
    if username is None and user_id is None:
        raise ValueError("Provide a username or a user_id.")
    ref = username if username is not None else f"id:{user_id}"
    return path_template.format(username=ref)
