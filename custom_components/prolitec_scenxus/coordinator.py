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
from .const import (
    CART_CAPACITY,
    CART_FIELD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KEY_FRAGRANCE_PCT,
    PROP_CARTRIDGE_LIFE,
)

_LOGGER = logging.getLogger(__name__)


def _fragrance_pct(
    cartridge_life: Any,
    cart_name: str | None,
    fragrance: str | None,
    fragrances: list[dict[str, Any]],
) -> float | None:
    """Reproduce the ScenXus app's Fragrance Remaining % calculation."""
    capacity = CART_CAPACITY.get(cart_name or "")
    field = CART_FIELD.get(cart_name or "")
    if not capacity or not field or cartridge_life is None or not fragrances:
        return None
    def _ci_get(rec: dict[str, Any], name: str) -> Any:
        """Case-insensitive field lookup (JSON casing may vary)."""
        if name in rec:
            return rec[name]
        low = name.lower()
        return next((v for k, v in rec.items() if k.lower() == low), None)

    record = next(
        (f for f in fragrances if str(_ci_get(f, "fragrance")) == str(fragrance)),
        None,
    )
    if not record:
        return None
    try:
        rate = float(_ci_get(record, field))
        density = float(_ci_get(record, "density"))
        if rate <= 0 or density <= 0:
            return None
        hours = float(cartridge_life) / 3600.0
        consumed = hours * (rate / density)
        return round(max(0.0, capacity - consumed) / capacity * 100.0, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


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
        self._datums: dict[str, Any] = {}
        self._fragrances: list[dict[str, Any]] = []

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Refresh the device object too (connection_status, versions, etc.).
            self.device_info_raw = await self.api.async_get_device(self.dsn)
            props = await self.api.async_get_properties(self.dsn)

            # Fetch the (near-static) metadata needed for Fragrance Remaining once.
            if not self._datums:
                try:
                    self._datums = await self.api.async_get_datums(self.dsn)
                except ScenXusApiError:
                    self._datums = {}
            if not self._fragrances:
                try:
                    self._fragrances = await self.api.async_get_fragrances()
                except ScenXusApiError:
                    self._fragrances = []

            props[KEY_FRAGRANCE_PCT] = _fragrance_pct(
                props.get(PROP_CARTRIDGE_LIFE),
                self._datums.get("CartName"),
                self._datums.get("Fragrance"),
                self._fragrances,
            )
            return props
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
