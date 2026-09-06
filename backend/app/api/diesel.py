from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone
from SIH2026PROJECTEMS.backend.app.core.config import settings
from SIH2026PROJECTEMS.backend.app.core.security import verify_api_key

router = APIRouter(prefix="/diesel", tags=["Diesel Generator Dispatch & Reserves"])

# In-memory polar diesel genset state
_gensets = {
    "GEN-01": {
        "id": "GEN-01",
        "name": "Primary Polar Genset 1 (Caterpillar 3406 Cold-Spec)",
        "status": "RUNNING",  # RUNNING, STANDBY_HOT, STANDBY_COLD, MAINTENANCE
        "power_output_kw": 35.0,
        "rated_capacity_kw": 80.0,
        "fuel_consumption_rate_lh": 9.2,
        "engine_block_temp_c": 78.4,
        "oil_pressure_bar": 4.2,
        "coolant_temp_c": 82.0,
        "total_run_hours": 3412.5,
        "pre_heater_active": False,
    },
    "GEN-02": {
        "id": "GEN-02",
        "name": "Secondary Polar Genset 2 (Backup Synchronous)",
        "status": "STANDBY_HOT",
        "power_output_kw": 0.0,
        "rated_capacity_kw": 80.0,
        "fuel_consumption_rate_lh": 0.0,
        "engine_block_temp_c": 52.0,  # Maintained hot by jacket heater for instant start
        "oil_pressure_bar": 0.0,
        "coolant_temp_c": 54.0,
        "total_run_hours": 2180.0,
        "pre_heater_active": True,
    },
    "GEN-03": {
        "id": "GEN-03",
        "name": "Emergency Cold Genset 3 (Deep Shelter)",
        "status": "STANDBY_COLD",
        "power_output_kw": 0.0,
        "rated_capacity_kw": 80.0,
        "fuel_consumption_rate_lh": 0.0,
        "engine_block_temp_c": -12.0,  # Requires 45-min pre-heating cycle before crank
        "oil_pressure_bar": 0.0,
        "coolant_temp_c": -10.0,
        "total_run_hours": 940.2,
        "pre_heater_active": False,
    }
}

_fuel_inventory = {
    "total_capacity_liters": 75000,
    "current_stock_liters": 48200,
    "fuel_type": "Polar Grade Aviation Kerosene (F-34 / Jet A-1 with Anti-Gel Additives)",
    "daily_burn_rate_avg_liters": 220.0,
    "next_supply_ship_days": 115,
}


class GensetCommandRequest(BaseModel):
    genset_id: str = Field(..., description="GEN-01, GEN-02, or GEN-03")
    action: str = Field(..., description="START, STOP, PRE_HEAT, or SET_LOAD")
    target_load_kw: float = Field(default=0.0, ge=0.0, le=80.0)


@router.get("/generators", summary="Get Status of Polar Diesel Generators")
async def get_generators() -> List[Dict[str, Any]]:
    """Returns telemetry and readiness of all three polar emergency diesel generators."""
    return list(_gensets.values())


@router.post("/dispatch", summary="Dispatch or Control Diesel Genset")
async def dispatch_genset(
    payload: GensetCommandRequest,
    operator: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Commands a diesel generator. Includes polar interlocks:
    Prevents engine start if block temperature is below 40°C to prevent thermal shock / engine seizure.
    """
    if payload.genset_id not in _gensets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Genset {payload.genset_id} not found.")

    genset = _gensets[payload.genset_id]

    if payload.action == "START":
        if genset["engine_block_temp_c"] < 40.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Safety Interlock: Block temp ({genset['engine_block_temp_c']}°C) is below 40°C. "
                       f"Engage PRE_HEAT before starting to prevent cold engine failure in polar temperatures.",
            )
        genset["status"] = "RUNNING"
        genset["power_output_kw"] = payload.target_load_kw if payload.target_load_kw > 0 else 40.0
        genset["fuel_consumption_rate_lh"] = round(genset["power_output_kw"] * 0.26, 1)

    elif payload.action == "STOP":
        genset["status"] = "STANDBY_HOT"
        genset["power_output_kw"] = 0.0
        genset["fuel_consumption_rate_lh"] = 0.0

    elif payload.action == "PRE_HEAT":
        genset["pre_heater_active"] = True
        genset["engine_block_temp_c"] = 48.0
        genset["status"] = "STANDBY_HOT"

    elif payload.action == "SET_LOAD":
        if genset["status"] != "RUNNING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Genset must be RUNNING to set load.")
        genset["power_output_kw"] = payload.target_load_kw
        genset["fuel_consumption_rate_lh"] = round(payload.target_load_kw * 0.26, 1)

    return {
        "status": "success",
        "message": f"Command {payload.action} executed on {payload.genset_id} by {operator}",
        "genset_state": genset,
    }


@router.get("/fuel-reserve", summary="Get Polar Fuel Inventory & Autonomy Calculation")
async def get_fuel_reserve() -> Dict[str, Any]:
    """Calculates days of fuel autonomy based on current burn rate and seasonal resupply windows."""
    remaining_days = round(_fuel_inventory["current_stock_liters"] / _fuel_inventory["daily_burn_rate_avg_liters"], 1)
    resupply_margin_days = round(remaining_days - _fuel_inventory["next_supply_ship_days"], 1)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **_fuel_inventory,
        "autonomy_days": remaining_days,
        "resupply_safety_margin_days": resupply_margin_days,
        "reserve_alert_level": "NORMAL" if resupply_margin_days > 20 else "WARNING_CONSERVATION_REQUIRED",
    }

