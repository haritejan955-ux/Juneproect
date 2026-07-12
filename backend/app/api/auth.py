"""API key authentication.

A single static shared-secret scheme (`X-API-Key` header), checked against
`settings.api_keys`. This is deliberately not OAuth2/JWT: there is no user
model anywhere in this system (a claimant is an opaque id supplied by the
caller, not an authenticated identity), so there is nothing for per-user
tokens to encode — the actual security boundary this project needs is
"is the caller our frontend / an authorized service," not "which user is
this." See docs/security-architecture.md for the fuller reasoning and the
explicit scope note on what this scheme does not attempt to solve.

`fastapi.security.APIKeyHeader` is used (rather than reading the header
by hand off `Request`) specifically so FastAPI registers it as an OpenAPI
security scheme — every protected router gets a lock icon in Swagger and
an "Authorize" button that actually works, for free.
"""

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config.settings import get_settings
from app.core.exceptions import AuthenticationError

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="Shared-secret API key. Configured server-side via the API_KEYS setting.",
)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    settings = get_settings()
    if not api_key or api_key not in settings.api_keys:
        raise AuthenticationError("Missing or invalid API key.")
    return api_key
