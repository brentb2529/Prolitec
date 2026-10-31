# Prolitec ScenXus — Home Assistant integration

Full **control** (not just read-only) of a Prolitec ScenXus HVAC scent diffuser
from Home Assistant. Sign in with your ScenXus email and password — nothing else.

## What you get

**Controls**
- **Mode** (select): Off · 24/7 · Run
- **Off-Cycle** (select): Very Short (30 s) · Short (2 min) · Normal (7 min)
- **Intensity** (number slider, 1–`max_intensity_in`)
- **Fan Speed** (number slider, 0–5; 0 = Off)

**Sensors**
- Fragrance Remaining (%), Cartridge Life (%), Pump Life (%), Appliance Life (%)
- Core Temperature, Error Code, Schedule Running, Host MCU Version (diagnostic)
- Online (connectivity binary sensor)

## How it works

The device is an Ayla-based IoT scent unit. True on-LAN control (Ayla "LAN mode")
is disabled on the hardware (`lan_enabled = false`) and can only be turned on by
Prolitec, so this integration controls the unit through the ScenXus cloud — the
same path the web app uses:

1. `POST https://scenxus.com/api/account/login` with your email + password.
   The ScenXus backend performs the Ayla sign-in server-side and returns a
   session cookie.
2. That session cookie authorizes reads and writes through the device-service
   proxy (`/proxy/deviceServices/apiv1/...`). The integration re-logs in
   automatically if the session expires.

No app keys, tokens, or developer credentials are required.

## Installation

1. Copy `custom_components/prolitec_scenxus/` into your HA
   `config/custom_components/` directory (or add this repo as a HACS custom
   repository), then restart Home Assistant.
2. **Settings → Devices & Services → Add Integration → "Prolitec ScenXus"**.
3. Enter your ScenXus **email** and **password**. If your account has more than
   one device, you'll be asked to pick one.

## Notes

- Poll interval is 30 s. Writes apply immediately and then re-poll.
- The integration reads/writes the `*_in` (commanded) properties, matching what
  the ScenXus web app shows.
- Unofficial, community integration; not affiliated with Prolitec or Ayla
  Networks.
