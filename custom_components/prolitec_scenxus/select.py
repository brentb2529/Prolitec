"""Select entities for Prolitec ScenXus (Mode and Off-Cycle)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScenXusConfigEntry
from .const import (
    CYCLE_MAP,
    CYCLE_MAP_REVERSE,
    MODE_MAP,
    MODE_MAP_REVERSE,
    PROP_CYCLE,
    PROP_MODE,
)
from .entity import ScenXusEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScenXusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            ScenXusSelect(coordinator, PROP_MODE, "Mode", MODE_MAP, MODE_MAP_REVERSE, "mdi:power"),
            ScenXusSelect(
                coordinator, PROP_CYCLE, "Off-Cycle", CYCLE_MAP, CYCLE_MAP_REVERSE, "mdi:timer-outline"
            ),
        ]
    )


class ScenXusSelect(ScenXusEntity, SelectEntity):
    """A mapped integer property exposed as a labelled select."""

    def __init__(self, coordinator, key, name, value_map, reverse_map, icon) -> None:
        super().__init__(coordinator, key)
        self._attr_name = name
        self._attr_icon = icon
        self._value_map = value_map
        self._reverse_map = reverse_map
        self._attr_options = list(value_map.values())

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get(self._key)
        if raw is None:
            return None
        try:
            return self._value_map.get(int(raw))
        except (TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        value = self._reverse_map.get(option)
        if value is not None:
            await self.coordinator.async_set_property(self._key, value)
