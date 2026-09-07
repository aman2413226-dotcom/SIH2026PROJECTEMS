"""
PolarEMS Security & Intrusion Detection System (IDS) Router
Provides real-time security posture telemetry, attack audit logs, and Red Team testing endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any

from simulation.digital_twin import digital_twin
from backend.app.services.security_service import security_service

router = APIRouter(prefix="/security", tags=["Cyber-Physical Security & IDS"])


class LoadHijackRequest(BaseModel):
    surge_kw: float = Field(default=85.0, ge=20.0, le=200.0, description="Rogue load surge in kW")


@router.get("/status", summary="Get Current Security Posture & Anomaly Log")
async def get_security_status() -> Dict[str, Any]:
    """
    Returns the real-time cyber-physical security posture (SECURE / WARNING / COMPROMISED),
    active anomaly detections, and chronological audit log of intercepted attacks.
    """
    telemetry = digital_twin.latest_telemetry
    status = security_service.evaluate_telemetry(telemetry)
    return status


@router.post("/attack/load-hijack", summary="Red Team: Simulate Load Hijacking Attack")
async def attack_load_hijack(payload: LoadHijackRequest = LoadHijackRequest()) -> Dict[str, Any]:
    """
    Red Team Endpoint: Simulates a cyber-attack where an adversary hijacks station heating/HVAC
    controllers, causing an unnatural load spike to trip the microgrid.
    """
    result = security_service.launch_load_hijack(digital_twin, surge_kw=payload.surge_kw)
    return {
        "status": "ATTACK_DEPLOYED",
        "action": f"Injected {payload.surge_kw} kW rogue electrical load.",
        "posture": result["posture"],
        "security_details": result,
    }


@router.post("/attack/sensor-spoof", summary="Red Team: Simulate Sensor Spoofing Attack")
async def attack_sensor_spoof() -> Dict[str, Any]:
    """
    Red Team Endpoint: Simulates a false data injection attack spoofing meteorological sensors
    with impossible temperature discontinuities.
    """
    result = security_service.launch_sensor_spoof(digital_twin)
    return {
        "status": "ATTACK_DEPLOYED",
        "action": "Injected impossible +28.5°C spoofed temperature into AWS telemetry feed.",
        "posture": result["posture"],
        "security_details": result,
    }


@router.post("/attack/thermal-runaway", summary="Red Team: Simulate Battery Thermal Runaway Risk")
async def attack_thermal_runaway() -> Dict[str, Any]:
    """
    Red Team Endpoint: Injects an artificial thermal runaway anomaly on BESS cell telemetry.
    """
    result = security_service.launch_thermal_runaway(digital_twin)
    return {
        "status": "ATTACK_DEPLOYED",
        "action": "Injected rapid battery thermal heating to 54°C.",
        "posture": result["posture"],
        "security_details": result,
    }


@router.post("/reset", summary="Reset Security Posture and Clear Alarms")
async def reset_security_posture() -> Dict[str, Any]:
    """
    Operator clearance endpoint: Resets the cyber-physical posture back to SECURE,
    clears injected rogue loads, and logs resolution to audit trail.
    """
    result = security_service.reset_posture(digital_twin)
    return {
        "status": "SUCCESS",
        "message": "Security posture restored to SECURE. Injected rogue vectors cleared.",
        "security_details": result,
    }
