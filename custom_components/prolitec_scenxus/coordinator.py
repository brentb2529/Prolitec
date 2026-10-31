"""DataUpdateCoordinator for Prolitec ScenXus."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ScenXusApi, ScenXusApiError, ScenXusAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ScenXusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls a single ScenXus device's properties."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: ScenXusApi,
        dsn: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{dsn}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.dsn = dsn
        self.entry = entry
        self.device_info_raw: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Refresh the device object too (connection_status, versions, etc.).
            self.device_info_raw = await self.api.async_get_device(self.dsn)
            return await self.api.async_get_properties(self.dsn)
        except ScenXusAuthError as err:
            # Triggers Home Assistant's reauth flow (prompt for new password).
            raise ConfigEntryAuthFailed(str(err)) from err
        except ScenXusApiError as err:
            raise UpdateFailed(f"Error updating ScenXus data: {err}") from err

    async def async_set_property(self, name: str, value: Any) -> None:
        """Write a property, then update local state and request a refresh."""
        await self.api.async_set_property(self.dsn, name, value)
        if self.data is not None:
            self.data[name] = value
            self.async_set_updated_data(self.data)
        await self.async_request_refresh()
