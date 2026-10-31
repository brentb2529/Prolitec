"""Async client for Prolitec ScenXus devices.

Authenticates against the ScenXus web backend with email + password (the
backend performs the Ayla sign-in server-side) and controls the device through
its device-service proxy, authorized by the session cookie set at login.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import BASE_URL, DEVICE_SVC, LOGIN_PATH

_LOGGER = logging.getLogger(__name__)


class ScenXusAuthError(Exception):
    """Raised when authentication fails (bad email/password)."""


class ScenXusApiError(Exception):
    """Raised for non-auth API errors."""


class ScenXusApi:
    """Client for a ScenXus account.

    `session` must be a dedicated aiohttp session with its own cookie jar so the
    login cookies are isolated to this integration.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._logged_in = False
        self._auth_lock = asyncio.Lock()

    # -- Authentication -------------------------------------------------------

    async def async_login(self) -> None:
        """Log in; stores the session cookies in the session's cookie jar."""
        url = f"{BASE_URL}{LOGIN_PATH}"
        payload = {"email": self._email, "password": self._password}
        try:
            async with self._session.post(
                url, json=payload, headers={"Accept": "application/json"}
            ) as resp:
                data = await _json(resp)
                if resp.status >= 500:
                    raise ScenXusApiError(f"Login server error {resp.status}")
                # The endpoint returns 200 with {"success": bool, "errors": [...]}.
                if isinstance(data, dict) and data.get("success") is False:
                    errors = data.get("errors") or ["Invalid credentials"]
                    raise ScenXusAuthError("; ".join(str(e) for e in errors)[:200])
                if resp.status in (401, 403):
                    raise ScenXusAuthError("Invalid email or password")
                if resp.status >= 400:
                    raise ScenXusApiError(f"Login failed ({resp.status})")
        except aiohttp.ClientError as err:
            raise ScenXusApiError(f"Login request failed: {err}") from err
        self._logged_in = True
        _LOGGER.debug("ScenXus login successful for %s", self._email)

    async def _async_ensure_login(self) -> None:
        async with self._auth_lock:
            if not self._logged_in:
                await self.async_login()

    # -- Core request helper --------------------------------------------------

    async def _request(
        self, method: str, path: str, *, json_body: Any | None = None, _retry: bool = True
    ) -> Any:
        await self._async_ensure_login()
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.request(
                method,
                url,
                json=json_body,
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status in (401, 403) and _retry:
                    # Session expired -> re-login once and retry.
                    _LOGGER.debug("Session expired (%s); re-logging in", resp.status)
                    self._logged_in = False
                    await self._async_ensure_login()
                    return await self._request(
                        method, path, json_body=json_body, _retry=False
                    )
                if resp.status in (401, 403):
                    self._logged_in = False
                    raise ScenXusAuthError("Unauthorized after re-login")
                if resp.status >= 400:
                    text = await resp.text()
                    raise ScenXusApiError(f"{method} {path} -> {resp.status}: {text[:200]}")
                return await _json(resp)
        except aiohttp.ClientError as err:
            raise ScenXusApiError(f"{method} {path} failed: {err}") from err

    # -- Device / property operations ----------------------------------------

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the list of device objects on the account."""
        data = await self._request("GET", f"{DEVICE_SVC}/devices.json")
        if isinstance(data, dict):
            data = data.get("devices", [])
        result = []
        for item in data or []:
            if isinstance(item, dict):
                result.append(item.get("device", item))
        return result

    async def async_get_device(self, dsn: str) -> dict[str, Any]:
        """Return the device object for a DSN."""
        data = await self._request("GET", f"{DEVICE_SVC}/dsns/{dsn}")
        if isinstance(data, dict):
            return data.get("device", data)
        return {}

    async def async_get_properties(self, dsn: str) -> dict[str, Any]:
        """Return a {property_name: value} map for a device."""
        data = await self._request("GET", f"{DEVICE_SVC}/dsns/{dsn}/properties.json")
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
        path = f"{DEVICE_SVC}/dsns/{dsn}/properties/{name}/datapoints"
        await self._request("POST", path, json_body={"datapoint": {"value": value}})
        _LOGGER.debug("Set %s = %s on %s", name, value, dsn)


async def _json(resp: aiohttp.ClientResponse) -> Any:
    """Parse JSON tolerantly (ScenXus/Ayla sometimes omit the JSON content-type)."""
    try:
        return await resp.json(content_type=None)
    except Exception:  # noqa: BLE001
        import json

        try:
            return json.loads(await resp.text())
        except (json.JSONDecodeError, aiohttp.ClientError):
            return {}
