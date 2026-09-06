from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone
from SIH2026PROJECTEMS.backend.app.core.config import settings

router = APIRouter(prefix="/dashboard", tags=["Station Energy Dashboard"])


@router.get("/overview", summary="Real-Time Station Energy Balance & Status")
async def get_dashboard_overview() -> Dict[str, Any]:
    """
    Returns real-time aggregated microgrid energy balance for the Polar Research Station:
    Wind (kW) + Solar (kW) + Diesel (kW) = Station Load (kW) + Battery (kW)
    """
    wind_kw = 54.2
    solar_kw = 22.0  # Summer polar day or partial insolation
    diesel_kw = 35.0
    total_generation_kw = wind_kw + solar_kw + diesel_kw

    life_support_kw = 42.0
    science_lab_kw = 28.5
    heat_tracing_cables_kw = 18.0
    battery_charging_kw = 22.7  # surplus being stored
    total_load_kw = life_support_kw + science_lab_kw + heat_tracing_cables_kw + battery_charging_kw

    renewable_generation_kw = wind_kw + solar_kw
    renewable_fraction_pct = round((renewable_generation_kw / total_generation_kw) * 100, 1)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station_name": settings.STATION_NAME,
        "station_code": settings.STATION_CODE,
        "station_mode": "NORMAL_RESEARCH",
        "ambient_temperature_c": -54.2,
        "power_balance": {
            "total_generation_kw": round(total_generation_kw, 1),
            "total_load_kw": round(total_load_kw, 1),
            "net_surplus_kw": round(total_generation_kw - total_load_kw, 1),
            "renewable_fraction_pct": renewable_fraction_pct,
        },
        "generation_sources": {
            "wind_turbines_kw": wind_kw,
            "solar_pv_kw": solar_kw,
            "diesel_generators_kw": diesel_kw,
        },
        "consumption_breakdown": {
            "life_support_heating_kw": life_support_kw,
            "science_laboratories_kw": science_lab_kw,
            "external_pipe_heat_tracing_kw": heat_tracing_cables_kw,
            "battery_storage_draw_kw": battery_charging_kw,
        },
        "autonomy": {
            "fuel_reserve_liters": 48200,
            "projected_fuel_days": 68.5,
            "battery_soc_pct": 75.0,
            "battery_backup_hours": 7.5,
        },
        "critical_indicators": {
            "grid_frequency_hz": 50.02,
            "grid_voltage_v": 400.1,
            "power_factor": 0.98,
            "ice_accumulation_warning": False,
        }
    }


@router.get("/kpi", summary="Key Performance Indicators (Last 24 Hours)")
async def get_dashboard_kpi() -> Dict[str, Any]:
    """Provides key performance indices for polar microgrid efficiency and sustainability."""
    return {
        "period": "Last 24 Hours",
        "total_energy_consumed_kwh": 2420.5,
        "renewable_energy_generated_kwh": 1680.0,
        "diesel_energy_generated_kwh": 740.5,
        "renewable_penetration_average_pct": 69.4,
        "diesel_fuel_consumed_liters": 185.2,
        "diesel_fuel_saved_by_renewables_liters": 420.0,
        "co2_emissions_avoided_kg": 1125.6,
        "peak_station_demand_kw": 112.4,
        "min_station_demand_kw": 68.2,
    }

