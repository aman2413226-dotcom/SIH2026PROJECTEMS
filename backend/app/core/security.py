from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from backend.app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-Polar-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Validates API key for mission-critical Polar EMS controls.
    Allows development mode bypass if configured, or validates against settings.API_KEY.
    """
    if settings.DEBUG and not api_key:
        # Allow default operator access in debug/development mode
        return "operator_dev_mode"

    if api_key == settings.API_KEY:
        return "station_chief_engineer"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid or missing Polar Station API Key (X-Polar-API-Key header required).",
    )

