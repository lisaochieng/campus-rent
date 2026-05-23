import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.metrics import record_http_request


REQUEST_ID_HEADER = "X-Request-ID"
logger = logging.getLogger("campusrent.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid4()))
        started_at = time.perf_counter()

        response = await call_next(request)
        duration_seconds = time.perf_counter() - started_at
        duration_ms = round(duration_seconds * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
