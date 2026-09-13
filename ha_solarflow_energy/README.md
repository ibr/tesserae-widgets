# HA SolarFlow Energy

A [Tesserae](https://tesserae.ink) widget for **SolarFlow 2400 Pro** and other **Zendure AIO** inverters via Home Assistant.

Shows live PV production, house consumption, battery SOC/power, grid usage — plus an optional 24h sparkline and PV forecast totals from Forecast.Solar.

## Requirements

- **Tesserae Home Assistant Core** plugin (`ha_core`) must be installed and configured (URL + Long-Lived Access Token)
- Home Assistant with SolarFlow / Zendure integration active
- Optional: [Forecast.Solar](https://www.home-assistant.io/integrations/forecast_solar/) for tomorrow's yield

## Install

```bash
# In your Tesserae checkout
cp -r /path/to/ha_solarflow_energy plugins/
# Restart Tesserae
```

Or via the catalog: **Settings → Widgets → Browse catalog → HA SolarFlow Energy**

## Configuration

Each cell lets you pick entities via dropdowns (powered by the shared HA connection):

| Entity slot | Suggested value | What it reads |
|---|---|---|
| Solar power | `sensor.solarflow_2400_pro_solar_input_power` | PV production (W) |
| House power | `sensor.solarflow_2400_pro_output_home_power` | House consumption (W) |
| Grid power | `sensor.solarflow_2400_pro_grid_input_power` | Grid import (W) |
| Battery charge power | `sensor.solarflow_2400_pro_output_pack_power` | Battery charge (W) |
| Battery discharge power | `sensor.solarflow_2400_pro_pack_input_power` | Battery discharge (W) |
| Battery SoC | `sensor.solarflow_2400_pro_electric_level` | Battery % |
| PV forecast today | `sensor.energy_production_today` | Today's yield (kWh) — optional |
| PV forecast tomorrow | `sensor.energy_production_tomorrow` | Tomorrow's yield (kWh) — optional |

### Battery power calculation

The widget computes battery net power internally:

- **Negative** = charging (e.g. -200 W)
- **Positive** = discharging / feeding the house (e.g. 350 W)

This matches how SolarFlow/Zendure reports pack charge vs. pack discharge as separate sensors.

### AIO 2400 users

If your entities use the `aio_2400` prefix instead of `solarflow_2400_pro`, pick the corresponding `sensor.aio_2400_*` entities from the dropdowns.

## Variants

- **Full card** — sparkline + stats + forecast footer
- **Stats only** — compact view without sparkline/forecast

## Layout

- Left: 24-hour sparkline of the selected solar (or house) power entity
- Right: Live stats — PV, house, battery, grid
- Footer: PV forecast today + tomorrow (from Forecast.Solar if configured)

## Development

```sh
# Tesserae checkout
.venv/bin/python -m pytest plugins/ha_solarflow_energy/tests -q
```

Preview: `/_test/render?plugin=ha_solarflow_energy&size=lg`

## Notes

- This widget relies on the shared **Home Assistant Core** plugin (`ha_core`) for all entity state fetching. No URL or token is configured per-widget.
- If you see "Home Assistant Core Plugin not installed", make sure `ha_core` is installed and has a valid URL + token.

Adapted from [fbaeumer/tesserae-evcc-energy](https://github.com/fbaeumer/tesserae-evcc-energy).

## License

[AGPL-3.0-or-later](LICENSE), same as Tesserae.
