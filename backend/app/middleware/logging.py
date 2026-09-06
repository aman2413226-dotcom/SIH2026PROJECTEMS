import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from SIH2026PROJECTEMS.backend.app.core.logger import logger


class TelemetryLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor incoming request latency, path access, and HTTP status codes
    for critical polar station operations.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url_path = request.url.path

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000.0

            logger.info(
                f"{method} {url_path} - Status: {response.status_code} - "
                f"Latency: {process_time_ms:.2f}ms - Client: {client_ip}"
            )
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
            return response
        except Exception as exc:
            process_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Unhandled error processing {method} {url_path} after {process_time_ms:.2f}ms: {exc}"
            )
            raise exc

