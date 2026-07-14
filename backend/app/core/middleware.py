import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_var

logger = get_logger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request-correlation id, stamped onto every log line emitted during
    the request via the request_id contextvar, and logs one access-log line per request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request_completed",
                extra={
                    "detail": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    }
                },
            )
            return response
        except Exception:
            logger.exception(
                "request_failed",
                extra={"detail": {"method": request.method, "path": request.url.path}},
            )
            raise
        finally:
            request_id_var.reset(token)
