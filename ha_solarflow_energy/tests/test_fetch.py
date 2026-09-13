"""ha_solarflow_energy fetch() smoke: mocked HA states via ha_core."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


_HA_STATES = [
    {"entity_id": "sensor.solarflow_2400_pro_solar_input_power", "state": "1200"},
    {"entity_id": "sensor.solarflow_2400_pro_output_home_power", "state": "400"},
    {"entity_id": "sensor.solarflow_2400_pro_grid_input_power", "state": "0"},
    {"entity_id": "sensor.solarflow_2400_pro_electric_level", "state": "80"},
    {"entity_id": "sensor.solarflow_2400_pro_output_pack_power", "state": "200"},
    {"entity_id": "sensor.solarflow_2400_pro_pack_input_power", "state": "0"},
    {"entity_id": "sensor.energy_production_today", "state": "5.5"},
    {"entity_id": "sensor.energy_production_tomorrow", "state": "7.2"},
]


def _mock_core():
    core = MagicMock()
    core.get_states.return_value = _HA_STATES
    core.coerce_error = lambda e: str(e)
    core.history.return_value = [
        {"state": "0"}, {"state": "100"}, {"state": "500"}, {"state": "1200"}
    ]
    return core


def test_fetch_full(monkeypatch):
    from plugins.ha_solarflow_energy import server as sf

    mock_registry = {"ha_core": MagicMock(server_module=_mock_core())}
    monkeypatch.setitem(
        sf.current_app.config["PLUGIN_REGISTRY"], "ha_core", mock_registry["ha_core"]
    )

    out = sf.fetch(
        {
            "solar_entity": "sensor.solarflow_2400_pro_solar_input_power",
            "home_entity": "sensor.solarflow_2400_pro_output_home_power",
            "grid_entity": "sensor.solarflow_2400_pro_grid_input_power",
            "battery_charge_entity": "sensor.solarflow_2400_pro_output_pack_power",
            "battery_discharge_entity": "sensor.solarflow_2400_pro_pack_input_power",
            "battery_soc_entity": "sensor.solarflow_2400_pro_electric_level",
            "forecast_today_entity": "sensor.energy_production_today",
            "forecast_tomorrow_entity": "sensor.energy_production_tomorrow",
            "label": "Balkon",
        },
        {},
        ctx={},
    )
    assert "error" not in out
    assert out["pv_w"] == 1200
    assert out["home_w"] == 400
    assert out["grid_w"] == 0
    assert out["battery_soc"] == 80
    # Charging: pack_charge=200, pack_discharge=0 → battery_w = -200
    assert out["battery_w"] == -200
    assert out["forecast_today_kwh"] == 5.5
    assert out["forecast_tomorrow_kwh"] == 7.2
    assert out["place"] == "Balkon"
    assert out["sparkline"]


def test_fetch_discharging(monkeypatch):
    from plugins.ha_solarflow_energy import server as sf

    states = [
        {"entity_id": "sensor.solarflow_2400_pro_output_pack_power", "state": "0"},
        {"entity_id": "sensor.solarflow_2400_pro_pack_input_power", "state": "350"},
    ]
    core = _mock_core()
    core.get_states.return_value = states
    mock_registry = {"ha_core": MagicMock(server_module=core)}
    monkeypatch.setitem(
        sf.current_app.config["PLUGIN_REGISTRY"], "ha_core", mock_registry["ha_core"]
    )

    out = sf.fetch(
        {
            "battery_charge_entity": "sensor.solarflow_2400_pro_output_pack_power",
            "battery_discharge_entity": "sensor.solarflow_2400_pro_pack_input_power",
        },
        {},
        ctx={},
    )
    # Discharging: pack_charge=0, pack_discharge=350 → battery_w = 350
    assert out["battery_w"] == 350


def test_no_ha_core(monkeypatch):
    from plugins.ha_solarflow_energy import server as sf

    monkeypatch.setitem(sf.current_app.config["PLUGIN_REGISTRY"], "ha_core", None)
    out = sf.fetch({}, {}, ctx={})
    assert out.get("error") == "Home Assistant Core plugin is not installed"
