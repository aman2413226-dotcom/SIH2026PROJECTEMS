from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime, timezone
from SIH2026PROJECTEMS.backend.app.core.security import verify_api_key

router = APIRouter(prefix="/faults", tags=["AI Fault Detection & Diagnostics"])

# Simulated active polar microgrid faults
_active_faults = [
    {
        "fault_id": "FLT-9021",
        "timestamp": "2026-09-04T22:15:00Z",
        "system": "Wind Turbine #2",
        "severity": "WARNING",
        "fault_type": "BLADE_AERODYNAMIC_ICING",
        "ai_confidence_score": 0.94,
        "description": "High rotor vibration and 32% power degradation detected indicative of rime ice buildup on blades.",
        "ai_recommendation": "Activate electro-thermal blade heating elements; reduce rpm to prevent blade stress.",
        "acknowledged": False,
    },
    {
        "fault_id": "FLT-9025",
        "timestamp": "2026-09-04T23:40:00Z",
        "system": "Exterior Utility Conduit #4",
        "severity": "CRITICAL",
        "fault_type": "HEAT_TRACING_CURRENT_DROP",
        "ai_confidence_score": 0.98,
        "description": "Heater tracing loop impedance anomaly. Risk of fresh water line freezing within 90 minutes at -54°C.",
        "ai_recommendation": "Switch to redundant auxiliary thermal loop B immediately; dispatch technician to conduit 4.",
        "acknowledged": False,
    },
]

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
    notes: str = Field(default="", description="Operator corrective action notes")


@router.get("/active", summary="List Active AI-Detected Faults & Anomalies")
async def get_active_faults() -> List[Dict[str, Any]]:
    """Returns active anomaly detections across polar wind, solar, genset, and thermal infrastructure."""
    return _active_faults


@router.post("/{fault_id}/acknowledge", summary="Acknowledge and Resolve Fault")
async def acknowledge_fault(
    fault_id: str,
    payload: AcknowledgeFaultRequest,
    operator: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Acknowledge or clear an active fault after inspecting or resolving physical equipment."""
    for fault in _active_faults:
        if fault["fault_id"] == fault_id:
            fault["acknowledged"] = True
            fault["acknowledged_by"] = operator
            fault["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            fault["operator_notes"] = payload.notes
            return {
                "status": "success",
                "message": f"Fault {fault_id} marked as acknowledged by {operator}.",
                "fault": fault,
            }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fault ID {fault_id} not found.")


@router.get("/history", summary="Historical Fault Diagnostic Records")
async def get_fault_history() -> List[Dict[str, Any]]:
    """Returns past resolved anomalies and maintenance history."""
    return _fault_history

