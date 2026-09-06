from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone
from SIH2026PROJECTEMS.backend.app.core.security import verify_api_key

router = APIRouter(prefix="/maintenance", tags=["Predictive Maintenance & Winterization"])

_schedules = [
    {
        "task_id": "MAINT-104",
        "asset": "Wind Turbine #1",
        "title": "Low-Temp Synthetic Grease Lubrication (Nacelle Bearing)",
        "priority": "HIGH",
        "due_date": "2026-09-12",
        "health_score": 88.0,
        "remaining_useful_life_hours": 1420,
        "winter_critical": True,
    },
    {
        "task_id": "MAINT-105",
        "asset": "Polar Genset 1 (GEN-01)",
        "title": "250-Hour Engine Lube Oil & Fuel Filter Replacement",
        "priority": "URGENT",
        "due_date": "2026-09-08",
        "health_score": 79.5,
        "remaining_useful_life_hours": 88,
        "winter_critical": True,
    },
    {
        "task_id": "MAINT-106",
        "asset": "BESS Battery Rack C",
        "title": "Jacket Heater Impedance & Terminal Torque Test",
        "priority": "MEDIUM",
        "due_date": "2026-09-20",
        "health_score": 95.0,
        "remaining_useful_life_hours": 3600,
        "winter_critical": True,
    }
]

_winterization_checklist = [
    {"item": "Diesel fuel tank biocides and anti-gel additives mixed", "completed": True},
    {"item": "Auxiliary genset coolant freeze point certified to -65°C", "completed": True},
    {"item": "External fuel line heat tracing cable insulation verified", "completed": True},
    {"item": "BESS emergency thermal bypass switch calibrated", "completed": True},
    {"item": "Emergency shelter survival rations & hand crank generator inspected", "completed": False},
]

_spare_parts = [
    {"part_number": "FILT-D3406", "name": "Caterpillar Heavy Duty Fuel Filter", "in_stock": 14, "min_required": 8},
    {"part_number": "HEAT-TRC-50M", "name": "50m Self-Regulating Trace Cable (120V)", "in_stock": 6, "min_required": 4},
    {"part_number": "BATT-MOD-72V", "name": "Modular LFP 72V Sub-Pack Unit", "in_stock": 3, "min_required": 2},
]


class CompleteTaskRequest(BaseModel):
    task_id: str
    technician_notes: str = Field(..., min_length=5)


@router.get("/schedules", summary="Get Predictive Maintenance Tasks & RUL")
async def get_maintenance_schedules() -> List[Dict[str, Any]]:
    """Returns scheduled and AI-recommended maintenance based on vibration, thermography, and run hours."""
    return _schedules


@router.get("/winterization-checklist", summary="Polar Winter-Over Readiness Checklist")
async def get_winterization_checklist() -> Dict[str, Any]:
    """Returns readiness protocol prior to polar winter isolation closure."""
    completed_count = sum(1 for item in _winterization_checklist if item["completed"])
    total_count = len(_winterization_checklist)
    return {
        "readiness_pct": round((completed_count / total_count) * 100, 1),
        "total_items": total_count,
        "completed_items": completed_count,
        "checklist": _winterization_checklist,
    }


@router.post("/log-action", summary="Log Completed Maintenance Procedure")
async def log_maintenance_action(
    payload: CompleteTaskRequest,
    operator: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Records completion of a maintenance task with technician signature."""
    for task in _schedules:
        if task["task_id"] == payload.task_id:
            task["health_score"] = 100.0
            task["last_completed_by"] = operator
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["notes"] = payload.technician_notes
            return {
                "status": "success",
                "message": f"Task {payload.task_id} marked as completed by {operator}",
                "task": task,
            }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance task ID not found.")


@router.get("/spares-inventory", summary="Mission-Critical Spare Parts Inventory")
async def get_spares_inventory() -> List[Dict[str, Any]]:
    """Returns stock levels for winter isolation where no deliveries are possible."""
    return _spare_parts

