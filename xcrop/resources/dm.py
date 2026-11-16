"""Direct messages resource: send a 1:1 DM from the connected account."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from .._http import AsyncHttpTransport, HttpTransport


def _dm_body(
    username: Optional[str],
    text: str,
    user_id: Optional[Union[str, int]],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"text": text}
    if user_id is not None:
        # String, so ids above 2^53 never lose precision in JSON.
        body["user_id"] = str(user_id)
    elif username is not None:
        body["username"] = username
    else:
        raise ValueError("Provide a username or a user_id.")
    return body


class DmResource:
    """Sync DM resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def send(
        self,
        username: Optional[str] = None,
        text: str = "",
        *,
        user_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Send a 1:1 direct message (requires connected account).

        Args:
            username: Recipient handle (or pass ``user_id``).
            text: Message text, 1 to 10000 characters.
            user_id: Numeric recipient id, used instead of ``username``.

        ``data`` is ``{recipient_id, username, message_id, conversation_id}``.
        A recipient whose DM settings refuse this account raises an error with
        code ``DM_NOT_ALLOWED`` (HTTP 403).
        """
        return self._transport.post("/dm/send", body=_dm_body(username, text, user_id))


class AsyncDmResource:
    """Async DM resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def send(
        self,
        username: Optional[str] = None,
        text: str = "",
        *,
        user_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Send a 1:1 direct message. See :meth:`DmResource.send`."""
        return await self._transport.post("/dm/send", body=_dm_body(username, text, user_id))
