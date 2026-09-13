"""ha_solarflow_energy, live SolarFlow / Zendure AIO snapshot via HA Core.

Reads the power entities you've configured for your SolarFlow or AIO
inverter through Home Assistant Core's shared connection. Produces a
structured shape the widget variants paint:

    {
      "place": str,
      "time": str,
      "pv_w": float,
      "home_w": float,
      "grid_w": float,
      "battery_w": float,      # + = discharging, - = charging
      "battery_soc": float|None,
      "pv_today_kwh": float|None,
      "forecast_today_kwh": float|None,
      "forecast_tomorrow_kwh": float|None,
      "sparkline": [float, ...]
    }

The sparkline uses the solar entity if configured, else the house entity.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from flask import current_app


def _core() -> Any:
    core_plugin = current_app.config["PLUGIN_REGISTRY"].get("ha_core")
    if core_plugin is None:
        return None
    return core_plugin.server_module


def choices(name: str) -> list[dict[str, str]]:
    """Entity picker dropdowns powered by HA Core."""
    core = _core()
    if core is None:
        return [{"value": "", "label": "Home Assistant Core plugin is not installed"}]
    if name == "entity":
        return core.entity_choices(domains=("sensor",))
    return []


def _f(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _f_or_none(value: Any) -> float | None:
    if value in (None, "", "unavailable", "unknown"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _state(states: list[dict[str, Any]], entity_id: str) -> dict[str, Any] | None:
    for st in states:
        if st.get("entity_id") == entity_id:
            return st
    return None


def _state_w(states: list[dict[str, Any]], entity_id: str) -> float:
    if not entity_id:
        return 0.0
    st = _state(states, entity_id)
    if st is None:
        return 0.0
    value = _f(st.get("state"))
    unit = str((st.get("attributes") or {}).get("unit_of_measurement", "")).lower()
    if unit == "kw":
        value *= 1000
    return value


def _downsample(values: list[float], *, slots: int) -> list[float]:
    if not values or slots < 1:
        return []
    n = len(values)
    if n <= slots:
        return [round(v, 1) for v in values]
    out: list[float] = []
    step = n / slots
    for i in range(slots):
        lo = int(i * step)
        hi = int((i + 1) * step) or lo + 1
        bucket = values[lo:hi] or [0.0]
        out.append(round(sum(bucket) / len(bucket), 1))
    return out


def fetch(
    options: dict[str, Any], settings: dict[str, Any], *, ctx: dict[str, Any]
) -> dict[str, Any]:
    del settings, ctx
    core = _core()
    if core is None:
        return {"error": "Home Assistant Core plugin is not installed"}

    try:
        states = core.get_states()
    except Exception as err:
        return {"error": core.coerce_error(err)}

    pv = _state_w(states, options.get("solar_entity") or "")
    home = _state_w(states, options.get("home_entity") or "")
    grid = _state_w(states, options.get("grid_entity") or "")
    pack_charge = _state_w(states, options.get("battery_charge_entity") or "")
    pack_discharge = _state_w(states, options.get("battery_discharge_entity") or "")

    # battery_w: positive = discharging, negative = charging
    battery = pack_discharge - pack_charge

    soc_entity = (options.get("battery_soc_entity") or "").strip()
    soc = None
    if soc_entity:
        soc_st = _state(states, soc_entity)
        if soc_st is not None:
            soc = _f_or_none(soc_st.get("state"))

    # Forecast totals (optional)
    forecast_today_kwh = None
    forecast_tomorrow_kwh = None
    fc_today_entity = (options.get("forecast_today_entity") or "").strip()
    fc_tomorrow_entity = (options.get("forecast_tomorrow_entity") or "").strip()
    if fc_today_entity:
        fc_st = _state(states, fc_today_entity)
        if fc_st is not None:
            forecast_today_kwh = _f_or_none(fc_st.get("state"))
    if fc_tomorrow_entity:
        fc_st = _state(states, fc_tomorrow_entity)
        if fc_st is not None:
            forecast_tomorrow_kwh = _f_or_none(fc_st.get("state"))

    # Sparkline: prefer solar, fall back to house
    spark_entity = (options.get("solar_entity") or options.get("home_entity") or "").strip()
    sparkline: list[float] = []
    if spark_entity:
        try:
            hist = core.history(spark_entity, hours=24)
            sparkline = _downsample([_f(s.get("state")) for s in hist], slots=48)
        except Exception:
            sparkline = []

    return {
        "place": options.get("label", "Home"),
        "time": datetime.now().strftime("%H:%M"),
        "pv_w": round(pv, 1),
        "home_w": round(home, 1),
        "grid_w": round(grid, 1),
        "battery_w": round(battery, 1),
        "battery_soc": round(soc, 1) if soc is not None else None,
        "pv_today_kwh": None,
        "forecast_today_kwh": round(forecast_today_kwh, 2) if forecast_today_kwh is not None else None,
        "forecast_tomorrow_kwh": round(forecast_tomorrow_kwh, 2) if forecast_tomorrow_kwh is not None else None,
        "sparkline": sparkline,
        "_fetched_at": int(time.time()),
    }
