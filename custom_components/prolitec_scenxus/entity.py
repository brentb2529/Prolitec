"""Base entity for Prolitec ScenXus."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ScenXusCoordinator


class ScenXusEntity(CoordinatorEntity[ScenXusCoordinator]):
    """Common base: shares the device registry entry and availability."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ScenXusCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.dsn}_{key}"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        # Stable keys so dashboards (B-Panels) can find fields without relying
        # on entity ids or friendly names, which move when renamed.
        raw = self.coordinator.device_info_raw
        return {
            "bp_scenxus_field": self._key,
            "bp_scenxus_dsn": self.coordinator.dsn,
            "bp_scenxus_name": raw.get("product_name") or f"ScenXus {self.coordinator.dsn}",
        }

    @property
    def device_info(self) -> DeviceInfo:
        raw = self.coordinator.device_info_raw
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.dsn)},
            name=raw.get("product_name") or f"ScenXus {self.coordinator.dsn}",
            manufacturer="Prolitec",
            model=raw.get("oem_model") or raw.get("model") or "ScenXus",
            sw_version=raw.get("sw_version"),
            serial_number=self.coordinator.dsn,
            configuration_url="https://scenxus.com",
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.last_update_success
