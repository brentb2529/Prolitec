"""Number entities for Prolitec ScenXus (Intensity and Fan)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScenXusConfigEntry
from .const import (
    FAN_MAX,
    FAN_MIN,
    INTENSITY_HARD_MAX,
    INTENSITY_MIN,
    PROP_FAN,
    PROP_INTENSITY,
    PROP_MAX_INTENSITY,
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
            ScenXusIntensityNumber(coordinator),
            ScenXusFanNumber(coordinator),
        ]
    )


class ScenXusIntensityNumber(ScenXusEntity, NumberEntity):
    """Fragrance intensity (1..max_intensity_in)."""

    _attr_name = "Intensity"
    _attr_icon = "mdi:scent"
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1
    _attr_native_min_value = INTENSITY_MIN

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, PROP_INTENSITY)

    @property
    def native_max_value(self) -> float:
        raw = self.coordinator.data.get(PROP_MAX_INTENSITY)
        try:
            value = int(raw)
            if INTENSITY_MIN <= value <= INTENSITY_HARD_MAX:
                return value
        except (TypeError, ValueError):
            pass
        return INTENSITY_HARD_MAX

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(PROP_INTENSITY)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_property(PROP_INTENSITY, int(value))


class ScenXusFanNumber(ScenXusEntity, NumberEntity):
    """Fan speed (0=Off, 1..5)."""

    _attr_name = "Fan Speed"
    _attr_icon = "mdi:fan"
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1
    _attr_native_min_value = FAN_MIN
    _attr_native_max_value = FAN_MAX

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, PROP_FAN)

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(PROP_FAN)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_property(PROP_FAN, int(value))
