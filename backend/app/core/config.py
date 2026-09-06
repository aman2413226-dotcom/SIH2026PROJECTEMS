import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "PolarEMS - AI Polar Research Station Energy Management System"
    PROJECT_DESCRIPTION: str = (
        "Mission-critical energy management system for polar research facilities operating under extreme "
        "Antarctic/Arctic conditions with wind, solar PV, BESS, thermal heating, and backup diesel dispatch."
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Station Metadata
    STATION_NAME: str = "Concordia Research Station (Dome C)"
    STATION_CODE: str = "DOMEC-ANTARCTICA"
    LATITUDE: float = -75.10
    LONGITUDE: float = 123.33
    ELEVATION_M: float = 3233.0

    # Safety & Survival Thresholds
    MIN_SAFE_TEMP_C: float = -80.0
    CRITICAL_BATTERY_RESERVE_PCT: float = 25.0
    CRITICAL_FUEL_RESERVE_HOURS: float = 96.0
    MAX_WIND_TURBINE_CUTOFF_MS: float = 25.0

    # Grid Capacities (kW)
    BASE_LIFE_SUPPORT_LOAD_KW: float = 45.0
    PEAK_STATION_LOAD_KW: float = 135.0
    MAX_WIND_CAPACITY_KW: float = 120.0
    MAX_SOLAR_CAPACITY_KW: float = 80.0
    BESS_CAPACITY_KWH: float = 450.0
    DIESEL_GENSET_COUNT: int = 3
    DIESEL_GENSET_RATED_KW: float = 80.0

    # Security
    SECRET_KEY: str = "polar-station-ai-energy-secret-change-in-production"
    API_KEY: str = "polar-station-operator-key-2026"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

