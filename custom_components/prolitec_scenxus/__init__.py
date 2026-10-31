"""The Prolitec ScenXus integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import ScenXusApi, ScenXusApiError, ScenXusAuthError
from .const import CONF_DSN, CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import ScenXusCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

ScenXusConfigEntry = ConfigEntry[ScenXusCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ScenXusConfigEntry) -> bool:
    """Set up Prolitec ScenXus from a config entry."""
    # Dedicated session so the login cookies stay isolated to this entry.
    session = async_create_clientsession(hass)
    api = ScenXusApi(
        session,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await api.async_login()
    except ScenXusAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except ScenXusApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = ScenXusCoordinator(hass, entry, api, entry.data[CONF_DSN])
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ScenXusConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: ScenXusConfigEntry
) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
