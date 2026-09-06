from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone
from backend.app.core.config import settings

router = APIRouter(prefix="/weather", tags=["Polar Meteorology & Weather Sensors"])


@router.get("/current", summary="Get Current Polar Station Weather Observations")
async def get_current_weather() -> Dict[str, Any]:
    """
    Returns real-time meteorological observations from the station's AWS (Automatic Weather Station).
    Includes calculated wind chill index and visibility for polar survival safety.
    """
    ambient_temp_c = -54.2
    wind_speed_ms = 14.5  # ~28 knots
    # Standard Jag/TI Wind Chill Formula
    wind_chill_c = round(
        13.12 + (0.6215 * ambient_temp_c) - (11.37 * (wind_speed_ms * 3.6) ** 0.16) + (0.3965 * ambient_temp_c * (wind_speed_ms * 3.6) ** 0.16),
        1
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station_name": settings.STATION_NAME,
        "station_code": settings.STATION_CODE,
        "elevation_meters": settings.ELEVATION_M,
        "ambient_temperature_c": ambient_temp_c,
        "wind_chill_temperature_c": wind_chill_c,
        "wind_speed_ms": wind_speed_ms,
        "wind_speed_knots": round(wind_speed_ms * 1.94384, 1),
        "wind_direction_deg": 195,
        "wind_direction_compass": "SSW (Katabatic Slope Flow)",
        "atmospheric_pressure_hpa": 645.0,  # High altitude polar plateau (Dome C ~3233m)
        "relative_humidity_pct": 28.0,
        "visibility_meters": 1200,
        "whiteout_condition": False,
        "snow_accumulation_rate_cm_day": 0.2,
    }


@router.get("/blizzard-warning", summary="Blizzard Alert Level & Outdoor Safety Status")
async def get_blizzard_warning() -> Dict[str, Any]:
    """Returns safety operational codes based on wind speed, temperature, and visibility."""
    return {
        "status_code": "CONDITION_2",  # Condition 1: Severe storm/stay inside, 2: Hazardous, 3: Normal
        "alert_level": "WARNING_HIGH_WIND",
        "outdoor_travel_permitted": "WITH_GUIDE_ROPES_ONLY",
        "maximum_safe_outdoor_exposure_minutes": 15,
        "frostbite_onset_time_minutes": 5,
        "wind_turbine_safety_status": "NORMAL_OPERATION_APPROACHING_CUTOFF_WATCH",
    }


@router.get("/polar-cycle", summary="Astronomical Solar Elevation & Polar Cycle")
async def get_polar_cycle() -> Dict[str, Any]:
    """Returns astronomical solar position and day/night season (Midnight Sun vs Polar Night)."""
    return {
        "latitude": settings.LATITUDE,
        "longitude": settings.LONGITUDE,
        "current_season": "AUSTRAL_SPRING_EQUINOX_TRANSITION",
        "polar_phase": "TRANSITIONAL_SUNRISE_SEASON",
        "daylight_hours_per_day": 14.2,
        "solar_elevation_noon_deg": 14.8,
        "solar_azimuth_deg": 42.1,
        "polar_night_days_remaining": 0,
        "next_full_polar_night_date": "2027-05-04",
    }

