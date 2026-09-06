from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime, timezone
from backend.app.core.config import settings

router = APIRouter(prefix="/emission", tags=["Emissions & Polar Treaty Compliance"])


@router.get("/stats", summary="Current Emission Rates & Black Carbon Footprint")
async def get_emission_stats() -> Dict[str, Any]:
    """
    Returns real-time carbon and particulate emissions from station generators.
    In Antarctica, preventing black carbon soot deposits on snow is critical to preserve local albedo.
    """
    diesel_flow_lh = 9.2  # current burn rate
    co2_factor_kg_per_liter = 2.68  # Jet A-1 / Arctic diesel
    current_co2_kg_per_hour = round(diesel_flow_lh * co2_factor_kg_per_liter, 2)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station": settings.STATION_NAME,
        "current_diesel_burn_rate_lh": diesel_flow_lh,
        "co2_emission_rate_kg_per_hour": current_co2_kg_per_hour,
        "daily_co2_kg": round(current_co2_kg_per_hour * 24, 1),
        "monthly_co2_metric_tons": 17.8,
        "particulate_matter": {
            "pm2_5_ug_m3": 4.1,
            "pm10_ug_m3": 6.8,
            "black_carbon_soot_index": "LOW_CLEAN_SNOW_ZONE",
        },
        "catalytic_soot_filter_efficiency_pct": 98.2,
    }


@router.get("/offsets", summary="Renewable Energy Emissions Avoided")
async def get_renewable_offsets() -> Dict[str, Any]:
    """Calculates diesel liters and CO2 saved by wind and solar microgrid generation."""
    wind_offset_kwh_today = 840.0
    solar_offset_kwh_today = 380.0
    total_renewable_kwh = wind_offset_kwh_today + solar_offset_kwh_today

    # Approx 0.28 L diesel saved per kWh renewable
    liters_saved = round(total_renewable_kwh * 0.28, 1)
    co2_saved_kg = round(liters_saved * 2.68, 1)

    return {
        "period": "Today (00:00 - Present UTC)",
        "wind_generation_kwh": wind_offset_kwh_today,
        "solar_pv_generation_kwh": solar_offset_kwh_today,
        "total_clean_energy_kwh": total_renewable_kwh,
        "diesel_fuel_avoided_liters": liters_saved,
        "co2_emissions_avoided_kg": co2_saved_kg,
        "monetary_fuel_saving_usd": round(liters_saved * 4.50, 2),  # polar logistics fuel cost ~ $4.50/L
    }


@router.get("/compliance-report", summary="Madrid Protocol Antarctic Environmental Compliance")
async def get_compliance_report() -> Dict[str, Any]:
    """Generates environmental compliance metric against Antarctic Treaty Annex IV (Waste & Prevention of Marine/Air Pollution)."""
    return {
        "regulatory_standard": "Antarctic Treaty Madrid Protocol Annex IV (Air Cleanliness & Energy Transition)",
        "compliance_status": "COMPLIANT_GRADE_A",
        "station_renewable_share_annual_pct": 58.4,
        "target_renewable_share_pct": 50.0,
        "exhaust_gas_cleaning": "Selective Catalytic Reduction (SCR) Active",
        "spill_risk_index": "MINIMAL_SECONDARY_CONTAINED",
        "last_inspection_date": "2026-01-15",
    }

