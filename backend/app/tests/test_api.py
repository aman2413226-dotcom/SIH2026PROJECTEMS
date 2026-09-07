"""
Automated Verification Suite for PolarEMS API & Digital Twin Engine
Tests all 10 domain routers, AI forecast models, Security IDS, and Simulation Controls.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_and_health():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "available_modules" in data
    assert "security" in data["available_modules"]

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_battery_status():
    response = client.get("/api/v1/battery/status")
    assert response.status_code == 200
    data = response.json()
    assert "state_of_charge_pct" in data
    assert "internal_cell_temp_c" in data
    assert "thermal_heater_status" in data
    assert "effective_capacity_kwh" in data


def test_dashboard_overview_and_power_flow():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert "power_balance" in data
    assert "generation_sources" in data
    assert "autonomy" in data

    # Test interactive power flow map endpoint
    pf = client.get("/api/v1/dashboard/power-flow")
    assert pf.status_code == 200
    pf_data = pf.json()
    assert "nodes" in pf_data
    assert "flows" in pf_data
    assert "solar" in pf_data["nodes"]
    assert "wind" in pf_data["nodes"]
    assert "bess" in pf_data["nodes"]


def test_diesel_generators():
    response = client.get("/api/v1/diesel/generators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(g["id"] == "GEN-01" for g in data)

    reserve = client.get("/api/v1/diesel/fuel-reserve")
    assert reserve.status_code == 200
    assert "current_stock_liters" in reserve.json()


def test_emission_stats():
    response = client.get("/api/v1/emission/stats")
    assert response.status_code == 200
    data = response.json()
    assert "co2_emission_rate_kg_per_hour" in data

    offsets = client.get("/api/v1/emission/offsets")
    assert offsets.status_code == 200
    assert "diesel_fuel_avoided_liters" in offsets.json()


def test_faults_active():
    response = client.get("/api/v1/faults/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_forecast_endpoints():
    wind = client.get("/api/v1/forecast/wind")
    assert wind.status_code == 200
    assert len(wind.json()["forecast"]) == 24

    solar = client.get("/api/v1/forecast/solar")
    assert solar.status_code == 200
    assert len(solar.json()["forecast"]) == 24

    load = client.get("/api/v1/forecast/load")
    assert load.status_code == 200
    assert len(load.json()["forecast"]) == 24
    assert load.json()["training_days"] == 730

    dispatch = client.get("/api/v1/forecast/optimal-dispatch-schedule")
    assert dispatch.status_code == 200
    assert len(dispatch.json()["hourly_schedule"]) == 24
    assert "expected_24h_fuel_liters" in dispatch.json()

    info = client.get("/api/v1/forecast/model-info")
    assert info.status_code == 200
    assert "LightGBM" in info.json()["model_architecture"]


def test_maintenance_schedules():
    response = client.get("/api/v1/maintenance/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_simulation_controls():
    # Test status
    status_res = client.get("/api/v1/simulation/status")
    assert status_res.status_code == 200
    assert "sim_time" in status_res.json()

    # Test step
    step_res = client.post("/api/v1/simulation/step", json={"seconds": 60})
    assert step_res.status_code == 200
    assert step_res.json()["status"] == "STEP_COMPLETED"

    # Test speed multiplier
    speed_res = client.post("/api/v1/simulation/speed", json={"multiplier": 10})
    assert speed_res.status_code == 200
    assert speed_res.json()["speed_multiplier"] == 10

    # Test pause and play
    pause_res = client.post("/api/v1/simulation/pause")
    assert pause_res.status_code == 200
    play_res = client.post("/api/v1/simulation/play")
    assert play_res.status_code == 200

    # Test fault injection
    fault_res = client.post("/api/v1/simulation/fault/inject", json={"fault_type": "BLIZZARD"})
    assert fault_res.status_code == 200
    assert fault_res.json()["status"] == "FAULT_INJECTED"
    fault_id = fault_res.json()["fault"]["fault_id"]

    # Clear fault
    clear_res = client.post(f"/api/v1/simulation/fault/clear/{fault_id}")
    assert clear_res.status_code == 200


def test_weather_and_stations():
    stations_res = client.get("/api/v1/weather/stations")
    assert stations_res.status_code == 200
    stations = stations_res.json()
    assert any(s["key"] == "MAITRI" for s in stations)
    assert any(s["key"] == "BHARATI" for s in stations)

    current_res = client.get("/api/v1/weather/current")
    assert current_res.status_code == 200
    data = current_res.json()
    assert "ambient_temperature_c" in data
    assert "wind_chill_temperature_c" in data

    cycle = client.get("/api/v1/weather/polar-cycle")
    assert cycle.status_code == 200
    assert "polar_phase" in cycle.json()


def test_security_ids_and_red_team():
    # 1. Check initial posture
    status_res = client.get("/api/v1/security/status")
    assert status_res.status_code == 200
    initial_posture = status_res.json()["posture"]
    assert initial_posture in ["SECURE", "WARNING", "COMPROMISED"]

    # 2. Red Team Attack: Load Hijacking
    attack_res = client.post("/api/v1/security/attack/load-hijack", json={"surge_kw": 95.0})
    assert attack_res.status_code == 200
    attack_data = attack_res.json()
    assert attack_data["posture"] == "COMPROMISED"
    assert "Injected 95.0 kW" in attack_data["action"]

    # 3. Verify posture updated
    status_after = client.get("/api/v1/security/status")
    assert status_after.json()["posture"] == "COMPROMISED"
    assert status_after.json()["active_threats_count"] >= 1

    # 4. Reset Posture
    reset_res = client.post("/api/v1/security/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "SUCCESS"
    assert reset_res.json()["security_details"]["posture"] == "SECURE"


if __name__ == "__main__":
    print("Running comprehensive automated Polar EMS API verification suite...")
    test_root_and_health()
    print("PASS: 1. Root & Health Check")
    test_battery_status()
    print("PASS: 2. Battery BESS Telemetry & Cold Derating")
    test_dashboard_overview_and_power_flow()
    print("PASS: 3. Dashboard Overview & Interactive Power Flow Map")
    test_diesel_generators()
    print("PASS: 4. Diesel Powerplant & Fuel Reserves")
    test_emission_stats()
    print("PASS: 5. Emission Rates & Renewable Offsets")
    test_faults_active()
    print("PASS: 6. Active Physical Fault Diagnostics")
    test_forecast_endpoints()
    print("PASS: 7. 24h AI Forecasting (LightGBM 730-day model & Optimal Dispatch)")
    test_maintenance_schedules()
    print("PASS: 8. Predictive Maintenance & Winterization")
    test_simulation_controls()
    print("PASS: 9. Digital Twin Simulation Controls (Play/Pause/Step/Speed/Faults)")
    test_weather_and_stations()
    print("PASS: 10. NCPOR Antarctic Weather & Station Switching (Maitri/Bharati)")
    test_security_ids_and_red_team()
    print("PASS: 11. Cyber-Physical Security IDS & Red Team Attack Simulation")
    print("\nALL 11 MISSION-CRITICAL API MODULES PASSED SUCCESSFULLY!")
