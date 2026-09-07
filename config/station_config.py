"""
PolarEMS Station Configurations
Configuration profiles for Indian Antarctic Research Stations (Maitri & Bharati).
"""

from typing import Dict, Any

STATION_CONFIGS: Dict[str, Dict[str, Any]] = {
    "MAITRI": {
        "station_code": "MAITRI-ANTARCTICA",
        "station_name": "Maitri Antarctic Research Station",
        "operator": "National Centre for Polar and Ocean Research (NCPOR), India",
        "region": "Schirmacher Oasis, Queen Maud Land, East Antarctica",
        "latitude": -70.7667,
        "longitude": 11.7333,
        "elevation_m": 117.0,
        "commissioned_year": 1989,
        "wintering_crew_capacity": 25,
        "summer_crew_capacity": 65,
        "grid_specs": {
            "nominal_voltage_v": 400.0,
            "nominal_frequency_hz": 50.0,
            "base_electrical_load_kw": 48.0,
            "peak_station_load_kw": 140.0,
            "thermal_conductance_kw_per_c": 0.62,  # Habitat heat loss coefficient per deg subzero
            "target_indoor_temp_c": 21.0,
            "solar_pv_capacity_kw": 80.0,
            "solar_tilt_deg": 65.0,  # Optimized for polar low-angle insolation
            "bifacial_albedo_factor": 1.25,  # Snow reflection gain
            "wind_turbine_capacity_kw": 120.0,  # 2 x 60 kW cold-climate polar turbines
            "wind_cut_in_ms": 3.0,
            "wind_rated_ms": 12.0,
            "wind_cut_out_ms": 25.0,
            "bess_capacity_kwh": 500.0,
            "bess_nominal_charge_kw": 100.0,
            "bess_nominal_discharge_kw": 100.0,
            "bess_min_soc_pct": 20.0,
            "bess_critical_reserve_pct": 15.0,
            "diesel_genset_count": 3,
            "diesel_genset_rated_kw": 80.0,  # Kirloskar / Cummins polar spec gensets
            "diesel_fuel_tank_liters": 50000.0,
            "fuel_consumption_rate_l_per_kwh": 0.28,
            "genset_idle_fuel_rate_l_per_h": 2.8,
            "genset_startup_seconds": 120,
            "genset_min_runtime_hours": 3.0,
        }
    },
    "BHARATI": {
        "station_code": "BHARATI-ANTARCTICA",
        "station_name": "Bharati Antarctic Research Station",
        "operator": "National Centre for Polar and Ocean Research (NCPOR), India",
        "region": "Larsemann Hills, East Antarctica",
        "latitude": -69.4072,
        "longitude": 76.1872,
        "elevation_m": 35.0,
        "commissioned_year": 2012,
        "wintering_crew_capacity": 25,
        "summer_crew_capacity": 72,
        "grid_specs": {
            "nominal_voltage_v": 400.0,
            "nominal_frequency_hz": 50.0,
            "base_electrical_load_kw": 55.0,
            "peak_station_load_kw": 160.0,
            "thermal_conductance_kw_per_c": 0.58,  # Modern modular containerized insulation
            "target_indoor_temp_c": 21.0,
            "solar_pv_capacity_kw": 100.0,
            "solar_tilt_deg": 60.0,
            "bifacial_albedo_factor": 1.28,
            "wind_turbine_capacity_kw": 150.0,
            "wind_cut_in_ms": 3.0,
            "wind_rated_ms": 12.5,
            "wind_cut_out_ms": 25.0,
            "bess_capacity_kwh": 600.0,
            "bess_nominal_charge_kw": 120.0,
            "bess_nominal_discharge_kw": 120.0,
            "bess_min_soc_pct": 20.0,
            "bess_critical_reserve_pct": 15.0,
            "diesel_genset_count": 3,
            "diesel_genset_rated_kw": 100.0,
            "diesel_fuel_tank_liters": 60000.0,
            "fuel_consumption_rate_l_per_kwh": 0.27,
            "genset_idle_fuel_rate_l_per_h": 3.2,
            "genset_startup_seconds": 120,
            "genset_min_runtime_hours": 3.0,
        }
    }
}

DEFAULT_STATION = "MAITRI"


def get_station_config(station_key: str = DEFAULT_STATION) -> Dict[str, Any]:
    key = station_key.upper().strip()
    if key in STATION_CONFIGS:
        return STATION_CONFIGS[key]
    return STATION_CONFIGS[DEFAULT_STATION]
