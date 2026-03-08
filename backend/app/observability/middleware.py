import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.metrics import http_request_duration_seconds, http_requests_total


class RequestTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        path = request.url.path
        method = request.method
        status_code = 500

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception:  # noqa: BLE001
            http_requests_total.labels(method=method, path=path, status="500").inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(
                time.perf_counter() - start
            )
            raise

        response.headers["X-Request-ID"] = request_id
        duration = time.perf_counter() - start
        http_requests_total.labels(method=method, path=path, status=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, path=path).observe(duration)
        return response
