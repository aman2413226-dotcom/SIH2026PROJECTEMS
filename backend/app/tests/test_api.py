import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi.testclient import TestClient
from SIH2026PROJECTEMS.backend.app.main import app

client = TestClient(app)


def test_root_and_health():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"

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


def test_dashboard_overview():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert "power_balance" in data
    assert "generation_sources" in data
    assert data["power_balance"]["renewable_fraction_pct"] > 0


def test_diesel_generators():
    response = client.get("/api/v1/diesel/generators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(g["id"] == "GEN-01" for g in data)


def test_emission_stats():
    response = client.get("/api/v1/emission/stats")
    assert response.status_code == 200
    data = response.json()
    assert "co2_emission_rate_kg_per_hour" in data
    assert "particulate_matter" in data


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

    load = client.get("/api/v1/forecast/load")
    assert load.status_code == 200


def test_maintenance_schedules():
    response = client.get("/api/v1/maintenance/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_simulation_scenarios():
    response = client.get("/api/v1/simulation/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_weather_current():
    response = client.get("/api/v1/weather/current")
    assert response.status_code == 200
    data = response.json()
    assert "ambient_temperature_c" in data
    assert "wind_chill_temperature_c" in data


if __name__ == "__main__":
    print("Running automated Polar EMS API verification tests...")
    test_root_and_health()
    print("PASS: Root & Health Check")
    test_battery_status()
    print("PASS: Battery BESS Telemetry")
    test_dashboard_overview()
    print("PASS: Dashboard Power Balance")
    test_diesel_generators()
    print("PASS: Diesel Generators")
    test_emission_stats()
    print("PASS: Emission & Carbon Tracking")
    test_faults_active()
    print("PASS: AI Fault Detection")
    test_forecast_endpoints()
    print("PASS: 24h AI Forecasting (Wind, Solar, Heating Demand)")
    test_maintenance_schedules()
    print("PASS: Predictive Maintenance & Winterization")
    test_simulation_scenarios()
    print("PASS: Digital Twin Simulation Scenarios")
    test_weather_current()
    print("PASS: Polar Meteorology & Wind Chill Sensors")
    print("\nALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!")

