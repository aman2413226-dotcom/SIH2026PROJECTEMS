from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class EventSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class StationEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: EventSeverity = EventSeverity.INFO
    source: str = "PolarEMS-Core"
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class BlizzardAlertEvent(StationEvent):
    event_type: str = "WEATHER_BLIZZARD_ALERT"
    severity: EventSeverity = EventSeverity.CRITICAL


class BatteryThermalCriticalEvent(StationEvent):
    event_type: str = "BESS_THERMAL_CRITICAL"
    severity: EventSeverity = EventSeverity.EMERGENCY


class DieselAutoStartEvent(StationEvent):
    event_type: str = "DIESEL_GENSET_AUTO_DISPATCH"
    severity: EventSeverity = EventSeverity.WARNING


class FaultDetectedEvent(StationEvent):
    event_type: str = "AI_FAULT_DETECTED"
    severity: EventSeverity = EventSeverity.WARNING

