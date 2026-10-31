"""Sensor entities for Prolitec ScenXus (status / diagnostics)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScenXusConfigEntry
from .const import (
    KEY_FRAGRANCE_PCT,
    PROP_APPLIANCE_LIFE,
    PROP_CARTRIDGE_LIFE,
    PROP_CORE_TEMP,
    PROP_ERROR_CODE,
    PROP_HOST_MCU_VERSION,
    PROP_PUMP_LIFE,
    PROP_SCHEDULE_RUNNING,
)
from .entity import ScenXusEntity


@dataclass(frozen=True, kw_only=True)
class ScenXusSensorDescription(SensorEntityDescription):
    """Describes a ScenXus sensor and how to read its value."""

    value_fn: Callable[[Any], Any] = lambda v: v


SENSORS: tuple[ScenXusSensorDescription, ...] = (
    ScenXusSensorDescription(
        key=KEY_FRAGRANCE_PCT,
        name="Fragrance Remaining",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:cup-water",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ScenXusSensorDescription(
        key=PROP_CARTRIDGE_LIFE,
        name="Cartridge Life",
        icon="mdi:cable-data",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ScenXusSensorDescription(
        key=PROP_PUMP_LIFE,
        name="Pump Life",
        icon="mdi:pump",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ScenXusSensorDescription(
        key=PROP_APPLIANCE_LIFE,
        name="Appliance Life",
        icon="mdi:air-filter",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ScenXusSensorDescription(
        key=PROP_CORE_TEMP,
        name="Core Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ScenXusSensorDescription(
        key=PROP_ERROR_CODE,
        name="Error Code",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ScenXusSensorDescription(
        key=PROP_SCHEDULE_RUNNING,
        name="Schedule Running",
        icon="mdi:calendar-clock",
    ),
    ScenXusSensorDescription(
        key=PROP_HOST_MCU_VERSION,
        name="Host MCU Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScenXusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ScenXusSensor(coordinator, desc) for desc in SENSORS)


class ScenXusSensor(ScenXusEntity, SensorEntity):
    """A read-only ScenXus property."""

    entity_description: ScenXusSensorDescription

    def __init__(self, coordinator, description: ScenXusSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        raw = self.coordinator.data.get(self.entity_description.key)
        if raw is None:
            return None
        return self.entity_description.value_fn(raw)
