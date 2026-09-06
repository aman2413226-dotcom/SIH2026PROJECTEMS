import sys
from pathlib import Path

# Ensure project root is in sys.path to support running from root or backend directory
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.middleware.cors import setup_cors
from backend.app.middleware.logging import TelemetryLoggingMiddleware
from backend.app.events.event_bus import event_bus
from backend.app.events.events import StationEvent, EventSeverity

# Import all 9 API Routers
from backend.app.api import (
    battery,
    dashboard,
    diesel,
    emission,
    faults,
    forecast,
    maintenance,
    simulation,
    weather,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: Runs diagnostics on startup and graceful shutdown."""
    logger.info("=" * 60)
    logger.info(f"Initializing {settings.PROJECT_NAME}")
    logger.info(f"Station: {settings.STATION_NAME} [{settings.STATION_CODE}]")
    logger.info(f"Coordinates: Lat {settings.LATITUDE}, Long {settings.LONGITUDE} | Alt: {settings.ELEVATION_M}m")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    logger.info("Mission-critical life support energy telemetry active.")
    logger.info("=" * 60)

    # Publish startup event to internal bus
    await event_bus.publish(
        StationEvent(
            event_id="STARTUP-INIT",
            event_type="SYSTEM_STARTUP",
            severity=EventSeverity.INFO,
            source="PolarEMS-Lifespan",
            message=f"Polar EMS initialized successfully for {settings.STATION_NAME}.",
        )
    )

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME} gracefully...")


# FastAPI Application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 1. Setup CORS Middleware
setup_cors(app)

# 2. Add Telemetry Logging Middleware
app.add_middleware(TelemetryLoggingMiddleware)

# 3. Register All 9 Domain Routers under API_V1_STR
api_prefix = settings.API_V1_STR
app.include_router(battery.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(diesel.router, prefix=api_prefix)
app.include_router(emission.router, prefix=api_prefix)
app.include_router(faults.router, prefix=api_prefix)
app.include_router(forecast.router, prefix=api_prefix)
app.include_router(maintenance.router, prefix=api_prefix)
app.include_router(simulation.router, prefix=api_prefix)
app.include_router(weather.router, prefix=api_prefix)


@app.get("/", summary="Polar EMS Root Status Banner")
async def root():
    """Returns basic system status and links to interactive OpenAPI documentation."""
    return {
        "system": settings.PROJECT_NAME,
        "station": settings.STATION_NAME,
        "station_code": settings.STATION_CODE,
        "status": "OPERATIONAL",
        "api_documentation": "/docs",
        "interactive_redoc": "/redoc",
        "api_v1_prefix": settings.API_V1_STR,
        "available_modules": [
            "battery",
            "dashboard",
            "diesel",
            "emission",
            "faults",
            "forecast",
            "maintenance",
            "simulation",
            "weather",
        ]
    }


@app.get("/health", summary="Health Check Endpoint")
async def health_check():
    """Health check endpoint for Docker / Kubernetes or cloud monitors."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "station": settings.STATION_CODE}
    )


if __name__ == "__main__":
    # Allows running directly via `python main.py` or from VS Code debug run
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

