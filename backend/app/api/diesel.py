"""
PolarEMS Diesel Generator Dispatch & Fuel Reserves Router
Real-time genset dispatch status, fuel reserve tracking, and cold-weather block heating.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin
from backend.app.core.config import settings
from backend.app.core.security import verify_api_key

router = APIRouter(prefix="/diesel", tags=["Diesel Generator Dispatch & Reserves"])


class GensetControlRequest(BaseModel):
    action: str = Field(..., description="START, STOP, PRE_HEAT")
    target_kw: float = Field(default=40.0, ge=0.0, le=100.0)


@router.get("/generators", summary="Get Telemetry for All Station Diesel Gensets")
async def get_diesel_generators() -> List[Dict[str, Any]]:
    """Returns telemetry for all generators in the polar power station from Digital Twin."""
    gensets = digital_twin.diesel.gensets
    result = []
    for g in gensets:
        output_kw = g.get("output_kw", 0.0)
        burn_lh = round(output_kw * 0.28 + (2.8 if output_kw > 0 else 0.0), 2)
        result.append({
            "id": g["id"],
            "name": g["name"],
            "status": "RUNNING" if output_kw > 0 else g["status"],
            "power_output_kw": output_kw,
            "rated_capacity_kw": digital_twin.diesel.rated_kw,
            "fuel_consumption_rate_lh": burn_lh,
            "engine_block_temp_c": g.get("coolant_temp_c", 82.0),
            "coolant_temp_c": g.get("coolant_temp_c", 82.0),
            "total_run_hours": round(g.get("runtime_hours", 3000.0), 1),
            "service_due_hours": round(g.get("maintenance_due_hours", 250.0), 1),
            "pre_heater_active": g.get("status") in ["STANDBY", "WARMING_UP"],
        })
    return result


@router.post("/generators/{genset_id}/control", summary="Manual Operator Control of Diesel Genset")
async def control_generator(
    genset_id: str,
    payload: GensetControlRequest,
) -> Dict[str, Any]:
    """Manually start, stop, or preheat a polar diesel generator."""
    target_genset = None
    for g in digital_twin.diesel.gensets:
        if g["id"] == genset_id:
            target_genset = g
            break

    if not target_genset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Genset {genset_id} not found.")

    if payload.action == "START":
        target_genset["status"] = "ONLINE"
        target_genset["output_kw"] = payload.target_kw
    elif payload.action == "STOP":
        target_genset["status"] = "STANDBY"
        target_genset["output_kw"] = 0.0
    elif payload.action == "PRE_HEAT":
        target_genset["status"] = "WARMING_UP"
        target_genset["startup_timer_s"] = 120.0

    digital_twin.tick(seconds=1)

    return {
        "status": "success",
        "genset_id": genset_id,
        "new_status": target_genset["status"],
        "message": f"Command {payload.action} executed for {genset_id}.",
    }


@router.get("/fuel-reserve", summary="Polar Diesel Fuel Inventory & Endurance Projection")
async def get_fuel_reserve() -> Dict[str, Any]:
    """Returns total fuel remaining, daily burn rate, and endurance until next resupply voyage."""
    telemetry = digital_twin.latest_telemetry
    diesel = telemetry.get("diesel", {})
    remaining = diesel.get("fuel_remaining_liters", 45000.0)
    capacity = digital_twin.diesel.tank_capacity_liters
    ratio_pct = round((remaining / capacity) * 100.0, 1)

    burn_lh = diesel.get("fuel_burn_rate_l_per_h", 8.5)
    daily_burn = max(50.0, round(burn_lh * 24.0, 1))
    days_endurance = round(remaining / daily_burn, 1)

    return {
        "timestamp": telemetry.get("timestamp"),
        "station_code": digital_twin.config["station_code"],
        "total_capacity_liters": capacity,
        "current_stock_liters": round(remaining, 1),
        "fill_percentage": ratio_pct,
        "fuel_type": "Polar Grade Aviation Kerosene (F-34 / Jet A-1 with Anti-Gel Additives)",
        "daily_burn_rate_liters": daily_burn,
        "days_endurance_remaining": days_endurance,
        "is_critical_reserve": ratio_pct < 20.0,
        "annual_resupply_window": "AUSTRAL_SUMMER_DECEMBER_FEBRUARY",
    }
