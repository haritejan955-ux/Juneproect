from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ClaimAgentError(Exception):
    """Base class for all domain errors in this service."""

    error_code = "internal_error"
    status_code = 500

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = context


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
