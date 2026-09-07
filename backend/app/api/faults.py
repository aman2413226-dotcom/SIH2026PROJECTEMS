"""
PolarEMS AI Fault Detection & Diagnostics Router
Exposes active physical microgrid faults, historical incidents, and operator acknowledgment.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone

from simulation.digital_twin import digital_twin

router = APIRouter(prefix="/faults", tags=["AI Fault Detection & Diagnostics"])

# Persistent diagnostic history
_fault_history = [
    {
        "fault_id": "FLT-8991",
        "timestamp": "2026-09-02T14:10:00Z",
        "resolved_at": "2026-09-02T15:20:00Z",
        "system": "Solar PV Array East",
        "severity": "MINOR",
        "fault_type": "SNOW_DRIFT_OCCLUSION",
        "ai_confidence_score": 0.91,
        "description": "50% surface snow burial following katabatic wind event.",
        "resolution": "Automated panel tilt cycle shook off loose snow; output restored.",
    }
]


class AcknowledgeFaultRequest(BaseModel):
    notes: str = Field(default="Inspected and verified", description="Operator corrective action notes")


@router.get("/active", summary="List Active AI-Detected Faults & Anomalies")
async def get_active_faults() -> List[Dict[str, Any]]:
    """Returns all active faults from the Digital Twin engine."""
    faults = list(digital_twin.active_faults.values())
    if not faults:
        # Default baseline warning if no physical fault is actively injected
        return [
            {
                "fault_id": "FLT-9021",
                "timestamp": digital_twin.sim_time.isoformat(),
                "system": "Wind Turbine #2",
                "severity": "WARNING",
                "fault_type": "ROTOR_ICING_WATCH",
                "ai_confidence_score": 0.92,
                "description": "Subzero humidity profile indicates elevated riming conditions on blade aerofoils.",
                "ai_recommendation": "Electro-thermal blade de-icing on standby.",
                "acknowledged": False,
            }
        ]
    return faults


@router.post("/{fault_id}/acknowledge", summary="Acknowledge and Clear Fault")
async def acknowledge_fault(
    fault_id: str,
    payload: AcknowledgeFaultRequest = AcknowledgeFaultRequest(),
) -> Dict[str, Any]:
    """Acknowledge and resolve an active fault in the Digital Twin."""
    if fault_id in digital_twin.active_faults:
        fault = digital_twin.active_faults[fault_id]
        fault["acknowledged"] = True
        fault["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        fault["notes"] = payload.notes
        digital_twin.clear_fault(fault_id)
        _fault_history.insert(0, {
            **fault,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "success",
            "message": f"Fault {fault_id} cleared by operator.",
            "fault": fault,
        }

    return {
        "status": "success",
        "message": f"Fault {fault_id} marked as acknowledged.",
        "fault_id": fault_id,
    }


@router.get("/history", summary="Historical Fault Diagnostic Records")
async def get_fault_history() -> List[Dict[str, Any]]:
    """Returns past resolved anomalies and maintenance history."""
    return _fault_history
