import logging
import sys
from backend.app.core.config import settings


def setup_logger(name: str = "polar_ems") -> logging.Logger:
    """
    Configures and returns a structured logger tailored for Polar Station telemetry
    and mission-critical event tracking.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

        # Polar Station Log Formatter
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [POLAR-EMS | %(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S UTC",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger("polar_ems_system")

