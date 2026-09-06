from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.core.security import verify_api_key

router = APIRouter(prefix="/battery", tags=["Battery Energy Storage System (BESS)"])

# In-memory polar battery state (simulated hardware telemetry)
_battery_state = {
    "capacity_kwh": settings.BESS_CAPACITY_KWH,
    "current_charge_kwh": 337.5,
    "state_of_charge_pct": 75.0,
    "state_of_health_pct": 96.5,
    "voltage_v": 768.4,
    "current_flow_kw": -18.5,  # negative: discharging to station, positive: charging
    "internal_cell_temp_c": 19.8,
    "ambient_temp_c": -54.2,
    "thermal_heater_status": "ACTIVE",
    "thermal_heater_power_kw": 4.2,
    "min_reserve_threshold_pct": settings.CRITICAL_BATTERY_RESERVE_PCT,
    "emergency_reserve_locked": True,
    "cycles_completed": 642,
}


class ThermalControlRequest(BaseModel):
    mode: str = Field(..., description="AUTO, FORCED_HEATING, or ECO")
    target_temp_c: float = Field(default=20.0, ge=10.0, le=30.0)


class ReserveLimitRequest(BaseModel):
    min_reserve_threshold_pct: float = Field(..., ge=15.0, le=50.0)


@router.get("/status", summary="Get Current BESS Telemetry & Thermal Conditioning Status")
async def get_battery_status() -> Dict[str, Any]:
    """
    Returns real-time status of the Polar Battery Energy Storage System (BESS),
    including internal core temperature and auxiliary heating jackets essential for polar survival.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station_code": settings.STATION_CODE,
        **_battery_state,
        "is_critical_reserve": _battery_state["state_of_charge_pct"] <= _battery_state["min_reserve_threshold_pct"],
        "estimated_runtime_hours": round(_battery_state["current_charge_kwh"] / settings.BASE_LIFE_SUPPORT_LOAD_KW, 1),
    }


@router.post("/thermal-control", summary="Configure BESS Thermal Heating Jackets")
async def set_thermal_control(
    payload: ThermalControlRequest,
    operator: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Configures the auxiliary battery thermal conditioning system.
    In polar conditions (-50°C to -80°C), cells must be actively heated to prevent dendrite damage.
    """
    if payload.mode not in ["AUTO", "FORCED_HEATING", "ECO"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode. Choose from AUTO, FORCED_HEATING, or ECO."
        )

    _battery_state["thermal_heater_status"] = payload.mode
    _battery_state["thermal_heater_power_kw"] = 6.5 if payload.mode == "FORCED_HEATING" else 3.8

    return {
        "status": "success",
        "message": f"Battery thermal control updated to {payload.mode} by {operator}",
        "target_temp_c": payload.target_temp_c,
        "current_cell_temp_c": _battery_state["internal_cell_temp_c"],
        "heater_power_kw": _battery_state["thermal_heater_power_kw"],
    }


@router.post("/reserve-limit", summary="Set Emergency Life-Support Reserve Threshold")
async def set_reserve_limit(
    payload: ReserveLimitRequest,
    operator: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Updates the minimum battery reserve reserved strictly for habitat heating and life-support.
    """
    _battery_state["min_reserve_threshold_pct"] = payload.min_reserve_threshold_pct
    return {
        "status": "success",
        "min_reserve_threshold_pct": _battery_state["min_reserve_threshold_pct"],
        "updated_by": operator,
    }


@router.get("/telemetry-history", summary="Get 24-Hour Battery SOC & Thermal Trend")
async def get_battery_history() -> List[Dict[str, Any]]:
    """Returns 24-hour hourly trend of SOC, pack temperature, and heater draw."""
    history = []
    base_soc = 82.0
    for hour in range(24):
        soc = round(base_soc - (hour * 0.7) + (3.0 if 10 <= hour <= 16 else 0.0), 1)
        temp = round(18.5 + (0.5 if hour % 2 == 0 else -0.3), 1)
        history.append({
            "hour_offset": - (24 - hour),
            "state_of_charge_pct": max(min(soc, 100.0), 20.0),
            "cell_temp_c": temp,
            "ambient_temp_c": round(-52.0 - (3.0 if hour < 6 else 0.0), 1),
            "heater_draw_kw": 4.1,
        })
    return history

