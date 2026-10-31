"""Async client for Prolitec ScenXus devices.

Authenticates against the ScenXus web backend with email + password to obtain a
Bearer token, then reads and controls the device directly through the ScenXus
device-service proxy (`/proxy/deviceServices/apiv1/...`) using that token.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import time
from typing import Any

import aiohttp

from .const import BASE_URL, DEVICE_SVC, LOGIN_PATH

_LOGGER = logging.getLogger(__name__)

# Refresh the token this many seconds before its expiry.
_TOKEN_MARGIN = 60
# Fallback lifetime if the token has no decodable expiry.
_DEFAULT_LIFETIME = 240


class ScenXusAuthError(Exception):
    """Raised when authentication fails (bad email/password)."""


class ScenXusApiError(Exception):
    """Raised for non-auth API errors."""


class ScenXusApi:
    """Client for a ScenXus account / device."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._token_exp: float = 0.0
        self._auth_lock = asyncio.Lock()

    # -- Authentication -------------------------------------------------------

    async def async_login(self) -> None:
        """Log in and store the Bearer token."""
        url = f"{BASE_URL}{LOGIN_PATH}"
        payload = {"email": self._email, "password": self._password}
        try:
            async with self._session.post(
                url, json=payload, headers={"Accept": "application/json"}
            ) as resp:
                data = await _json(resp)
                if resp.status >= 500:
                    raise ScenXusApiError(f"Login server error {resp.status}")
                if not isinstance(data, dict) or data.get("success") is not True:
                    errors = (data or {}).get("errors") if isinstance(data, dict) else None
                    raise ScenXusAuthError(
                        "; ".join(map(str, errors))[:200]
                        if errors
                        else "Invalid email or password"
                    )
                token = (data.get("result") or {}).get("token")
                if not token:
                    raise ScenXusAuthError("Login succeeded but returned no token")
        except aiohttp.ClientError as err:
            raise ScenXusApiError(f"Login request failed: {err}") from err

        self._token = token
        self._token_exp = _jwt_exp(token) or (time.time() + _DEFAULT_LIFETIME)
        _LOGGER.debug("ScenXus login OK for %s (token exp in %.0fs)",
                      self._email, self._token_exp - time.time())

    async def _async_ensure_token(self) -> None:
        async with self._auth_lock:
            if self._token is None or time.time() >= self._token_exp - _TOKEN_MARGIN:
                await self.async_login()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    # -- Core request helper --------------------------------------------------

    async def _request(
        self, method: str, path: str, *, json_body: Any | None = None, _retry: bool = True
    ) -> Any:
        await self._async_ensure_token()
        url = f"{BASE_URL}{DEVICE_SVC}{path}"
        headers = self._headers()
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        try:
            async with self._session.request(
                method, url, json=json_body, headers=headers
            ) as resp:
                text = await resp.text()
                if resp.status in (401, 403) and _retry:
                    self._token = None
                    await self._async_ensure_token()
                    return await self._request(
                        method, path, json_body=json_body, _retry=False
                    )
                if resp.status >= 400:
                    raise ScenXusApiError(f"{method} {path} -> {resp.status}: {text[:200]}")
                return _parse(text)
        except aiohttp.ClientError as err:
            raise ScenXusApiError(f"{method} {path} failed: {err}") from err

    # -- Device operations ----------------------------------------------------

    async def async_get_device(self, dsn: str) -> dict[str, Any]:
        """Return the device object (name, model, connection_status, ...)."""
        data = await self._request("GET", f"/dsns/{dsn}")
        if isinstance(data, dict):
            return data.get("device", data)
        return {}

    async def async_get_properties(self, dsn: str) -> dict[str, Any]:
        """Return a {property_name: value} map for the device."""
        data = await self._request("GET", f"/dsns/{dsn}/properties.json")
        result: dict[str, Any] = {}
        if isinstance(data, list):
            for item in data:
                prop = item.get("property", {}) if isinstance(item, dict) else {}
                name = prop.get("name")
                if name is not None:
                    result[name] = prop.get("value")
        return result

    async def async_set_property(self, dsn: str, name: str, value: Any) -> None:
        """Write a datapoint to an input property."""
        path = f"/dsns/{dsn}/properties/{name}/datapoints"
        await self._request("POST", path, json_body={"datapoint": {"value": value}})
        _LOGGER.debug("Set %s = %s on %s", name, value, dsn)


def _jwt_exp(token: str) -> float:
    """Return the `exp` claim (unix seconds) from a JWT, or 0 if undecodable."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload.get("exp", 0))
    except (IndexError, ValueError, binascii.Error, json.JSONDecodeError):
        return 0.0


def _parse(text: str) -> Any:
    """Parse a JSON response body; non-JSON (e.g. XML datapoint echo) -> None."""
    text = text.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def _json(resp: aiohttp.ClientResponse) -> Any:
    try:
        return await resp.json(content_type=None)
    except (aiohttp.ClientError, ValueError):
        return _parse(await resp.text())
