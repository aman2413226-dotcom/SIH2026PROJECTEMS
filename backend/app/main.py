import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root and parent are in sys.path to support any execution context
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root.parent) not in sys.path:
    sys.path.insert(0, str(_project_root.parent))

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.middleware.cors import setup_cors
from backend.app.middleware.logging import TelemetryLoggingMiddleware
from backend.app.events.event_bus import event_bus
from backend.app.events.events import StationEvent, EventSeverity
from simulation.digital_twin import digital_twin

# Import domain API routers
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
    security,
)

# Background simulation loop task reference
_sim_task: asyncio.Task = None


async def simulation_background_loop():
    """Continuously runs the Digital Twin physics tick in real time."""
    logger.info("Starting PolarEMS Digital Twin real-time physics loop.")
    try:
        while True:
            if digital_twin.is_running:
                digital_twin.tick(seconds=1.0)
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        logger.info("Digital Twin background simulation loop stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: Initializes services, seeds models, and runs digital twin."""
    global _sim_task
    logger.info("=" * 65)
    logger.info(f"Initializing {settings.PROJECT_NAME}")
    logger.info(f"Active Station: {settings.STATION_NAME} [{settings.STATION_CODE}]")
    logger.info(f"Antarctic Coordinates: Lat {settings.LATITUDE}, Long {settings.LONGITUDE} | Alt: {settings.ELEVATION_M}m")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    logger.info("Mission-critical life support energy telemetry active.")
    logger.info("=" * 65)

    # Start Digital Twin background physics clock
    _sim_task = asyncio.create_task(simulation_background_loop())

    # Publish startup event to event bus
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

    if _sim_task and not _sim_task.done():
        _sim_task.cancel()

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

# 3. Register All 10 Domain Routers under API_V1_STR
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
app.include_router(security.router, prefix=api_prefix)


@app.get("/", summary="Polar EMS Root Status Banner")
async def root():
    """Returns basic system status and links to interactive OpenAPI documentation."""
    return {
        "system": settings.PROJECT_NAME,
        "station": digital_twin.config["station_name"],
        "station_code": digital_twin.config["station_code"],
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
            "security",
            "simulation",
            "weather",
        ]
    }


@app.get("/health", summary="Health Check Endpoint")
async def health_check():
    """Health check endpoint for Docker / Kubernetes or cloud monitors."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "station": digital_twin.config["station_code"],
            "simulation_running": digital_twin.is_running,
            "speed_multiplier": digital_twin.speed_multiplier,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
