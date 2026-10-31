"""Constants for the Prolitec ScenXus integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "prolitec_scenxus"

# --- Config entry keys -------------------------------------------------------
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_DSN: Final = "dsn"

# --- ScenXus cloud endpoints -------------------------------------------------
# The ScenXus web backend performs the Ayla sign-in server-side, so the client
# only needs email + password. Control then goes through its device-service
# proxy, authorized by the session cookie set at login.
BASE_URL: Final = "https://scenxus.com"
LOGIN_PATH: Final = "/api/account/login"
DEVICE_SVC: Final = "/proxy/deviceServices/apiv1"

# --- Polling -----------------------------------------------------------------
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# --- Property names (device datapoints) --------------------------------------
PROP_MODE: Final = "current_state_in"
PROP_CYCLE: Final = "cycle_in"
PROP_INTENSITY: Final = "current_intensity_in"
PROP_FAN: Final = "fan_in"
PROP_MAX_INTENSITY: Final = "max_intensity_in"

PROP_SCHEDULE_RUNNING: Final = "current_schedule_running"
PROP_FRAGRANCE_REMAINING: Final = "fragrance_remaining"
PROP_CARTRIDGE_LIFE: Final = "cartridge_life"
PROP_PUMP_LIFE: Final = "pump_life"
PROP_APPLIANCE_LIFE: Final = "appliance_life"
PROP_ERROR_CODE: Final = "error_code"
PROP_CORE_TEMP: Final = "esp32_core_temp"
PROP_HOST_MCU_VERSION: Final = "host_mcu_version"

# --- Value maps (extracted from the ScenXus web app) -------------------------
# Mode: current_state_in. Value 2 is unused by the web app.
MODE_MAP: Final = {1: "Off", 3: "24/7", 4: "Run"}
MODE_MAP_REVERSE: Final = {v: k for k, v in MODE_MAP.items()}

# Off-cycle: cycle_in.
CYCLE_MAP: Final = {
    1: "Very Short (30 Sec)",
    2: "Short (2 Min)",
    3: "Normal (7 Min)",
}
CYCLE_MAP_REVERSE: Final = {v: k for k, v in CYCLE_MAP.items()}

# Fan speed: fan_in. 0 = Off, 1..5 = speed.
FAN_MIN: Final = 0
FAN_MAX: Final = 5

# Intensity: current_intensity_in. 1..max_intensity_in (hard cap 50).
INTENSITY_MIN: Final = 1
INTENSITY_HARD_MAX: Final = 50
