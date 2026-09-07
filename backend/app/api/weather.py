"""
PolarEMS Weather & Meteorology API Router
Provides real-time observations from NCPOR, Antarctic weather station switching, and polar cycle telemetry.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin
from backend.app.services.ncpor_service import ncpor_service
from config.station_config import STATION_CONFIGS

router = APIRouter(prefix="/weather", tags=["Polar Meteorology & Weather Sensors"])


class StationSwitchRequest(BaseModel):
    station: str = Field(..., description="MAITRI or BHARATI")


@router.get("/current", summary="Get Current Polar Station Weather Observations")
async def get_current_weather(
    station: str = Query(default="", description="Optional station filter: MAITRI or BHARATI")
) -> Dict[str, Any]:
    """
    Returns real-time meteorological observations from NCPOR feeds or Digital Twin AWS.
    Includes calculated wind chill index and visibility for polar survival safety.
    """
    target_station = station.upper() if station else digital_twin.station_key
    ncpor_data = await ncpor_service.fetch_live_weather(target_station)

    # Sync latest temperature & wind into digital twin if this is active station
    if target_station == digital_twin.station_key:
        ncpor_service.sync_to_digital_twin(digital_twin, target_station)

    return ncpor_data


@router.get("/stations", summary="List Available Indian Antarctic Research Stations")
async def list_stations() -> List[Dict[str, Any]]:
    """Lists supported Indian Antarctic stations (Maitri & Bharati) and their coordinates."""
    stations = []
    for key, cfg in STATION_CONFIGS.items():
        stations.append({
            "key": key,
            "station_name": cfg["station_name"],
            "station_code": cfg["station_code"],
            "region": cfg["region"],
            "latitude": cfg["latitude"],
            "longitude": cfg["longitude"],
            "elevation_m": cfg["elevation_m"],
            "is_active": (key == digital_twin.station_key),
        })
    return stations


@router.post("/switch-station", summary="Switch Active Antarctic Station")
async def switch_station(payload: StationSwitchRequest) -> Dict[str, Any]:
    """Switches the active microgrid and meteorology profile to Maitri or Bharati."""
    key = payload.station.upper().strip()
    if key not in STATION_CONFIGS:
        return {"status": "ERROR", "message": f"Station {key} not found. Choose MAITRI or BHARATI."}

    digital_twin.set_station(key)
    await ncpor_service.fetch_live_weather(key)
    ncpor_service.sync_to_digital_twin(digital_twin, key)

    return {
        "status": "SUCCESS",
        "active_station": digital_twin.config["station_name"],
        "station_code": digital_twin.config["station_code"],
        "message": f"Successfully switched active station to {digital_twin.config['station_name']}.",
    }


@router.get("/blizzard-warning", summary="Blizzard Alert Level & Outdoor Safety Status")
async def get_blizzard_warning() -> Dict[str, Any]:
    """Returns safety operational codes based on wind speed, temperature, and visibility."""
    wind_speed = digital_twin.wind_speed_ms
    wind_chill = digital_twin.latest_telemetry.get("environment", {}).get("wind_chill_c", -60.0)

    if wind_speed >= 25.0 or wind_chill <= -60.0:
        code = "CONDITION_1"
        alert = "CRITICAL_BLIZZARD_ALERT"
        travel = "FORBIDDEN - ALL PERSONNEL MUST REMAIN INDOORS"
        exposure = 3
    elif wind_speed >= 15.0 or wind_chill <= -40.0:
        code = "CONDITION_2"
        alert = "WARNING_HIGH_WIND"
        travel = "WITH_GUIDE_ROPES_AND_BUDDY_ONLY"
        exposure = 15
    else:
        code = "CONDITION_3"
        alert = "NORMAL_POLAR_MONITOR"
        travel = "PERMITTED_STATION_PERIMETER"
        exposure = 45

    return {
        "status_code": code,
        "alert_level": alert,
        "outdoor_travel_permitted": travel,
        "maximum_safe_outdoor_exposure_minutes": exposure,
        "frostbite_onset_time_minutes": 5 if wind_chill < -50 else 15,
        "wind_turbine_safety_status": "STORM_CUTOFF_ACTIVE" if wind_speed >= 25.0 else "NORMAL_OPERATION",
    }


@router.get("/polar-cycle", summary="Astronomical Solar Elevation & Polar Cycle")
async def get_polar_cycle() -> Dict[str, Any]:
    """Returns astronomical solar position and day/night season (Midnight Sun vs Polar Night)."""
    now = digital_twin.sim_time
    doy = now.timetuple().tm_yday

    if doy <= 45 or doy >= 315:
        season = "AUSTRAL_SUMMER_MIDNIGHT_SUN"
        phase = "24H_CONTINUOUS_SOLAR_INSOLATION"
        daylight_hours = 24.0
    elif 125 <= doy <= 225:
        season = "AUSTRAL_WINTER_POLAR_NIGHT"
        phase = "CONTINUOUS_POLAR_NIGHT"
        daylight_hours = 0.0
    else:
        season = "TRANSITIONAL_EQUINOX_SEASON"
        phase = "DIURNAL_SUNRISE_SUNSET_CYCLE"
        daylight_hours = 14.2

    solar_elev = digital_twin.latest_telemetry.get("environment", {}).get("solar_elevation_deg", 12.0)

    return {
        "latitude": digital_twin.config["latitude"],
        "longitude": digital_twin.config["longitude"],
        "current_season": season,
        "polar_phase": phase,
        "day_of_year": doy,
        "daylight_hours_per_day": daylight_hours,
        "solar_elevation_deg": solar_elev,
        "polar_night_active": daylight_hours == 0.0,
    }
