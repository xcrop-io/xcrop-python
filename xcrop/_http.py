"""Low-level HTTP transport with retry, rate-limit back-off, and SSE streaming."""

from __future__ import annotations

import json
import time
import asyncio
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Union,
)

import httpx

from ._version import __version__
from .errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    StreamError,
    XCropError,
)

DEFAULT_BASE_URL = "https://xcrop.io/api/v2"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_BACKOFF_MAX = 30.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raise_for_status(response: httpx.Response) -> None:
    """Raise a typed exception based on the HTTP status code."""
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.json()
        message = body.get("error", response.text)
        code = body.get("code", "")
    except Exception:
        message = response.text or f"HTTP {status}"
        code = ""

    if status == 401 or status == 403:
        raise AuthError(message, status_code=status, error_code=code, response=response)
    if status == 404:
        raise NotFoundError(message, error_code=code, response=response)
    if status == 429:
        retry_after = _parse_retry_after(response)
        raise RateLimitError(
            message, retry_after=retry_after, error_code=code, response=response,
        )
    if 500 <= status < 600:
        raise ServerError(message, status_code=status, error_code=code, response=response)

    raise XCropError(message, status_code=status, error_code=code, response=response)


def _parse_retry_after(response: httpx.Response) -> Optional[float]:
    val = response.headers.get("retry-after")
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _backoff(attempt: int) -> float:
    return min(RETRY_BACKOFF_BASE * (2 ** attempt), RETRY_BACKOFF_MAX)


def _should_retry(status: int) -> bool:
    return status == 429 or status >= 500


def _parse_sse_data(event_str: str) -> Optional[str]:
    """Parse an SSE event block, concatenating multiple data: lines per spec."""
    data_lines = []
    for line in event_str.split("\n"):
        if line.startswith("data: "):
            data_lines.append(line[6:])
        elif line.startswith("data:"):
            data_lines.append(line[5:])
    if not data_lines:
        return None
    joined = "\n".join(data_lines)
    if joined == "[DONE]":
        return None
    return joined


# ---------------------------------------------------------------------------
# Sync transport
# ---------------------------------------------------------------------------

class HttpTransport:
    """Synchronous HTTP transport with automatic retries."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._default_hdrs = self._default_headers()
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"xcrop-python/{__version__}",
            "Accept": "application/json",
        }

    # -- core request --

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.request(
                    method, url, params=params, json=json_body,
                    headers=self._default_hdrs,
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise XCropError(f"Transport error: {exc}") from exc

            if resp.is_success:
                return resp.json()  # type: ignore[no-any-return]

            if _should_retry(resp.status_code) and attempt < self.max_retries:
                wait = _backoff(attempt)
                if resp.status_code == 429:
                    ra = _parse_retry_after(resp)
                    if ra is not None:
                        wait = ra
                time.sleep(wait)
                last_exc = None
                continue

            _raise_for_status(resp)

        # Should not reach here, but just in case
        if last_exc:
            raise XCropError(f"Max retries exceeded: {last_exc}") from last_exc
        raise XCropError("Max retries exceeded")

    def get(self, path: str, **params: Any) -> Dict[str, Any]:
        # Filter None values
        cleaned = {k: v for k, v in params.items() if v is not None}
        return self.request("GET", path, params=cleaned)

    def post(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("POST", path, json_body=body)

    def delete(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("DELETE", path, json_body=body)

    # -- SSE streaming --

    def stream_sse(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        with self._client.stream(
            method, url, params=params, json=json_body, headers=self._default_hdrs,
        ) as resp:
            if not resp.is_success:
                resp.read()
                _raise_for_status(resp)
            buffer = ""
            for chunk in resp.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    data = _parse_sse_data(event_str)
                    if data is not None:
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


# ---------------------------------------------------------------------------
# Async transport
# ---------------------------------------------------------------------------

class AsyncHttpTransport:
    """Asynchronous HTTP transport with automatic retries."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._default_hdrs = self._default_headers()
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"xcrop-python/{__version__}",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.request(
                    method, url, params=params, json=json_body,
                    headers=self._default_hdrs,
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise XCropError(f"Transport error: {exc}") from exc

            if resp.is_success:
                return resp.json()  # type: ignore[no-any-return]

            if _should_retry(resp.status_code) and attempt < self.max_retries:
                wait = _backoff(attempt)
                if resp.status_code == 429:
                    ra = _parse_retry_after(resp)
                    if ra is not None:
                        wait = ra
                await asyncio.sleep(wait)
                last_exc = None
                continue

            _raise_for_status(resp)

        if last_exc:
            raise XCropError(f"Max retries exceeded: {last_exc}") from last_exc
        raise XCropError("Max retries exceeded")

    async def get(self, path: str, **params: Any) -> Dict[str, Any]:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return await self.request("GET", path, params=cleaned)

    async def post(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.request("POST", path, json_body=body)

    async def delete(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.request("DELETE", path, json_body=body)

    async def stream_sse(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        async with self._client.stream(
            method, url, params=params, json=json_body, headers=self._default_hdrs,
        ) as resp:
            if not resp.is_success:
                await resp.aread()
                _raise_for_status(resp)
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    data = _parse_sse_data(event_str)
                    if data is not None:
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
