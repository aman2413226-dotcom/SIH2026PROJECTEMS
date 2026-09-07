"""
PolarEMS Predictive Maintenance & Antarctic Winterization Router
Tracks component health scores, Remaining Useful Life (RUL), and winterization protocols.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin
from backend.app.core.config import settings

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
    {"item": "Emergency shelter survival rations & hand crank generator inspected", "completed": True},
]

_spare_parts = [
    {"part_number": "FILT-D3406", "name": "Heavy Duty Fuel Filter Set", "in_stock": 14, "min_required": 8},
    {"part_number": "HEAT-TRC-50M", "name": "50m Self-Regulating Trace Cable (120V)", "in_stock": 6, "min_required": 4},
    {"part_number": "BATT-MOD-72V", "name": "Modular LFP Sub-Pack Unit", "in_stock": 3, "min_required": 2},
]


class CompleteTaskRequest(BaseModel):
    task_id: str
    technician_notes: str = Field(default="Completed winterization inspection", min_length=3)


@router.get("/schedules", summary="Active Predictive Maintenance Tasks")
async def get_maintenance_schedules() -> List[Dict[str, Any]]:
    """Returns predictive maintenance tasks derived from runtime hours and vibration telemetry."""
    # Update GEN-01 remaining useful life from live engine hours
    gen1 = digital_twin.diesel.gensets[0]
    _schedules[1]["remaining_useful_life_hours"] = round(gen1.get("maintenance_due_hours", 88.0), 1)
    return _schedules


@router.post("/tasks/complete", summary="Mark Maintenance Task Completed")
async def complete_task(
    payload: CompleteTaskRequest,
) -> Dict[str, Any]:
    """Marks a scheduled maintenance task completed and resets engine service timer."""
    for task in _schedules:
        if task["task_id"] == payload.task_id:
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["technician_notes"] = payload.technician_notes
            task["health_score"] = 99.0
            if "Genset" in task["asset"]:
                digital_twin.diesel.gensets[0]["maintenance_due_hours"] = 500.0
            return {
                "status": "success",
                "message": f"Task {payload.task_id} marked complete.",
                "task": task,
            }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {payload.task_id} not found.")


@router.get("/winterization-checklist", summary="Antarctic Station Winterization Readiness")
async def get_winterization_checklist() -> Dict[str, Any]:
    """Audit checklist for station readiness prior to polar winter isolation."""
    completed = sum(1 for item in _winterization_checklist if item["completed"])
    total = len(_winterization_checklist)
    return {
        "station": digital_twin.config["station_name"],
        "readiness_percentage": round((completed / total) * 100, 1),
        "certified_for_polar_winter": completed == total,
        "checklist": _winterization_checklist,
    }


@router.get("/spare-parts-inventory", summary="Critical Spare Parts Stock Level")
async def get_spare_parts() -> List[Dict[str, Any]]:
    """Returns inventory status of mission-critical microgrid spare parts."""
    return _spare_parts
