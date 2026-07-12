"""ASGI middleware: request correlation id + structured access logging.

One middleware, two responsibilities that belong together: it assigns the
correlation id that `app.core.logging.RequestIdFilter` stamps onto every log
line for the duration of the request, and it emits the access-log line
itself. Splitting these into two middlewares would mean the access log
couldn't include the id it's responsible for creating.

Implemented as a plain ASGI middleware (`__call__(scope, receive, send)`),
not `starlette.middleware.base.BaseHTTPMiddleware`. `BaseHTTPMiddleware`
reconstructs the response from a buffered stream of ASGI messages, which is
well known to interact badly with FastAPI's own exception-handler
middleware: an exception already turned into a response by a registered
`@app.exception_handler` can still re-propagate past a `try/except` wrapped
around `call_next`, so the response never makes it out (see
https://github.com/encode/starlette/discussions/2391). Injecting the
`X-Request-ID` header via a wrapped `send` instead sidesteps that entirely
— every ASGI message, including ones sent from inside an exception handler,
passes straight through in real time.

The request id is stashed in *two* places, deliberately: `request_id_var`
(a contextvar) for every ordinary log line emitted while this request is
being handled, and `scope["state"]["request_id"]` for the one consumer that
runs *outside* this middleware's own try/finally — Starlette treats a
handler registered for the bare `Exception` class specially, wiring it into
`ServerErrorMiddleware`, which wraps *everything* (including this
middleware) rather than sitting where every other exception handler does.
By the time that handler runs, this middleware's `finally` has already
reset the contextvar. `scope` is the same mutable dict threaded through
every layer regardless of how exceptions propagate, so it survives where
the contextvar can't — see `app.core.exceptions.handle_unexpected_error`.
"""

import time
import uuid
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger, request_id_var

logger = get_logger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_HEADER_BYTES = REQUEST_ID_HEADER.encode("latin-1")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _header_value(scope, REQUEST_ID_HEADER_BYTES) or str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)
        status_code = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers.append(REQUEST_ID_HEADER, request_id)
            await send(message)

        start = time.perf_counter()
        log_fields: dict[str, Any] = {
            "request_id": request_id,
            "method": scope["method"],
            "path": scope["path"],
        }
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            log_fields["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
            logger.exception("request_failed", extra=log_fields)
            raise
        else:
            log_fields["status_code"] = status_code
            log_fields["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
            logger.info("request_completed", extra=log_fields)
        finally:
            request_id_var.reset(token)


def _header_value(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name.lower():
            return value.decode("latin-1")
    return None
