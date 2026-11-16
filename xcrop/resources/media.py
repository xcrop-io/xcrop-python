"""Media resource: upload an image, GIF or short video for use in tweets."""

from __future__ import annotations

import base64
from typing import Any, Dict, Union

from .._http import AsyncHttpTransport, HttpTransport

MEDIA_MIME_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif", "video/mp4")


def _upload_body(data: Union[bytes, str], mime_type: str) -> Dict[str, Any]:
    """``data`` is raw bytes (encoded here) or an already base64 string."""
    if isinstance(data, (bytes, bytearray)):
        b64 = base64.b64encode(bytes(data)).decode("ascii")
    else:
        b64 = data
    return {"base64": b64, "mime_type": mime_type}


class MediaResource:
    """Sync media resource."""

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def upload(self, data: Union[bytes, str], mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Upload media with the connected account (requires connected account).

        Args:
            data: Raw bytes, or a base64 string (a ``data:...;base64,`` prefix is accepted).
            mime_type: One of ``image/jpeg``, ``image/png``, ``image/webp``,
                ``image/gif``, ``video/mp4``. Max 5 MB decoded.

        ``data["data"]["media_id"]`` goes into ``tweets.create(media_ids=[...])``.
        """
        return self._transport.post("/media/upload", body=_upload_body(data, mime_type))


class AsyncMediaResource:
    """Async media resource."""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def upload(self, data: Union[bytes, str], mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Upload media. See :meth:`MediaResource.upload`."""
        return await self._transport.post("/media/upload", body=_upload_body(data, mime_type))
