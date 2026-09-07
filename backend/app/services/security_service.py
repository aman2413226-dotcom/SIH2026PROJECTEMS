"""
PolarEMS Cyber-Physical Intrusion Detection System (IDS) Service
Monitors microgrid telemetry for Sensor Spoofing, Load Hijacking, and Battery Thermal Runaway.
Provides interactive Red Team endpoints for live security demonstrations.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class SecurityIDSService:
    """
    Real-time heuristics and anomaly detection engine monitoring Digital Twin telemetry.
    Detects cyber-physical attacks and coordinates automated grid isolation/containment.
    """

    def __init__(self):
        self.posture = "SECURE"  # "SECURE", "WARNING", "COMPROMISED"
        self.active_threats: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = [
            {
                "timestamp": "2026-09-06T08:15:22Z",
                "event_id": "SEC-LOG-001",
                "vector": "BASELINE_VERIFICATION",
                "severity": "INFO",
                "status": "CLEARED",
                "details": "Heuristics IDS baseline synchronized with Maitri station SCADA gateway.",
                "mitigation": "Continuous telemetry monitoring active.",
            }
        ]

        # Prior telemetry memory for delta calculations
        self.prev_temp: Optional[float] = None
        self.prev_wind: Optional[float] = None
        self.prev_load: Optional[float] = None
        self.prev_batt_temp: Optional[float] = None

    def evaluate_telemetry(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic evaluation of telemetry stream on every tick.
        Detects sensor spoofing, load hijacking, and battery thermal runaway.
        """
        env = telemetry.get("environment", {})
        loads = telemetry.get("loads", {})
        bess = telemetry.get("bess", {})

        current_temp = env.get("ambient_temp_c", -50.0)
        current_wind = env.get("wind_speed_ms", 12.0)
        current_load = telemetry.get("power_balance", {}).get("total_demand_kw", 80.0)
        current_batt_temp = bess.get("cell_temp_c", 20.0)

        new_threats = []

        # 1. Sensor Spoofing Check
        if self.prev_temp is not None:
            temp_delta = abs(current_temp - self.prev_temp)
            if temp_delta >= 15.0 or current_temp > 20.0 or current_temp < -90.0:
                threat = {
                    "id": f"THREAT-SPOOF-{int(datetime.now().timestamp())}",
                    "type": "SENSOR_SPOOFING",
                    "severity": "CRITICAL",
                    "channel": "AMBIENT_TEMPERATURE_SENSOR_AWS",
                    "observed_value": current_temp,
                    "previous_value": self.prev_temp,
                    "delta": round(temp_delta, 1),
                    "description": f"Physically impossible temperature discontinuity detected (ΔT = {temp_delta:.1f}°C). Signature matches falsified packet injection.",
                    "mitigation": "Sensor marked UNTRUSTED. Failover to backup platinum RTD sensor array.",
                }
                new_threats.append(threat)

        if self.prev_wind is not None:
            wind_delta = abs(current_wind - self.prev_wind)
            if wind_delta >= 20.0:
                threat = {
                    "id": f"THREAT-WIND-{int(datetime.now().timestamp())}",
                    "type": "SENSOR_SPOOFING",
                    "severity": "HIGH",
                    "channel": "ULTRASONIC_ANEMOMETER",
                    "observed_value": current_wind,
                    "previous_value": self.prev_wind,
                    "delta": round(wind_delta, 1),
                    "description": f"Impossible wind velocity jump of {wind_delta:.1f} m/s in single sample period.",
                    "mitigation": "Feather turbines safety-first; cross-verify with cup anemometer.",
                }
                new_threats.append(threat)

        # 2. Load Hijacking Check
        hijacked_kw = loads.get("hijacked_attack_load_kw", 0.0)
        if hijacked_kw > 0.0 or (self.prev_load is not None and (current_load - self.prev_load) >= 70.0):
            threat = {
                "id": f"THREAT-LOAD-{int(datetime.now().timestamp())}",
                "type": "LOAD_HIJACKING",
                "severity": "CRITICAL",
                "channel": "STATION_HVAC_AND_PUMPING_CONTROLLER",
                "observed_load_kw": current_load,
                "surge_kw": hijacked_kw if hijacked_kw > 0.0 else (current_load - (self.prev_load or 0.0)),
                "description": "Unscheduled massive load spike detected on life support / auxiliary bus. Signature matches malicious remote takeover command.",
                "mitigation": "Microgrid EMS tripped auxiliary breakers. Emergency life-support priority bus locked.",
            }
            new_threats.append(threat)

        # 3. Battery Thermal Anomaly / Runaway Check
        if current_batt_temp >= 45.0 or (self.prev_batt_temp is not None and (current_batt_temp - self.prev_batt_temp) >= 3.0):
            threat = {
                "id": f"THREAT-THERMAL-{int(datetime.now().timestamp())}",
                "type": "THERMAL_RUNAWAY_RISK",
                "severity": "CRITICAL",
                "channel": "BESS_CORE_MODULE_4",
                "observed_temp_c": current_batt_temp,
                "description": f"Battery core temperature reached {current_batt_temp:.1f}°C in polar subzero climate. Exceeds safe LFP threshold.",
                "mitigation": "BESS contactors opened. Active Novec 1230 fire suppressant system pre-armed.",
            }
            new_threats.append(threat)

        # Update previous values
        self.prev_temp = current_temp
        self.prev_wind = current_wind
        self.prev_load = current_load
        self.prev_batt_temp = current_batt_temp

        # Update state posture
        if new_threats:
            self.posture = "COMPROMISED"
            for t in new_threats:
                if not any(at["type"] == t["type"] for at in self.active_threats):
                    self.active_threats.append(t)
                    self.audit_log.insert(0, {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event_id": f"SEC-ALERT-{len(self.audit_log) + 1:03d}",
                        "vector": t["type"],
                        "severity": t["severity"],
                        "status": "INTERCEPTED",
                        "details": t["description"],
                        "mitigation": t["mitigation"],
                    })

        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """Returns current IDS security posture and attack audit log."""
        return {
            "posture": self.posture,
            "security_score": 100 if self.posture == "SECURE" else (75 if self.posture == "WARNING" else 20),
            "threat_level": "LOW" if self.posture == "SECURE" else ("ELEVATED" if self.posture == "WARNING" else "CRITICAL"),
            "active_threats_count": len(self.active_threats),
            "active_threats": self.active_threats,
            "audit_log": self.audit_log[:15],
            "last_inspected": datetime.now(timezone.utc).isoformat(),
        }

    # Red Team Simulation Methods
    def launch_load_hijack(self, twin, surge_kw: float = 85.0) -> Dict[str, Any]:
        """Red Team: Simulates malicious takeover of heating loads."""
        twin.hijacked_load_kw = surge_kw
        self.posture = "COMPROMISED"
        threat = {
            "id": f"THREAT-HIJACK-{int(datetime.now().timestamp())}",
            "type": "LOAD_HIJACKING",
            "severity": "CRITICAL",
            "channel": "MICROGRID_SCADA_CONTROLLER",
            "observed_load_kw": surge_kw,
            "description": f"Simulated Red Team Load Hijack: Injected +{surge_kw} kW artificial surge into heating bus.",
            "mitigation": "Automated IDS Interception: Isolated compromised HVAC sub-circuit; flagged cyber incident.",
        }
        self.active_threats = [t for t in self.active_threats if t["type"] != "LOAD_HIJACKING"]
        self.active_threats.append(threat)
        self.audit_log.insert(0, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"SEC-ATTACK-{len(self.audit_log) + 1:03d}",
            "vector": "LOAD_HIJACKING",
            "severity": "CRITICAL",
            "status": "INTERCEPTED",
            "details": f"Red Team attack simulated: Injected +{surge_kw} kW rogue electrical load.",
            "mitigation": "Heuristics IDS triggered. Posture transitioned to COMPROMISED.",
        })
        twin.tick(seconds=1)
        return self.get_status()

    def launch_sensor_spoof(self, twin) -> Dict[str, Any]:
        """Red Team: Simulates spoofed sensor telemetry."""
        twin.ambient_temp_c = 28.5  # Impossible +28.5°C in Antarctica!
        self.posture = "COMPROMISED"
        threat = {
            "id": f"THREAT-SPOOF-{int(datetime.now().timestamp())}",
            "type": "SENSOR_SPOOFING",
            "severity": "CRITICAL",
            "channel": "AWS_METEOROLOGICAL_SENSOR",
            "observed_value": 28.5,
            "description": "Simulated Red Team Sensor Spoof: Injected +28.5°C temperature packet in deep Antarctic polar winter.",
            "mitigation": "IDS detected temperature discrepancy with satellite IR reanalysis; quarantined sensor channel.",
        }
        self.active_threats = [t for t in self.active_threats if t["type"] != "SENSOR_SPOOFING"]
        self.active_threats.append(threat)
        self.audit_log.insert(0, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"SEC-ATTACK-{len(self.audit_log) + 1:03d}",
            "vector": "SENSOR_SPOOFING",
            "severity": "CRITICAL",
            "status": "INTERCEPTED",
            "details": "Red Team sensor spoof attack: Injected +28.5°C impossible temperature reading.",
            "mitigation": "Heuristics IDS flagged packet anomaly. Sensor input quarantined.",
        })
        twin.tick(seconds=1)
        return self.get_status()

    def launch_thermal_runaway(self, twin) -> Dict[str, Any]:
        """Red Team: Simulates battery thermal runaway anomaly."""
        twin.bess.cell_temp_c = 54.0
        self.posture = "COMPROMISED"
        threat = {
            "id": f"THREAT-THERMAL-{int(datetime.now().timestamp())}",
            "type": "THERMAL_RUNAWAY_RISK",
            "severity": "CRITICAL",
            "channel": "BESS_CORE_MODULE_4",
            "observed_temp_c": 54.0,
            "description": "Simulated Red Team Cyber-Physical Anomaly: Forced battery cell temperature to 54.0°C.",
            "mitigation": "IDS triggered emergency contactor isolation; disengaged charge controller.",
        }
        self.active_threats = [t for t in self.active_threats if t["type"] != "THERMAL_RUNAWAY_RISK"]
        self.active_threats.append(threat)
        self.audit_log.insert(0, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"SEC-ATTACK-{len(self.audit_log) + 1:03d}",
            "vector": "THERMAL_RUNAWAY_RISK",
            "severity": "CRITICAL",
            "status": "INTERCEPTED",
            "details": "Red Team battery thermal runaway anomaly injected.",
            "mitigation": "BESS high-temperature contactor opened automatically.",
        })
        twin.tick(seconds=1)
        return self.get_status()

    def reset_posture(self, twin) -> Dict[str, Any]:
        """Clears all active threats and returns system to SECURE posture."""
        twin.hijacked_load_kw = 0.0
        if twin.ambient_temp_c > 0.0:
            twin.ambient_temp_c = -52.4
        if twin.bess.cell_temp_c > 35.0:
            twin.bess.cell_temp_c = 19.5

        self.posture = "SECURE"
        self.active_threats.clear()
        self.audit_log.insert(0, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"SEC-RESET-{len(self.audit_log) + 1:03d}",
            "vector": "OPERATOR_CLEARANCE",
            "severity": "INFO",
            "status": "CLEARED",
            "details": "Operator manual override: Security alarms acknowledged and posture reset to SECURE.",
            "mitigation": "All subsystems returned to normal autonomous control.",
        })
        twin.tick(seconds=1)
        return self.get_status()


security_service = SecurityIDSService()
