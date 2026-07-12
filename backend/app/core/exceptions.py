from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.core.middleware import REQUEST_ID_HEADER

logger = get_logger(__name__)


class ClaimAgentError(Exception):
    """Base class for all domain errors in this service."""

    error_code = "internal_error"
    status_code = 500

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = context


class AuthenticationError(ClaimAgentError):
    """Missing or invalid `X-API-Key`. Distinct from a 403: this project has no
    per-user roles/permissions, only "is this caller holding a valid key," so
    every auth failure is a 401, never a 403."""

    error_code = "unauthorized"
    status_code = 401


class ClaimNotFoundError(ClaimAgentError):
    error_code = "claim_not_found"
    status_code = 404


class ClaimantNotFoundError(ClaimAgentError):
    error_code = "claimant_not_found"
    status_code = 404


class DisputeNotFoundError(ClaimAgentError):
    error_code = "dispute_not_found"
    status_code = 404


class InvalidUploadError(ClaimAgentError):
    error_code = "invalid_upload"
    status_code = 422


class VectorStoreError(ClaimAgentError):
    error_code = "vector_store_error"
    status_code = 503


class LLMProviderError(ClaimAgentError):
    error_code = "llm_provider_error"
    status_code = 503


class GraphStateError(ClaimAgentError):
    """A node read GraphState and found a required field missing or
    malformed — an invariant violation between nodes (e.g. Final Output
    running without an upstream node having set `decision`), not a bad
    request. Distinct from InvalidUploadError, which is a bad *input*."""

    error_code = "graph_state_error"
    status_code = 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ClaimAgentError)
    async def handle_claim_agent_error(request: Request, exc: ClaimAgentError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                **exc.context,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Same `{error_code, message, ...}` shape as every other error response — the
        frontend has one error-handling path, not a special case for 422s just because
        FastAPI's default validation handler uses a different shape (`{"detail": [...]}`)."""
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "validation_error",
                "message": "Request validation failed.",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Last-resort handler for anything not already a `ClaimAgentError` — a bug, not a
        modeled failure. Logs the full traceback server-side (with the request's correlation
        id) and returns a message with no internal detail, so an unhandled exception never
        leaks a stack trace or exception message to the client.

        Reads the request id from `request.state`, and sets the response header itself,
        rather than relying on `RequestContextMiddleware` the way every other response does:
        Starlette wires a bare-`Exception` handler into `ServerErrorMiddleware`, which wraps
        *outside* that middleware, so by the time this runs, the contextvar it set has
        already been reset in its `finally`, and any headers this handler's response carries
        never pass back through that middleware's header-injecting `send` wrapper either. See
        `app.core.middleware`'s module docstring for the full explanation.
        """
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "unhandled_exception",
            extra={"request_id": request_id, "path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "internal_error",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )
