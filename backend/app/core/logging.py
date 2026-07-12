import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),
]

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
"""Set by `app.core.middleware.RequestContextMiddleware` for the duration of one HTTP
request. Reading it here (rather than threading a `request_id` parameter through every
service/node/repository call) is what lets every log line emitted anywhere during that
request — including deep inside the LangGraph pipeline — carry the same correlation id
with zero call-site changes."""


class SecretRedactionFilter(logging.Filter):
    """Strips API-key-shaped substrings from log records before they are emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = message
        for pattern in _SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


class RequestIdFilter(logging.Filter):
    """Stamps the active request's correlation id onto every record, unless the call site
    already passed one explicitly via `extra={"request_id": ...}`."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            request_id = request_id_var.get()
            if request_id is not None:
                record.request_id = request_id
        return True


_STANDARD_RECORD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None)))


class JsonFormatter(logging.Formatter):
    """Structured JSON logs. Any `extra={...}` kwarg passed to a logging call
    (e.g. `logger.info("...", extra={"claim_id": claim_id, "chunk_count": 3})`)
    is included verbatim in the emitted record — this is what every agent
    node's logging relies on for machine-parseable, claim-correlated logs,
    rather than free-text messages an operator has to grep and guess at."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(log_level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SecretRedactionFilter())
    handler.addFilter(RequestIdFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
