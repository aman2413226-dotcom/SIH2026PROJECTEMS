"""
PolarEMS Battery Energy Storage System (BESS) API Router
Real-time state of charge, cell core temperatures, cold-derating factors, and thermal conditioning.
"""

import math
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin
from backend.app.core.config import settings
from backend.app.core.security import verify_api_key
from config.constants import get_capacity_factor, get_rate_factor

router = APIRouter(prefix="/battery", tags=["Battery Energy Storage System (BESS)"])


class ThermalControlRequest(BaseModel):
    mode: str = Field(..., description="AUTO, FORCED_HEATING, or ECO")
    target_temp_c: float = Field(default=20.0, ge=10.0, le=30.0)


class ReserveLimitRequest(BaseModel):
    min_reserve_threshold_pct: float = Field(..., ge=15.0, le=50.0)


@router.get("/status", summary="Get Current BESS Telemetry & Thermal Conditioning Status")
async def get_battery_status() -> Dict[str, Any]:
    """
    Returns real-time status of the Polar Battery Energy Storage System (BESS),
    including internal core temperature, derating factor, and heating jacket status.
    """
    bess = digital_twin.bess
    telemetry = digital_twin.latest_telemetry.get("bess", {})
    env = digital_twin.latest_telemetry.get("environment", {})

    cap_factor = get_capacity_factor(bess.cell_temp_c)
    rate_factor = get_rate_factor(bess.cell_temp_c)

    return {
        "timestamp": telemetry.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "station_code": digital_twin.config["station_code"],
        "capacity_kwh": bess.capacity_kwh,
        "effective_capacity_kwh": round(bess.capacity_kwh * cap_factor, 1),
        "capacity_derate_factor": round(cap_factor, 2),
        "rate_derate_factor": round(rate_factor, 2),
        "state_of_charge_pct": bess.soc_pct,
        "current_flow_kw": telemetry.get("bess_flow_kw", 0.0),
        "internal_cell_temp_c": bess.cell_temp_c,
        "ambient_temp_c": env.get("ambient_temp_c", -52.4),
        "thermal_heater_status": "ACTIVE" if bess.heater_active else "STANDBY",
        "thermal_heater_power_kw": bess.heater_power_kw if bess.heater_active else 0.0,
        "thermal_heater_mode": bess.heater_mode,
        "min_reserve_threshold_pct": 20.0,
        "is_critical_reserve": bess.soc_pct <= 20.0,
        "emergency_reserve_locked": True,
        "cycles_completed": round(bess.cycles, 1),
        "estimated_runtime_hours": round(telemetry.get("bess_stored_kwh", 350.0) / 48.0, 1),
    }


@router.post("/thermal-control", summary="Configure BESS Thermal Heating Jackets")
async def set_thermal_control(
    payload: ThermalControlRequest,
) -> Dict[str, Any]:
    """
    Configures the auxiliary battery thermal conditioning system.
    In polar conditions (-50°C to -80°C), cells must be actively heated to prevent electrolyte freezing.
    """
    if payload.mode not in ["AUTO", "FORCED_HEATING", "ECO"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode. Choose from AUTO, FORCED_HEATING, or ECO."
        )

    digital_twin.bess.heater_mode = payload.mode
    if payload.mode == "FORCED_HEATING":
        digital_twin.bess.heater_active = True
        digital_twin.bess.heater_power_kw = 6.5
    elif payload.mode == "ECO":
        digital_twin.bess.heater_power_kw = 3.2

    digital_twin.tick(seconds=1)

    return {
        "status": "success",
        "message": f"Battery thermal control updated to {payload.mode}.",
        "target_temp_c": payload.target_temp_c,
        "current_cell_temp_c": digital_twin.bess.cell_temp_c,
        "heater_power_kw": digital_twin.bess.heater_power_kw,
    }


@router.get("/telemetry-history", summary="Get 24-Hour Battery SOC & Thermal Trend")
async def get_battery_history() -> List[Dict[str, Any]]:
    """Returns 24-hour hourly trend of SOC, pack temperature, and heater draw."""
    history = []
    base_soc = digital_twin.bess.soc_pct
    for hour in range(24):
        soc = round(base_soc - (hour * 0.4) + (2.5 if 10 <= hour <= 16 else 0.0), 1)
        temp = round(19.2 + (math.sin(hour * 0.26) * 0.8), 1)
        history.append({
            "hour_offset": - (24 - hour),
            "state_of_charge_pct": max(min(soc, 100.0), 20.0),
            "cell_temp_c": temp,
            "ambient_temp_c": round(-52.0 - (3.0 if hour < 6 else 0.0), 1),
            "heater_draw_kw": 4.2 if temp < 18.0 else 0.0,
        })
    return history
