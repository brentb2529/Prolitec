# Prolitec ScenXus — Home Assistant integration

Full **control** (not just read-only) of a Prolitec ScenXus HVAC scent diffuser
from Home Assistant. Sign in with your ScenXus email + password and your device's
DSN — everything is entered in the UI, no YAML.

## What you get

**Controls**
- **Mode** (select): Off · 24/7 · Run
- **Off-Cycle** (select): Very Short (30 s) · Short (2 min) · Normal (7 min)
- **Intensity** (number slider, 1–`max_intensity_in`)
- **Fan Speed** (number slider, 0–5; 0 = Off)

**Sensors**
- Fragrance Remaining (%), Cartridge Life, Pump Life, Appliance Life
- Core Temperature, Error Code, Schedule Running, Host MCU Version (diagnostic)
- Online (connectivity binary sensor)

## How it works

The device runs on the ScenXus cloud (an Ayla IoT platform). The integration:

1. Signs in at `POST https://scenxus.com/api/account/login` with your email +
   password to obtain a Bearer token (auto-refreshed before it expires).
2. Reads and controls the device directly through the ScenXus device-service
   proxy — `GET /proxy/deviceServices/apiv1/dsns/<DSN>/properties.json` for state
   and `POST .../properties/<name>/datapoints` for control — using that token.

No app keys, Ayla credentials, or developer accounts are needed. True on-LAN
control (Ayla "LAN mode") is disabled on the hardware (`lan_enabled = false`) and
can only be enabled by Prolitec, so this uses the cloud path — the same one the
ScenXus web app uses.

## Installation (HACS)

1. **HACS → ⋮ → Custom repositories** → add `https://github.com/brentb2529/Prolitec`,
   type **Integration**.
2. Find **Prolitec ScenXus** in HACS → **Download** → **Restart Home Assistant**.
3. **Settings → Devices & Services → Add Integration → "Prolitec ScenXus"**.
4. Enter your **email**, **password**, and **device DSN** (shown on the device's
   page at scenxus.com and on the unit — e.g. `AC000W048697889`).

If you later change your ScenXus password, Home Assistant will prompt you to
re-enter it (a reauth dialog) — still no YAML.

## Notes

- Poll interval is 30 s. Writes apply immediately and then re-poll.
- The integration reads/writes the `*_in` (commanded) properties, matching what
  the ScenXus web app shows.
- Unofficial, community integration; not affiliated with Prolitec or Ayla
  Networks.
