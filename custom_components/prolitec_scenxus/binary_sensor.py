"""Binary sensor for ScenXus online/connection status."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScenXusConfigEntry
from .entity import ScenXusEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScenXusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ScenXusOnlineBinarySensor(entry.runtime_data)])


class ScenXusOnlineBinarySensor(ScenXusEntity, BinarySensorEntity):
    """Reports whether the device is connected to the cloud."""

    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "online")

    @property
    def is_on(self) -> bool:
        status = self.coordinator.device_info_raw.get("connection_status")
        return str(status).lower() == "online"
